#!/usr/bin/env python3
"""
会议纪要文件处理脚本
自动化步骤1-4：创建日期文件夹、复制文件、重命名逐字稿、自动归档
"""

import os
import re
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set

# 技能根目录（scripts/ 的上一级）
SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = SKILL_DIR / 'config.json'
EXAMPLE_CONFIG_PATH = SKILL_DIR / 'config.example.json'


def get_default_config_path() -> Path:
    """返回默认配置文件路径（技能目录下的 config.json）。"""
    return DEFAULT_CONFIG_PATH


class MeetingFileProcessor:
    """会议文件处理器"""

    # 支持的音频格式
    SUPPORTED_AUDIO_FORMATS = ['.m4a', '.mp3', '.wav', '.aac', '.ogg', '.flac', '.wma']

    def __init__(self, source_dir: str, config_path: Optional[str] = None):
        self.source_dir = Path(source_dir).expanduser()
        if not self.source_dir.exists():
            raise ValueError(f"源文件夹不存在: {source_dir}")

        # 加载配置
        self.config = self._load_config(config_path)
        self.archive_dir = Path(self.config.get('archive_dir', '/Users/jin/SynologyDrive/Working/Lumis_Doc/📹 Meeting/')).expanduser()
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.audio_files = []
        self.transcript_files = []
        self.date_folders = {}
        self.skipped_files: Set[Path] = set()

    def _load_config(self, config_path: Optional[str]) -> dict:
        """加载配置文件"""
        default_config = {
            'archive_dir': '/Users/jin/SynologyDrive/Working/Lumis_Doc/📹 Meeting/',
            'overwrite': False,
            'skip_existing': True
        }

        if config_path:
            config_file = Path(config_path).expanduser()
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        user_config = json.load(f)
                    default_config.update(user_config)
                    print(f"✅ 已加载配置文件: {config_file}")
                except Exception as e:
                    print(f"⚠️  配置文件加载失败，使用默认配置: {e}")

        return default_config

    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名提取日期 YYYY-MM-DD
        支持格式：
        - 录音2026-01-08.m4a
        - 录音2026-01-09-1.m4a
        """
        pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            # 验证日期有效性
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            except ValueError:
                print(f"  ⚠️  无效日期: {date_str}")
                return None
        return None

    def is_audio_file(self, filename: str) -> bool:
        """判断是否为录音文件（支持多种音频格式）"""
        return any(filename.endswith(ext) for ext in self.SUPPORTED_AUDIO_FORMATS) and filename.startswith('录音')

    def is_transcript_file(self, filename: str) -> bool:
        """判断是否为逐字稿文件"""
        return filename.endswith('_原文.md')

    def scan_files(self):
        """扫描源文件夹，识别录音和逐字稿文件"""
        print(f"\n📂 扫描源文件夹: {self.source_dir}")

        for file_path in self.source_dir.iterdir():
            if not file_path.is_file():
                continue

            filename = file_path.name

            if self.is_audio_file(filename):
                date = self.extract_date_from_filename(filename)
                if date:
                    self.audio_files.append((file_path, date))
                    print(f"  ✓ 录音: {filename} (日期: {date})")
                else:
                    print(f"  ⚠️  无法提取日期: {filename}")

            elif self.is_transcript_file(filename):
                date = self.extract_date_from_filename(filename)
                if date:
                    self.transcript_files.append((file_path, date))
                    print(f"  ✓ 逐字稿: {filename} (日期: {date})")
                else:
                    print(f"  ⚠️  无法提取日期: {filename}")

        print(f"\n📊 统计: 找到 {len(self.audio_files)} 个录音文件, {len(self.transcript_files)} 个逐字稿文件")

    def group_by_date(self):
        """按日期分组文件"""
        print(f"\n📅 按日期分组文件...")

        # 收集所有日期
        dates = set()
        for _, date in self.audio_files:
            dates.add(date)
        for _, date in self.transcript_files:
            dates.add(date)

        # 为每个日期分组文件
        for date in sorted(dates):
            audio_list = [f for f, d in self.audio_files if d == date]
            transcript_list = [f for f, d in self.transcript_files if d == date]

            self.date_folders[date] = {
                'audio': audio_list,
                'transcript': transcript_list
            }

            print(f"  📆 {date}: {len(audio_list)} 个录音, {len(transcript_list)} 个逐字稿")

    def create_date_folders_and_copy(self):
        """创建日期文件夹并复制文件（步骤1）"""
        print(f"\n📁 创建日期文件夹并复制文件...")

        for date, files in self.date_folders.items():
            # 创建日期文件夹
            date_folder = self.source_dir / date
            date_folder.mkdir(exist_ok=True)
            print(f"\n  📂 {date}/")

            # 复制录音文件
            for audio_file in files['audio']:
                dest = date_folder / audio_file.name
                if self._safe_copy(audio_file, dest):
                    print(f"    ✓ 复制: {audio_file.name}")

            # 复制逐字稿文件
            for transcript_file in files['transcript']:
                dest = date_folder / transcript_file.name
                if self._safe_copy(transcript_file, dest):
                    print(f"    ✓ 复制: {transcript_file.name}")

        print(f"\n✅ 文件复制完成（源文件保持不变）")

    def _safe_copy(self, src: Path, dest: Path) -> bool:
        """安全复制文件，处理已存在的情况"""
        if dest.exists():
            if self.config.get('skip_existing', True):
                print(f"    ⏭️  跳过已存在: {dest.name}")
                self.skipped_files.add(dest)
                return False
            elif not self.config.get('overwrite', False):
                response = input(f"    ⚠️  文件已存在，是否覆盖? {dest.name} [y/N]: ")
                if response.lower() != 'y':
                    print(f"    ⏭️  跳过: {dest.name}")
                    self.skipped_files.add(dest)
                    return False

        try:
            shutil.copy2(src, dest)
            return True
        except Exception as e:
            print(f"    ❌ 复制失败: {e}")
            return False

    def pair_audio_and_transcript(self, date: str) -> List[Tuple[Path, Path]]:
        """
        配对录音和逐字稿文件（步骤2）
        返回: [(录音文件, 逐字稿文件), ...]
        """
        date_folder = self.source_dir / date
        pairs = []

        # 获取日期文件夹内的所有文件（支持多种音频格式）
        audio_files = []
        for ext in self.SUPPORTED_AUDIO_FORMATS:
            audio_files.extend(date_folder.glob(f'*{ext}'))
        audio_files = sorted(audio_files)
        transcript_files = sorted([f for f in date_folder.glob('*_原文.md')])

        print(f"\n  🔗 配对文件...")

        for audio_file in audio_files:
            # 提取录音文件的基础名称（去除扩展名）
            base_name = audio_file.stem  # 例如：录音2026-01-09-1

            # 查找对应的逐字稿文件（base_name_原文.md）
            expected_transcript = date_folder / f"{base_name}_原文.md"

            if expected_transcript.exists():
                pairs.append((audio_file, expected_transcript))
                print(f"    ✓ {audio_file.name} ↔ {expected_transcript.name}")
            else:
                print(f"    ⚠️  {audio_file.name} 缺少对应的逐字稿")

        # 检查是否有孤立的逐字稿
        paired_transcripts = {t for _, t in pairs}
        for transcript_file in transcript_files:
            if transcript_file not in paired_transcripts:
                print(f"    ⚠️  {transcript_file.name} 没有对应的录音文件")

        return pairs

    def rename_transcripts(self, date: str, pairs: List[Tuple[Path, Path]]):
        """
        重命名逐字稿文件（步骤3）
        录音2026-01-09-1_原文.md → 逐字稿2026-01-09-1.md
        """
        print(f"\n  ✏️  重命名逐字稿...")

        for audio_file, transcript_file in pairs:
            # 从录音文件名生成逐字稿文件名
            # 录音2026-01-09-1.m4a → 逐字稿2026-01-09-1.md
            audio_base = audio_file.stem  # 录音2026-01-09-1

            # 去除"录音"前缀
            if audio_base.startswith('录音'):
                suffix = audio_base[2:]  # 2026-01-09-1
            else:
                suffix = audio_base

            # 生成新的逐字稿文件名
            new_transcript_name = f"逐字稿{suffix}.md"
            new_transcript_path = transcript_file.parent / new_transcript_name

            # 检查目标文件是否存在
            if new_transcript_path.exists():
                print(f"    ⏭️  跳过已存在: {new_transcript_name}")
                continue

            # 重命名
            try:
                transcript_file.rename(new_transcript_path)
                print(f"    ✓ {transcript_file.name} → {new_transcript_name}")
            except Exception as e:
                print(f"    ❌ 重命名失败: {e}")

    def move_to_archive(self, date: str) -> bool:
        """
        移动日期文件夹到归档目录（步骤4）
        """
        date_folder = self.source_dir / date
        archive_dest = self.archive_dir / date

        if not date_folder.exists():
            print(f"    ⚠️  日期文件夹不存在: {date}")
            return False

        # 检查归档目标是否已存在
        if archive_dest.exists():
            print(f"    ⚠️  归档目标已存在: {archive_dest}")
            response = input(f"    是否合并文件夹? [y/N]: ")
            if response.lower() != 'y':
                print(f"    ⏭️  跳过归档: {date}")
                return False

            # 合并文件夹
            try:
                for item in date_folder.iterdir():
                    dest_item = archive_dest / item.name
                    if dest_item.exists():
                        print(f"    ⏭️  跳过已存在: {item.name}")
                        continue
                    shutil.move(str(item), str(archive_dest))
                date_folder.rmdir()
                print(f"    ✓ 合并归档: {date}")
                return True
            except Exception as e:
                print(f"    ❌ 归档失败: {e}")
                return False

        # 移动整个文件夹
        try:
            shutil.move(str(date_folder), str(archive_dest))
            print(f"    ✓ 归档完成: {date} → {archive_dest}")
            return True
        except Exception as e:
            print(f"    ❌ 归档失败: {e}")
            return False

    def process_all_dates(self):
        """处理所有日期文件夹"""
        print(f"\n🔄 开始处理所有日期文件夹...")

        for date in sorted(self.date_folders.keys()):
            print(f"\n📆 处理日期: {date}")

            # 配对文件
            pairs = self.pair_audio_and_transcript(date)

            if pairs:
                # 重命名逐字稿
                self.rename_transcripts(date, pairs)
                print(f"  ✅ {date} 处理完成，共 {len(pairs)} 对文件")
            else:
                print(f"  ⚠️  {date} 没有找到配对的文件")

    def archive_all_dates(self):
        """归档所有日期文件夹"""
        print(f"\n📦 开始归档到: {self.archive_dir}")

        archived_count = 0
        for date in sorted(self.date_folders.keys()):
            if self.move_to_archive(date):
                archived_count += 1

        print(f"\n✅ 归档完成: {archived_count}/{len(self.date_folders)} 个日期文件夹")

    def run(self, auto_archive: bool = True):
        """执行完整流程"""
        print("=" * 60)
        print("🎯 会议文件处理脚本 v2.0")
        print("=" * 60)
        print(f"📂 源文件夹: {self.source_dir}")
        print(f"📦 归档目录: {self.archive_dir}")

        try:
            # 步骤1：扫描文件
            self.scan_files()

            if not self.audio_files and not self.transcript_files:
                print("\n❌ 没有找到任何录音或逐字稿文件")
                return False

            # 步骤2：按日期分组
            self.group_by_date()

            # 步骤3：创建日期文件夹并复制文件
            self.create_date_folders_and_copy()

            # 步骤4：处理所有日期（配对和重命名）
            self.process_all_dates()

            # 步骤5：归档到目标目录
            if auto_archive:
                self.archive_all_dates()

            print("\n" + "=" * 60)
            print("✅ 所有处理完成！")
            print("=" * 60)

            if self.skipped_files:
                print(f"\n⏭️  跳过的文件: {len(self.skipped_files)}")

            return True

        except Exception as e:
            print(f"\n❌ 处理出错: {e}")
            import traceback
            traceback.print_exc()
            return False


def create_default_config() -> Optional[Path]:
    """从 config.example.json 复制或写入默认配置到技能目录的 config.json。"""
    config_path = get_default_config_path()
    if config_path.exists():
        print(f"⚠️  配置文件已存在: {config_path}")
        return config_path

    if EXAMPLE_CONFIG_PATH.exists():
        try:
            shutil.copy2(EXAMPLE_CONFIG_PATH, config_path)
            print(f"✅ 已从示例创建配置文件: {config_path}")
            return config_path
        except Exception as e:
            print(f"⚠️  复制示例配置失败，使用内置默认值: {e}")

    default_config = {
        "archive_dir": "/Users/jin/SynologyDrive/Working/Lumis_Doc/📹 Meeting/",
        "overwrite": False,
        "skip_existing": True
    }
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print(f"✅ 已创建默认配置文件: {config_path}")
        return config_path
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return None


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='会议纪要文件处理脚本 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 使用默认 Downloads 文件夹
  %(prog)s ~/Desktop/meetings        # 指定源文件夹
  %(prog)s --no-archive              # 不自动归档
  %(prog)s --create-config           # 创建默认配置文件
        """
    )

    parser.add_argument('source_dir', nargs='?', default='~/Downloads',
                        help='源文件夹路径（默认：~/Downloads）')
    parser.add_argument('--config', '-c',
                        help=f'配置文件路径（默认：{DEFAULT_CONFIG_PATH}）')
    parser.add_argument('--no-archive', action='store_true',
                        help='跳过自动归档步骤')
    parser.add_argument('--create-config', action='store_true',
                        help='创建默认配置文件并退出')

    args = parser.parse_args()

    # 创建配置文件
    if args.create_config:
        create_default_config()
        sys.exit(0)

    # 如果没有指定配置文件，使用技能目录下的 config.json
    config_path = args.config or str(DEFAULT_CONFIG_PATH)

    try:
        processor = MeetingFileProcessor(args.source_dir, config_path)
        success = processor.run(auto_archive=not args.no_archive)
        sys.exit(0 if success else 1)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(130)


if __name__ == "__main__":
    main()
