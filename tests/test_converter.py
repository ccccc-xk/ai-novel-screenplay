"""
AI转换模块测试（单元测试，不调用真实API）
"""

import pytest
from backend.converter.prompt_builder import (
    build_chapter_convert_prompt,
    build_context_summary_prompt,
    build_metadata_prompt,
    SYSTEM_PROMPT
)
from backend.models.models import Chapter


class TestPromptBuilder:
    """Prompt构建测试"""

    def test_system_prompt_not_empty(self):
        """系统提示词不为空"""
        assert len(SYSTEM_PROMPT) > 100

    def test_chapter_convert_prompt(self):
        """章节转换提示词构建"""
        chapter = Chapter(index=1, title="第一章 测试", content="测试内容", char_count=4)
        prompt = build_chapter_convert_prompt(
            chapter.title,
            chapter.content,
            1,
            3
        )

        assert "第一章 测试" in prompt
        assert "测试内容" in prompt
        assert "1/3" in prompt

    def test_chapter_convert_with_context(self):
        """带上下文的章节转换提示词"""
        prompt = build_chapter_convert_prompt(
            "第二章", "内容", 2, 3, "前文摘要内容"
        )
        assert "前文摘要内容" in prompt

    def test_context_summary_prompt(self):
        """上下文摘要提示词"""
        prompt = build_context_summary_prompt("一段内容", "第一章")
        assert "第一章" in prompt
        assert "一段内容" in prompt

    def test_metadata_prompt(self):
        """元数据提取提示词"""
        prompt = build_metadata_prompt("小说内容", "测试小说")
        assert "测试小说" in prompt
