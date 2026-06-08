"""
剧本转换主逻辑
支持批量章节合并，大幅减少API调用次数
"""

import json
import re
import yaml
from datetime import datetime
from typing import Callable, Optional

from backend.models.models import (
    Chapter, NovelFile, Screenplay, ScreenplayMetadata,
    Scene, ScreenplayLine, ActionLine, DialogueLine, Transition
)
from backend.converter.llm_client import LLMClient
from backend.converter.prompt_builder import (
    SYSTEM_PROMPT,
    build_chapter_convert_prompt,
    build_metadata_prompt
)

# 每批合并多少章（一次API调用处理N章）
BATCH_SIZE = 3
# 每章最多取多少字送入API（控制token量）
MAX_CHARS_PER_CHAPTER = 2000
# 每批最大输出token数
MAX_TOKENS_PER_BATCH = 16000


class ScreenplayConverter:
    """剧本转换器（支持批量处理）"""

    def __init__(self, llm_client: LLMClient, batch_size: int = BATCH_SIZE):
        self.llm = llm_client
        self.batch_size = batch_size
        self._progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self._progress_callback = callback

    def _report_progress(self, step: str, current: int, total: int, detail: str = ""):
        """报告进度"""
        if self._progress_callback:
            self._progress_callback({
                "step": step,
                "current": current,
                "total": total,
                "detail": detail,
                "percent": int(current / max(total, 1) * 100)
            })

    def extract_metadata(self, novel_file: NovelFile) -> ScreenplayMetadata:
        """从小说中提取元数据"""
        self._report_progress("提取元数据", 0, 1, "正在分析小说内容...")

        sample_content = ""
        for ch in novel_file.chapters[:3]:
            sample_content += f"\n{ch.title}\n{ch.content[:1000]}\n"

        prompt = build_metadata_prompt(sample_content, novel_file.filename)

        try:
            response = self.llm.chat(SYSTEM_PROMPT, prompt, temperature=0.3, max_tokens=500)
            response = response.strip()
            response = re.sub(r'^```(?:json)?\s*', '', response)
            response = re.sub(r'\s*```$', '', response)

            data = json.loads(response)
            self._report_progress("提取元数据", 1, 1, "元数据提取完成")

            return ScreenplayMetadata(
                title=data.get("title", novel_file.filename),
                genre=data.get("genre", ""),
                characters=data.get("characters", []),
                synopsis=data.get("synopsis", ""),
                source_chapters=len(novel_file.chapters),
                created_at=datetime.now().isoformat(),
                version="1.0"
            )
        except (json.JSONDecodeError, Exception) as e:
            self._report_progress("提取元数据", 1, 1, f"元数据提取使用默认值: {str(e)}")
            return ScreenplayMetadata(
                title=novel_file.filename,
                source_chapters=len(novel_file.chapters),
                created_at=datetime.now().isoformat()
            )

    def _build_batch_prompt(self, chapters: list[Chapter], batch_index: int, total_batches: int) -> str:
        """构建批量章节转换的提示词"""
        parts = []

        parts.append(f"## 待转换内容")
        parts.append(f"这是第 {batch_index}/{total_batches} 批，包含 {len(chapters)} 个章节。\n")

        for ch in chapters:
            # 截取每章内容，控制token量
            content = ch.content[:MAX_CHARS_PER_CHAPTER]
            if len(ch.content) > MAX_CHARS_PER_CHAPTER:
                content += "\n...（后续内容省略）"
            parts.append(f"### {ch.title}\n{content}\n")

        parts.append("## 要求")
        parts.append("请将上述**所有章节**内容转换为YAML格式的剧本，**不要遗漏任何一个章节**。")
        parts.append("要求：")
        parts.append("1. 每个场景的scene_number从1开始连续编号")
        parts.append("2. 准确识别对白（注意中文的\"说\"\"道\"等对话标记）")
        parts.append("3. 直接输出YAML数组，不要包含```yaml标记或其他说明文字")
        parts.append("4. 确保输出是合法的YAML格式")
        parts.append("5. 每章至少生成1个场景，所有章节都要有对应的场景输出")

        return "\n".join(parts)

    def convert_batch(
        self,
        chapters: list[Chapter],
        batch_index: int,
        total_batches: int
    ) -> list[Scene]:
        """转换一批章节"""
        self._report_progress(
            "转换章节",
            batch_index,
            total_batches,
            f"正在转换第 {batch_index} 批（{chapters[0].title} ~ {chapters[-1].title}）"
        )

        prompt = self._build_batch_prompt(chapters, batch_index, total_batches)
        response = self.llm.chat(SYSTEM_PROMPT, prompt, temperature=0.3, max_tokens=MAX_TOKENS_PER_BATCH)

        scenes = self._parse_scenes_yaml(response)

        self._report_progress(
            "转换章节",
            batch_index,
            total_batches,
            f"第 {batch_index} 批完成，生成 {len(scenes)} 个场景"
        )

        return scenes

    def _parse_scenes_yaml(self, yaml_str: str) -> list[Scene]:
        """解析LLM返回的YAML为场景列表"""
        yaml_str = yaml_str.strip()
        yaml_str = re.sub(r'^```(?:yaml)?\s*', '', yaml_str)
        yaml_str = re.sub(r'\s*```$', '', yaml_str)

        try:
            data = yaml.safe_load(yaml_str)

            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                return []

            scenes = []
            for item in data:
                try:
                    if not isinstance(item, dict):
                        continue

                    lines = []
                    for line_data in item.get("lines", []):
                        if not isinstance(line_data, dict):
                            continue
                        line_type = line_data.get("line_type", "action")

                        if line_type == "action":
                            action_data = line_data.get("action", {})
                            if isinstance(action_data, str):
                                action_data = {"content": action_data}
                            elif not isinstance(action_data, dict):
                                action_data = {"content": str(action_data)}
                            lines.append(ScreenplayLine(
                                line_type="action",
                                action=ActionLine(
                                    content=action_data.get("content", ""),
                                    character=action_data.get("character")
                                )
                            ))
                        elif line_type == "dialogue":
                            dial_data = line_data.get("dialogue", {})
                            if isinstance(dial_data, str):
                                dial_data = {"character": "未知", "content": dial_data}
                            elif not isinstance(dial_data, dict):
                                continue
                            lines.append(ScreenplayLine(
                                line_type="dialogue",
                                dialogue=DialogueLine(
                                    character=dial_data.get("character", "未知"),
                                    parenthetical=dial_data.get("parenthetical"),
                                    content=dial_data.get("content", "")
                                )
                            ))
                        elif line_type == "transition":
                            trans_data = line_data.get("transition", {})
                            if isinstance(trans_data, dict):
                                lines.append(ScreenplayLine(
                                    line_type="transition",
                                    transition=Transition(
                                        type=trans_data.get("type", "CUT_TO"),
                                        target=trans_data.get("target")
                                    )
                                ))

                    scene = Scene(
                        scene_number=item.get("scene_number", len(scenes) + 1),
                        scene_heading=item.get("scene_heading", "INT. 未知 - DAY"),
                        location=item.get("location", "未知"),
                        scene_type=item.get("scene_type", "INT"),
                        time_of_day=item.get("time_of_day", "DAY"),
                        characters=item.get("characters", []),
                        summary=item.get("summary", ""),
                        lines=lines
                    )
                    scenes.append(scene)
                except Exception:
                    continue

            return scenes

        except yaml.YAMLError:
            return []

    def convert_novel(self, novel_file: NovelFile) -> Screenplay:
        """
        完整转换流程：批量处理，大幅减少API调用

        原来：每章2次API调用（转换+摘要），1003章 = 2006次
        现在：每5章1次调用，1003章 = ~201次，快10倍
        """
        total_chapters = len(novel_file.chapters)

        # 1. 提取元数据
        metadata = self.extract_metadata(novel_file)
        metadata.total_scenes = 0

        # 2. 分批转换
        all_scenes: list[Scene] = []
        scene_counter = 0

        # 将章节分成批次
        batches: list[list[Chapter]] = []
        for i in range(0, total_chapters, self.batch_size):
            batch = novel_file.chapters[i:i + self.batch_size]
            batches.append(batch)

        total_batches = len(batches)

        for batch_idx, batch in enumerate(batches):
            try:
                scenes = self.convert_batch(batch, batch_idx + 1, total_batches)

                # 重新编号
                for scene in scenes:
                    scene_counter += 1
                    scene.scene_number = scene_counter

                all_scenes.extend(scenes)
            except Exception as e:
                # 单批失败不影响整体
                self._report_progress(
                    "转换章节",
                    batch_idx + 1,
                    total_batches,
                    f"第 {batch_idx + 1} 批转换失败: {str(e)}，跳过"
                )
                continue

        # 3. 更新元数据
        metadata.total_scenes = len(all_scenes)

        # 4. 汇总角色
        all_characters = set()
        for scene in all_scenes:
            all_characters.update(scene.characters)
        if not metadata.characters:
            metadata.characters = sorted(list(all_characters))

        return Screenplay(metadata=metadata, scenes=all_scenes)
