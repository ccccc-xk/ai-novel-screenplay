"""
TXT文件解析器
支持UTF-8/GBK编码自动检测
"""

import chardet
from pathlib import Path


def detect_encoding(file_path: str) -> str:
    """检测文件编码"""
    with open(file_path, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result.get("encoding", "utf-8")
        # chardet有时返回None或不准确的编码
        if encoding is None or encoding.lower() in ("ascii",):
            encoding = "utf-8"
        return encoding


def read_txt_file(file_path: str) -> tuple[str, str]:
    """
    读取TXT文件
    返回: (文件内容, 编码)
    """
    encoding = detect_encoding(file_path)

    # 尝试检测到的编码，失败则依次尝试常见编码
    encodings_to_try = [encoding, "utf-8", "gbk", "gb2312", "gb18030", "utf-16"]

    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            return content, enc
        except (UnicodeDecodeError, LookupError):
            continue

    # 最终兜底：忽略错误字符
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return content, "utf-8"


def read_txt_from_bytes(file_bytes: bytes, filename: str = "") -> tuple[str, str]:
    """从字节数据读取TXT内容"""
    result = chardet.detect(file_bytes)
    encoding = result.get("encoding", "utf-8") or "utf-8"

    encodings_to_try = [encoding, "utf-8", "gbk", "gb2312", "gb18030", "utf-16"]

    for enc in encodings_to_try:
        try:
            content = file_bytes.decode(enc)
            return content, enc
        except (UnicodeDecodeError, LookupError):
            continue

    content = file_bytes.decode("utf-8", errors="ignore")
    return content, "utf-8"
