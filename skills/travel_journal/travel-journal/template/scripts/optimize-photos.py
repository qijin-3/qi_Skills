#!/usr/bin/env python3
"""批量压缩 data/locations.json 中引用的原图，生成 thumb / medium 两档，
并把 locations.json 的 src 指向 medium、新增 thumb 字段。

- 原图保持不动（仍在 public/photos/original/ 下）。
- 使用 macOS 自带 sips，无第三方依赖。
- 幂等：若目标文件已存在且不比原图旧，则跳过。
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATIONS_JSON = os.path.join(ROOT, "data", "locations.json")
OUT_BASE = os.path.join(ROOT, "public", "photos")

# 两档尺寸：thumb 给悬停预览，medium 给详情面板
PRESETS = {
    "thumb": {"max": 480, "quality": 70},
    "medium": {"max": 1600, "quality": 80},
}


def rel_under_original(src: str) -> str:
    """把 'public/photos/original/xxx/a.jpg' 归一化成相对 original 的子路径。"""
    norm = src.replace("\\", "/")
    prefix = "public/photos/original/"
    if norm.startswith(prefix):
        return norm[len(prefix):]
    # 兼容旧版 Reference/ 路径
    if norm.startswith("Reference/"):
        return norm[len("Reference/"):]
    return norm


def needs_build(src_path: str, out_path: str) -> bool:
    """目标缺失或比原图旧时需要重新生成。"""
    if not os.path.exists(out_path):
        return True
    return os.path.getmtime(out_path) < os.path.getmtime(src_path)


def build_variant(src_path: str, out_path: str, max_size: int, quality: int) -> bool:
    """用 sips 生成单张压缩图，返回是否成功。"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    result = subprocess.run(
        [
            "sips",
            "-s", "format", "jpeg",
            "-s", "formatOptions", str(quality),
            "-Z", str(max_size),
            src_path,
            "--out", out_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        sys.stderr.write(f"  [失败] {src_path}: {result.stderr.decode().strip()}\n")
        return False
    return True


def main() -> None:
    with open(LOCATIONS_JSON, "r", encoding="utf-8") as f:
        locations = json.load(f)

    total = built = skipped = missing = 0

    for loc in locations:
        for photo in loc.get("photos") or []:
            src = photo.get("src")
            if not src:
                continue
            # 跳过已优化的图和 data URL
            if src.startswith("data:"):
                continue
            if src.startswith("public/photos/medium/") or src.startswith("public/photos/thumb/"):
                continue

            rel = rel_under_original(src)
            # 优先从 original 目录查找
            src_path = os.path.join(ROOT, "public", "photos", "original", rel)
            if not os.path.exists(src_path):
                # 兼容 src 本身就是绝对路径或其他相对路径
                alt = src if os.path.isabs(src) else os.path.join(ROOT, src)
                if os.path.exists(alt):
                    src_path = alt
                else:
                    missing += 1
                    sys.stderr.write(f"  [缺图] {src}\n")
                    continue

            total += 1
            out_rel = {}
            ok = True
            for name, cfg in PRESETS.items():
                # 保持原始子目录结构（去掉 original/ 前缀后的相对路径）
                out_path = os.path.join(OUT_BASE, name, rel)
                out_rel[name] = os.path.relpath(out_path, ROOT).replace("\\", "/")
                if needs_build(src_path, out_path):
                    if build_variant(src_path, out_path, cfg["max"], cfg["quality"]):
                        built += 1
                    else:
                        ok = False
                else:
                    skipped += 1

            if ok:
                # 保留原始路径作为 id（保证幂等与删除逻辑稳定）
                if not photo.get("id"):
                    photo["id"] = src
                photo["src"] = out_rel["medium"]
                photo["thumb"] = out_rel["thumb"]

    with open(LOCATIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"完成：照片 {total} 张，生成 {built} 个变体，跳过 {skipped} 个，缺图 {missing} 个。")
    print(f"输出目录：{OUT_BASE}")


if __name__ == "__main__":
    main()
