"""
文件工具函数
"""

import os
from backend.models.models import NovelFile
from backend.parser.txt_parser import read_txt_from_bytes
from backend.parser.docx_parser import read_docx_from_bytes
from backend.parser.chapter_detector import split_chapters


def parse_uploaded_file(file_bytes: bytes, filename: str) -> NovelFile:
    """
    解析上传的文件

    Args:
        file_bytes: 文件字节数据
        filename: 文件名

    Returns:
        解析后的小说文件对象
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt":
        content, encoding = read_txt_from_bytes(file_bytes, filename)
        file_type = "txt"
    elif ext == ".docx":
        content = read_docx_from_bytes(file_bytes)
        encoding = "utf-8"
        file_type = "docx"
    else:
        raise ValueError(f"不支持的文件格式: {ext}，请上传 .txt 或 .docx 文件")

    # 章节检测与拆分
    chapters = split_chapters(content, min_chapters=1)

    # 计算总字符数
    total_chars = sum(ch.char_count for ch in chapters)

    return NovelFile(
        filename=filename,
        file_type=file_type,
        encoding=encoding,
        chapters=chapters,
        total_chars=total_chars
    )
