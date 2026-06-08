"""
章节自动检测模块
支持多种中文章节格式的自动识别
"""

import re
from backend.models.models import Chapter


# 常见章节标题正则模式（按优先级排列）
CHAPTER_PATTERNS = [
    # 中文数字章节：第一章、第二十三章
    r'^[ \t]*第[一二三四五六七八九十百千万零\d]+[章节回折幕][ \t\S]*$',
    # 阿拉伯数字章节：第1章、第23章
    r'^[ \t]*第?\d+[章节回折幕][ \t\S]*$',
    # "章节 N" 格式
    r'^[ \t]*章节[\s]*\d+[ \t\S]*$',
    # 纯数字标题：1、23、
    r'^[ \t]*\d+[、.．][ \t\S]*$',
    # Chapter X 格式（英文）
    r'^[ \t]*[Cc]hapter\s+\d+[ \t\S]*$',
    # 卷/篇 分隔
    r'^[ \t]*第[一二三四五六七八九十百千万零\d]+[卷篇集部][ \t\S]*$',
    # Markdown标题格式
    r'^#{1,3}\s+\S.*$',
    # 中文分隔线
    r'^[ \t]*[＊\*]{3,}[ \t]*$',
    r'^[ \t]*[-—]{3,}[ \t]*$',
]


def _build_patterns() -> list[re.Pattern]:
    """编译所有正则模式"""
    return [re.compile(p, re.MULTILINE) for p in CHAPTER_PATTERNS]


COMPILED_PATTERNS = _build_patterns()


def detect_chapter_title(line: str) -> bool:
    """判断一行是否是章节标题"""
    line = line.strip()
    if not line or len(line) > 100:
        return False
    for pattern in COMPILED_PATTERNS:
        if pattern.match(line):
            return True
    return False


def split_chapters(text: str, min_chapters: int = 1) -> list[Chapter]:
    """
    将文本按章节拆分
    如果检测不到章节标题，则按段落数均分为 min_chapters 个章节

    Args:
        text: 小说全文
        min_chapters: 最少章节数

    Returns:
        章节列表
    """
    lines = text.split("\n")
    chapter_starts: list[tuple[int, str]] = []  # (行号, 标题)

    for i, line in enumerate(lines):
        if detect_chapter_title(line):
            chapter_starts.append((i, line.strip()))

    # 如果检测到的章节不足，尝试更宽松的检测
    if len(chapter_starts) < min_chapters and len(chapter_starts) == 0:
        # 完全没有检测到章节，按字数均分
        return _split_by_length(text, min_chapters)

    if len(chapter_starts) == 0:
        return _split_by_length(text, min_chapters)

    # 从检测到的章节标题拆分
    chapters = []
    for idx, (line_num, title) in enumerate(chapter_starts):
        # 确定本章结束位置
        if idx + 1 < len(chapter_starts):
            end_line = chapter_starts[idx + 1][0]
        else:
            end_line = len(lines)

        # 章节内容（不包含标题行本身）
        content_lines = lines[line_num + 1: end_line]
        content = "\n".join(content_lines).strip()

        chapters.append(Chapter(
            index=idx + 1,
            title=title,
            content=content,
            char_count=len(content)
        ))

    # 如果第一章标题前面有内容，作为序章
    if chapter_starts[0][0] > 0:
        preface_lines = lines[:chapter_starts[0][0]]
        preface = "\n".join(preface_lines).strip()
        if len(preface) > 50:  # 超过50字才认为是有效序章
            chapters.insert(0, Chapter(
                index=0,
                title="序章",
                content=preface,
                char_count=len(preface)
            ))
            # 重新编号
            for i, ch in enumerate(chapters):
                ch.index = i + 1

    return chapters


def _split_by_length(text: str, num_parts: int) -> list[Chapter]:
    """按字数将文本均分为指定数量的章节"""
    total_len = len(text)
    part_size = total_len // num_parts

    chapters = []
    for i in range(num_parts):
        start = i * part_size
        end = start + part_size if i < num_parts - 1 else total_len

        # 尝试在段落边界切分
        if i < num_parts - 1:
            # 在目标位置附近找最近的段落分隔
            search_start = max(start, end - 200)
            search_end = min(end + 200, total_len)
            segment = text[search_start:search_end]
            # 找最近的双换行
            pos = segment.find("\n\n")
            if pos != -1:
                end = search_start + pos

        content = text[start:end].strip()
        chapters.append(Chapter(
            index=i + 1,
            title=f"第{i + 1}部分",
            content=content,
            char_count=len(content)
        ))

    return chapters


def get_chapter_stats(chapters: list[Chapter]) -> dict:
    """获取章节统计信息"""
    return {
        "total_chapters": len(chapters),
        "total_chars": sum(ch.char_count for ch in chapters),
        "avg_chars_per_chapter": sum(ch.char_count for ch in chapters) // max(len(chapters), 1),
        "chapters": [
            {"index": ch.index, "title": ch.title, "chars": ch.char_count}
            for ch in chapters
        ]
    }
