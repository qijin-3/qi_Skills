#!/usr/bin/env python3
"""
产品名称搜索竞争度检查工具

用法:
    python3 search_competition.py "名称1" "名称2" "名称3"
    python3 search_competition.py --file names.txt

输出:
    每个名称的搜索结果统计，包括：
    - Google 搜索结果数量（用于评估品牌竞争度）
    - 搜索建议（用于评估常见度）
"""

import sys
import json
import subprocess
from typing import List, Dict, Any
import argparse


def search_google(query: str) -> Dict[str, Any]:
    """
    使用 Google 搜索（通过 ddgr 或其他命令行工具）

    注意：这个脚本需要一个命令行搜索工具。
    推荐使用 ddgr (DuckDuckGo) 或 googlesearch-cli

    安装:
    brew install ddgr  # macOS
    apt install ddgr   # Ubuntu/Debian

    返回:
        {
            "query": "搜索词",
            "result_count": "约 1,000 条结果",
            "status": "success" | "no_tool"
        }
    """
    # 尝试使用 ddgr (DuckDuckGo)
    try:
        # 使用 ddgr 获取搜索结果数量
        # 注意：ddgr 不直接提供结果数量，这里简化处理
        cmd = f"ddgr --json '{query}' --count 5"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # 解析 ddgr 输出
            lines = result.stdout.strip().split('\n')
            return {
                "query": query,
                "result_count": "无法获取精确数量（ddgr 限制）",
                "has_results": len([l for l in lines if l.strip()]) > 0,
                "status": "success"
            }

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # 如果 ddgr 不可用，尝试其他方法
    return {
        "query": query,
        "result_count": "未安装搜索工具（ddgr）",
        "has_results": False,
        "status": "no_tool"
    }


def check_name_competition(name: str) -> Dict[str, Any]:
    """
    检查单个名称的竞争度

    Args:
        name: 要检查的名称

    Returns:
        包含搜索结果的字典
    """
    # 执行搜索
    search_result = search_google(name)

    # 添加额外的分析
    competition_level = analyze_competition_level(search_result)

    return {
        "name": name,
        "search_result": search_result,
        "competition_level": competition_level
    }


def analyze_competition_level(search_result: Dict[str, Any]) -> str:
    """
    根据搜索结果分析竞争程度

    Returns:
        "low", "medium", "high", "unknown"
    """
    if search_result["status"] == "no_tool":
        return "unknown"

    if search_result.get("has_results", False):
        # 如果有搜索结果，说明有竞争
        return "medium"
    else:
        # 如果没有搜索结果，说明竞争较少
        return "low"


def format_results(results: List[Dict[str, Any]]) -> str:
    """
    格式化搜索结果为易读的输出
    """
    output = []
    output.append("=" * 60)
    output.append("产品名称竞争度检查报告")
    output.append("=" * 60)
    output.append("")

    for result in results:
        name = result["name"]
        comp_level = result["competition_level"]
        search_result = result["search_result"]

        output.append(f"📛 名称: {name}")
        output.append(f"   竞争程度: {get_competition_emoji(comp_level)} {comp_level.upper()}")
        output.append(f"   搜索状态: {search_result['status']}")

        if search_result["status"] == "success":
            output.append(f"   结果: {search_result.get('result_count', 'N/A')}")

        output.append("")

    output.append("=" * 60)
    output.append("💡 建议:")
    output.append("  - LOW: 竞争较少，更容易建立品牌")
    output.append("  - MEDIUM: 有一定竞争，但仍有空间")
    output.append("  - HIGH: 竞争激烈，需要强有力的差异化")
    output.append("  - UNKNOWN: 需要手动检查 Google/百度")
    output.append("=" * 60)

    return "\n".join(output)


def get_competition_emoji(level: str) -> str:
    """返回竞争程度的表情符号"""
    emojis = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🔴",
        "unknown": "⚪"
    }
    return emojis.get(level, "⚪")


def main():
    parser = argparse.ArgumentParser(
        description="检查产品名称的搜索竞争度"
    )
    parser.add_argument(
        "names",
        nargs="*",
        help="要检查的名称列表"
    )
    parser.add_argument(
        "--file",
        "-f",
        help="从文件读取名称列表（每行一个）"
    )

    args = parser.parse_args()

    # 获取名称列表
    names = []

    if args.file:
        # 从文件读取
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                names = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"错误: 文件 '{args.file}' 不存在")
            sys.exit(1)
    else:
        # 从命令行参数读取
        names = args.names

    if not names:
        print("错误: 请提供要检查的名称")
        print("用法: python3 search_competition.py '名称1' '名称2' '名称3'")
        print("      python3 search_competition.py --file names.txt")
        sys.exit(1)

    # 检查每个名称
    results = []
    for name in names:
        result = check_name_competition(name)
        results.append(result)

    # 输出结果
    print(format_results(results))


if __name__ == "__main__":
    main()
