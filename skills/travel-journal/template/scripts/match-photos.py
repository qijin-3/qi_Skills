#!/usr/bin/env python3
"""
将用户提供的照片文件夹按 EXIF/GPS 与行程日期匹配到各地点。

用法：
  python3 match-photos.py --photo-dir /path/to/photos [--trip-start YYYY-MM-DD] [--trip-end YYYY-MM-DD]

依赖：macOS（使用 mdls 读取 EXIF 元数据）
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MAX_DISTANCE_KM = 55
MAX_DISTANCE_FALLBACK_KM = 75
MAX_PHOTOS_PER_LOCATION = 4
RESERVE_PER_ROUTE_STOP = 2


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两点球面距离（千米）。"""
    radius = 6371.0
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * atan2(sqrt(a), sqrt(1 - a))


def parse_date_from_name(name: str) -> str | None:
    """从文件名中尝试解析日期（格式如 IMG20260502xxx 或 IMG_2026-05-02xxx）。"""
    match = re.search(r"(\d{4})[_\-]?(\d{2})[_\-]?(\d{2})", name)
    if not match:
        return None
    year, month, day = match.group(1), match.group(2), match.group(3)
    if int(year) < 2000 or int(month) > 12 or int(day) > 31:
        return None
    return f"{year}-{month}-{day}"


def read_mdls(path: Path) -> tuple[float | None, float | None, str | None]:
    """用 macOS Spotlight 元数据读取经纬度与拍摄日期。"""
    try:
        output = subprocess.check_output(
            [
                "mdls",
                "-name", "kMDItemLatitude",
                "-name", "kMDItemLongitude",
                "-name", "kMDItemContentCreationDate",
                str(path),
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None, None

    lat = lon = date = None
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        raw = raw.strip()
        if raw == "(null)":
            continue
        if "Latitude" in key:
            try:
                lat = float(raw)
            except ValueError:
                pass
        elif "Longitude" in key:
            try:
                lon = float(raw)
            except ValueError:
                pass
        elif "ContentCreationDate" in key:
            date = raw[:10]
    return lon, lat, date


def collect_photos(photo_dir: Path, trip_start: str | None, trip_end: str | None) -> list[dict]:
    """收集照片元数据列表，按行程日期过滤（如果提供了日期范围）。"""
    photos: list[dict] = []
    extensions = {".jpg", ".jpeg", ".png", ".heic", ".webp"}

    for file_path in photo_dir.rglob("*"):
        if file_path.suffix.lower() not in extensions:
            continue

        date = parse_date_from_name(file_path.name)
        lon, lat, mdls_date = read_mdls(file_path)
        if not date:
            date = mdls_date

        # 若有行程日期范围，过滤掉范围外的照片
        if date and trip_start and date < trip_start:
            continue
        if date and trip_end and date > trip_end:
            continue

        photos.append({
            "path": str(file_path),
            "rel_path": str(file_path.relative_to(photo_dir)),
            "date": date,
            "lon": lon,
            "lat": lat,
        })

    return photos


def match_photo_to_location(
    photo: dict,
    locations: list[dict],
    loc_by_id: dict[str, dict],
    day_routes: dict[str, list[str]],
) -> tuple[str, float] | None:
    """将单张照片匹配到最近且日期合理的地点。"""
    if photo["lon"] is None or photo["lat"] is None:
        return None

    route_ids = day_routes.get(photo["date"] or "", [])
    best: tuple[float, str, float] | None = None

    def try_location(location_id: str, penalty: float = 0.0) -> None:
        nonlocal best
        loc = loc_by_id[location_id]
        dist = haversine_km(
            photo["lon"], photo["lat"],
            loc["coordinates"][0], loc["coordinates"][1],
        )
        if dist > MAX_DISTANCE_KM:
            return
        score = dist + penalty
        if best is None or score < best[0]:
            best = (score, location_id, dist)

    for location_id in route_ids:
        try_location(location_id)

    if best is None:
        for loc in locations:
            if photo["date"] and photo["date"] not in loc.get("dates", []):
                continue
            try_location(loc["id"], penalty=3.0)

    return (best[1], best[2]) if best else None


def build_photo_assignments(
    locations: list[dict], days: list[dict], photos: list[dict]
) -> dict[str, list[dict]]:
    """为各地点挑选最近且数量适量的照片。"""
    loc_by_id = {loc["id"]: loc for loc in locations}
    day_routes = {day["date"]: day["routeLocationIds"] for day in days}
    assigned: dict[str, list[dict]] = defaultdict(list)
    used_paths: set[str] = set()

    gps_photos = [p for p in photos if p["lon"] is not None]

    # 阶段一：按当日路线认领照片，每站先保留少量名额
    for day in days:
        route_ids = day_routes.get(day["date"], [])
        if not route_ids:
            continue
        day_photos = [p for p in gps_photos if p["date"] == day["date"]]
        for location_id in route_ids:
            picks = []
            for photo in day_photos:
                if photo["path"] in used_paths:
                    continue
                all_dists = [
                    (haversine_km(photo["lon"], photo["lat"],
                                  loc_by_id[lid]["coordinates"][0],
                                  loc_by_id[lid]["coordinates"][1]), lid)
                    for lid in route_ids
                ]
                all_dists.sort()
                if not all_dists or all_dists[0][1] != location_id:
                    continue
                if all_dists[0][0] > MAX_DISTANCE_KM:
                    continue
                picks.append({**photo, "dist": all_dists[0][0]})
            picks.sort(key=lambda x: x["dist"])
            for pick in picks[:RESERVE_PER_ROUTE_STOP]:
                assigned[location_id].append(pick)
                used_paths.add(pick["path"])

    # 阶段二：剩余照片全局匹配补足
    for photo in gps_photos:
        if photo["path"] in used_paths:
            continue
        matched = match_photo_to_location(photo, locations, loc_by_id, day_routes)
        if not matched:
            continue
        location_id, dist = matched
        if len(assigned[location_id]) >= MAX_PHOTOS_PER_LOCATION:
            continue
        assigned[location_id].append({**photo, "dist": dist})
        used_paths.add(photo["path"])

    # 阶段三：仍无图的地点，取最近未用照片
    for loc in locations:
        if assigned.get(loc["id"]):
            continue
        best_picks = []
        for photo in gps_photos:
            if photo["path"] in used_paths:
                continue
            if photo["date"] and photo["date"] not in loc.get("dates", []):
                continue
            dist = haversine_km(
                photo["lon"], photo["lat"],
                loc["coordinates"][0], loc["coordinates"][1],
            )
            if dist > MAX_DISTANCE_FALLBACK_KM:
                continue
            best_picks.append({**photo, "dist": dist})
        best_picks.sort(key=lambda x: x["dist"])
        for pick in best_picks[:MAX_PHOTOS_PER_LOCATION]:
            assigned[loc["id"]].append(pick)
            used_paths.add(pick["path"])

    # 截断超出限额的部分
    for location_id in assigned:
        assigned[location_id].sort(key=lambda x: x["dist"])
        assigned[location_id] = assigned[location_id][:MAX_PHOTOS_PER_LOCATION]

    return assigned


def apply_photos_to_locations(
    locations: list[dict], assigned: dict[str, list[dict]], photo_dir: Path
) -> None:
    """把匹配结果写入 locations 的 photos 字段，路径转换为 public/ 下的相对路径。"""
    # 将原始照片复制到 public/photos/original/ 下，optimize-photos.py 会进一步处理
    original_dir = ROOT / "public" / "photos" / "original"
    original_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    for loc in locations:
        picks = assigned.get(loc["id"], [])
        photo_entries = []
        for pick in picks:
            src = Path(pick["path"])
            rel = pick["rel_path"].replace("\\", "/")
            dest = original_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(src, dest)
            photo_entries.append({
                "id": f"original/{rel}",
                "src": f"public/photos/original/{rel}",
                "caption": f"{pick['date'] or ''} · {loc['name']}",
            })
        loc["photos"] = photo_entries


def main() -> int:
    parser = argparse.ArgumentParser(description="将照片文件夹匹配到游记地点")
    parser.add_argument("--photo-dir", required=True, help="照片文件夹路径")
    parser.add_argument("--trip-start", default=None, help="行程开始日期 YYYY-MM-DD（可选，不填则不过滤）")
    parser.add_argument("--trip-end", default=None, help="行程结束日期 YYYY-MM-DD（可选）")
    args = parser.parse_args()

    photo_dir = Path(args.photo_dir).expanduser().resolve()
    if not photo_dir.is_dir():
        print(f"错误：找不到照片目录 {photo_dir}", file=sys.stderr)
        return 1

    locations = json.loads((ROOT / "data/locations.json").read_text(encoding="utf-8"))
    days = json.loads((ROOT / "data/days.json").read_text(encoding="utf-8"))

    if not locations:
        print("data/locations.json 为空，请先完成行程解析步骤。", file=sys.stderr)
        return 1

    # 自动推断行程日期范围（若未指定）
    trip_start = args.trip_start
    trip_end = args.trip_end
    if not trip_start and days:
        trip_start = min(d["date"] for d in days)
    if not trip_end and days:
        trip_end = max(d["date"] for d in days)

    print(f"行程日期范围：{trip_start} → {trip_end}")
    print(f"正在扫描照片目录：{photo_dir}")

    photos = collect_photos(photo_dir, trip_start, trip_end)
    gps_count = sum(1 for p in photos if p["lon"] is not None)
    print(f"找到照片 {len(photos)} 张，含 GPS 信息 {gps_count} 张")

    assigned = build_photo_assignments(locations, days, photos)
    apply_photos_to_locations(locations, assigned, photo_dir)

    with_photos = sum(1 for loc in locations if loc.get("photos"))
    total = sum(len(loc.get("photos", [])) for loc in locations)
    print(f"已匹配 {with_photos} / {len(locations)} 个地点，共 {total} 张展示图")

    (ROOT / "data/locations.json").write_text(
        json.dumps(locations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("✅ locations.json 已更新，请运行 optimize-photos.py 生成缩略图")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
