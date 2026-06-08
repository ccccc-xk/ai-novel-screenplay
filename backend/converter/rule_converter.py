"""
规则引擎转换器
不调用AI API，使用正则表达式和规则将小说转换为剧本格式
效果有限但完全免费、离线可用
"""

import re
import yaml
from datetime import datetime
from backend.models.models import (
    Chapter, NovelFile, Screenplay, ScreenplayMetadata,
    Scene, ScreenplayLine, ActionLine, DialogueLine, Transition
)


# 常见的对白引号模式
DIALOGUE_PATTERNS = [
    # 中文引号："xxx" 『xxx』
    re.compile(r'[""「]([^""」]+)[""」]'),
    # 冒号后跟对白：他说：xxx
    re.compile(r'[说道喊问答叫嚷吼低声笑道叹道怒道冷笑道](?:着|了|道)?[：:]\s*[""「]?([^""」\n]{2,})'),
]

# 对话行模式：角色名 + 说/道 + 对白
SPEECH_PATTERN = re.compile(
    r'([^\s,，。！!？?""]{2,4})'  # 角色名（2-4字）
    r'[说道喊问答叫嚷吼笑了笑叹怒冷冷轻低声]'  # 说话动词
    r'[着了道]?[：:]\s*'  # 冒号
    r'[""「]?([^""」\n]+)[""」]?'  # 对白内容
)

# 纯对白模式：只有引号内容
PURE_DIALOGUE_PATTERN = re.compile(r'[""「]([^""」\n]{2,})[""」]')

# 场景切换提示词
SCENE_CHANGE_KEYWORDS = [
    '第二天', '次日', '当天晚上', '当天下午', '当天上午',
    '一周后', '一个月后', '一年后', '几年后',
    '此时', '与此同时', '另一边',
    '回到家', '来到', '走进', '走出', '推开',
    '深夜', '清晨', '傍晚', '黄昏',
]

# 时间词
TIME_KEYWORDS = {
    '清晨': 'MORNING', '早上': 'MORNING', '上午': 'MORNING',
    '中午': 'DAY', '下午': 'DAY',
    '傍晚': 'EVENING', '黄昏': 'DUSK',
    '深夜': 'NIGHT', '夜晚': 'NIGHT', '夜里': 'NIGHT', '晚上': 'NIGHT',
    '夜里': 'NIGHT', '半夜': 'NIGHT',
}


def extract_characters_from_text(text: str) -> list[str]:
    """从文本中提取可能的角色名"""
    # 使用说话模式提取角色名
    characters = set()
    for match in SPEECH_PATTERN.finditer(text):
        name = match.group(1).strip()
        if 2 <= len(name) <= 4 and not any(c in name for c in '的了吗呢啊吧呀哦嗯'):
            characters.add(name)
    return sorted(list(characters))


def detect_time_of_day(text: str) -> str:
    """从文本中检测时间"""
    for keyword, time_val in TIME_KEYWORDS.items():
        if keyword in text:
            return time_val
    return 'DAY'


def detect_location(text: str) -> str:
    """从文本中检测地点"""
    location_patterns = [
        re.compile(r'在([^，。！？\n]{2,10})(?:里|中|内|外|上|下|旁|边|门口)'),
        re.compile(r'([^，。！？\n]{2,8})(?:里|中|内|外|上|下|旁|边|门口)'),
    ]
    for pattern in location_patterns:
        match = pattern.search(text[:200])
        if match:
            loc = match.group(1).strip()
            if len(loc) >= 2:
                return loc
    return '未知地点'


def convert_chapter_to_scenes(chapter: Chapter, scene_start: int) -> list[Scene]:
    """将单个章节转换为场景列表"""
    paragraphs = [p.strip() for p in chapter.content.split('\n') if p.strip()]

    if not paragraphs:
        return []

    scenes = []
    current_scene_lines: list[ScreenplayLine] = []
    current_location = ""
    current_time = "DAY"
    scene_chars = set()

    def flush_scene():
        nonlocal current_scene_lines, current_location, current_time, scene_chars
        if not current_scene_lines:
            return
        scene_num = scene_start + len(scenes) + 1
        stype = "INT"  # 默认内景
        heading = f"{stype}. {current_location or '未知地点'} - {current_time}"

        scenes.append(Scene(
            scene_number=scene_num,
            scene_heading=heading,
            location=current_location or "未知地点",
            scene_type=stype,
            time_of_day=current_time,
            characters=sorted(list(scene_chars)),
            summary="",
            lines=current_scene_lines
        ))
        current_scene_lines = []
        scene_chars = set()

    for para in paragraphs:
        # 检测是否需要新场景
        is_scene_change = any(kw in para[:50] for kw in SCENE_CHANGE_KEYWORDS)

        if is_scene_change and current_scene_lines:
            flush_scene()
            current_location = detect_location(para)
            current_time = detect_time_of_day(para)

        # 提取对白
        dialogue_matches = list(SPEECH_PATTERN.finditer(para))

        if dialogue_matches:
            last_end = 0
            for match in dialogue_matches:
                # 对白前面的叙述作为动作
                pre_text = para[last_end:match.start()].strip()
                if pre_text and len(pre_text) > 3:
                    current_scene_lines.append(ScreenplayLine(
                        line_type="action",
                        action=ActionLine(content=pre_text)
                    ))

                char_name = match.group(1).strip()
                dialogue_text = match.group(2).strip()
                scene_chars.add(char_name)

                # 提取表演提示
                parenthetical = None
                hint_match = re.search(r'[低声笑怒冷冷轻叹](?:道|着|声)?', match.group(0))
                if hint_match:
                    parenthetical = hint_match.group(0).replace('道', '').replace('着', '')

                current_scene_lines.append(ScreenplayLine(
                    line_type="dialogue",
                    dialogue=DialogueLine(
                        character=char_name,
                        parenthetical=parenthetical,
                        content=dialogue_text
                    )
                ))
                last_end = match.end()

            # 对白后面的叙述
            post_text = para[last_end:].strip()
            if post_text and len(post_text) > 3:
                current_scene_lines.append(ScreenplayLine(
                    line_type="action",
                    action=ActionLine(content=post_text)
                ))
        else:
            # 纯叙述段落
            current_scene_lines.append(ScreenplayLine(
                line_type="action",
                action=ActionLine(content=para)
            ))

    # 刷新最后一个场景
    flush_scene()
    return scenes


def convert_novel_by_rule(novel_file: NovelFile, novel_title: str = "") -> Screenplay:
    """
    使用规则引擎将小说转换为剧本

    Args:
        novel_file: 解析好的小说文件
        novel_title: 小说标题

    Returns:
        完整的剧本对象
    """
    all_scenes: list[Scene] = []
    all_characters = set()

    for chapter in novel_file.chapters:
        scenes = convert_chapter_to_scenes(chapter, len(all_scenes))
        all_scenes.extend(scenes)
        for scene in scenes:
            all_characters.update(scene.characters)

    # 为每个场景生成摘要
    for scene in all_scenes:
        action_texts = [l.action.content for l in scene.lines if l.line_type == "action" and l.action]
        if action_texts:
            scene.summary = action_texts[0][:50]

    title = novel_title or novel_file.filename.rsplit('.', 1)[0]

    metadata = ScreenplayMetadata(
        title=title,
        genre="",
        characters=sorted(list(all_characters)),
        synopsis="",
        source_chapters=len(novel_file.chapters),
        total_scenes=len(all_scenes),
        created_at=datetime.now().isoformat(),
        version="1.0"
    )

    return Screenplay(metadata=metadata, scenes=all_scenes)
