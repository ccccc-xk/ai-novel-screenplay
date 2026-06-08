"""
小说解析模块测试
"""

import pytest
from backend.parser.chapter_detector import split_chapters, detect_chapter_title
from backend.parser.txt_parser import read_txt_from_bytes


class TestChapterDetector:
    """章节检测测试"""

    def test_detect_chinese_chapter_title(self):
        """测试中文章节标题检测"""
        assert detect_chapter_title("第一章 初遇") == True
        assert detect_chapter_title("第二十三章 暗流涌动") == True
        assert detect_chapter_title("第1章 开始") == True

    def test_detect_markdown_title(self):
        """测试Markdown标题检测"""
        assert detect_chapter_title("# 第一章") == True
        assert detect_chapter_title("## 序章") == True

    def test_reject_normal_text(self):
        """测试普通文本不被误判为章节"""
        assert detect_chapter_title("他走在路上，心里想着昨天的事。") == False
        assert detect_chapter_title("") == False

    def test_split_chapters_with_titles(self):
        """测试带标题的章节拆分"""
        text = """第一章 开始

这是第一章的内容。

第二章 发展

这是第二章的内容。

第三章 高潮

这是第三章的内容。"""

        chapters = split_chapters(text)
        assert len(chapters) == 3
        assert chapters[0].title == "第一章 开始"
        assert chapters[1].title == "第二章 发展"
        assert chapters[2].title == "第三章 高潮"
        assert "第一章的内容" in chapters[0].content

    def test_split_chapters_without_titles(self):
        """测试无章节标题时按字数拆分"""
        text = "这是一段很长的文本。" * 200
        chapters = split_chapters(text, min_chapters=3)
        assert len(chapters) >= 3

    def test_chapter_char_count(self):
        """测试章节字数统计"""
        text = """第一章 测试

这是测试内容，共二十个字左右。"""

        chapters = split_chapters(text)
        assert len(chapters) == 1
        assert chapters[0].char_count > 0


class TestTxtParser:
    """TXT解析测试"""

    def test_read_utf8(self):
        """测试UTF-8编码读取"""
        content = "这是UTF-8编码的中文内容"
        data = content.encode("utf-8")
        result, encoding = read_txt_from_bytes(data)
        assert "中文内容" in result

    def test_read_gbk(self):
        """测试GBK编码读取"""
        content = "这是GBK编码的中文内容"
        data = content.encode("gbk")
        result, encoding = read_txt_from_bytes(data)
        assert "中文内容" in result
