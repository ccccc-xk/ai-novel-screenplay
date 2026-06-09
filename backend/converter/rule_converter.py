"""
规则引擎转换器
不调用AI API，使用正则表达式和规则将小说转换为剧本格式
参考AI转换样本质量标准，优化对话提取、场景分割、表演提示
"""

import re
import yaml
from datetime import datetime
from backend.models.models import (
    Chapter, NovelFile, Screenplay, ScreenplayMetadata,
    Scene, ScreenplayLine, ActionLine, DialogueLine, Transition
)

# ===== 对话提取模式 =====

# 模式1：引号对话 "xxx"「xxx」『xxx』
QUOTE_DIALOGUE = re.compile(
    r'[“「『‘]([^"」』’”\n]{2,})[”」』’“]?'
)

# 模式2：角色名 + 说话动词 + 冒号 + 引号
NAME_SPEECH_QUOTE = re.compile(
    r'([一-鿿]{2,6})'                    # 角色名（2-6个汉字）
    r'([\s]*(?:笑|叹|怒|冷|轻|低声|大|高声|沉声|冷声|厉声|轻声|柔声|淡淡|微微|急忙|慌忙|急忙|急|急急|着急|冷冷|淡淡|幽幽|默默|静静|偷偷|悄悄|慢慢|狠狠|淡淡|冷冷|轻轻|缓缓|深深|重重|微微|稍稍|略微|急忙|慌张|急忙|紧张|焦急|平静|认真|严肃|诚恳|真诚|温柔|关切|担忧|好奇|惊讶|惊讶|疑惑|困惑|沉思|思考|感叹|感慨|感叹|无奈|苦涩|自嘲|嘲讽|讥讽|冷嘲|讽刺|嘲笑|轻蔑|不屑|鄙夷|厌恶|厌烦|烦躁|暴怒|狂怒|大怒|震怒|愤怒|恼怒|恼火|生气|气愤|愤慨|悲痛|悲伤|悲愤|痛苦|难过|伤心|心碎|绝望|恐惧|害怕|惊恐|惊慌|慌张|紧张|焦虑|担忧|担心|忧虑|不安|忐忑|犹豫|迟疑|为难|尴尬|羞涩|害羞|羞愧|惭愧|内疚|自责|后悔|懊悔|后悔|遗憾|可惜|惋惜|同情|怜悯|心疼|欣慰|满意|高兴|开心|快乐|兴奋|激动|惊喜|惊讶|震惊|震撼|佩服|敬佩|尊敬|崇拜|仰慕|爱慕|思念|想念|牵挂|眷恋|不舍|留恋|依恋|痴迷|沉醉|陶醉|恍惚|出神|发呆|愣住|怔住))'
    r'[着了道]?[\s]*[：:]\s*'                     # 冒号
    r'[“「『]?([^”」』\n]{2,})[”」』]?'  # 对话内容
)

# 模式3：角色名 + 说 + 冒号 + 引号（宽松版）
NAME_SHUO = re.compile(
    r'([一-鿿]{2,6})'
    r'(?:说|道|喊|问|答|叫|嚷|吼|笑|叹|怒|骂|喝|嚷|唤|叫|低声说|轻声说|大声说|高声说|急忙说|慌忙说|急急说|冷冷说|淡淡说|幽幽说|默默说|轻轻说|缓缓说|狠狠说)'
    r'[着了道]?\s*[：:]\s*'
    r'[“「]?([^”」』\n]{2,})[”」』]?'
)

# ===== 场景检测 =====

# 位置关键词（出现在段首表示场景切换）
LOCATION_KEYWORDS = [
    '办公室', '会议室', '教室', '宿舍', '家里', '家中', '医院', '学校',
    '餐厅', '饭店', '咖啡', '酒吧', '商场', '超市', '书店', '图书馆',
    '机场', '车站', '地铁', '酒店', '旅馆', '公园', '河边', '山上',
    '街道', '马路', '路上', '车里', '车上', '门口', '楼下', '楼上',
    '卧室', '客厅', '厨房', '阳台', '卫生间', '浴室',
    '工厂', '公司', '大厦', '广场', '花园', '操场', '食堂',
    '前台', '大厅', '走廊', '楼梯', '电梯',
    '诊所', '药房', '银行', '邮局', '警察局', '法院',
    '厨房', '餐厅', '包间', '大厅',
]

# 时间关键词
TIME_KEYWORDS = {
    '清晨': 'MORNING', '早上': 'MORNING', '早晨': 'MORNING', '上午': 'MORNING',
    '中午': 'DAY', '下午': 'DAY',
    '傍晚': 'EVENING', '黄昏': 'DUSK',
    '深夜': 'NIGHT', '夜晚': 'NIGHT', '夜里': 'NIGHT', '晚上': 'NIGHT',
    '半夜': 'NIGHT', '凌晨': 'NIGHT',
}

# 场景切换信号词
SCENE_SHIFT_WORDS = [
    '第二天', '次日', '当天晚上', '当天下午', '当天上午',
    '一周后', '一个月后', '一年后', '几年后', '几天后', '几个小时后',
    '此时', '与此同时', '另一边', '与此同时', '话说',
    '回到家', '来到', '走进', '走出', '推开', '打开', '关上',
    '深夜', '清晨', '傍晚', '黄昏', '入夜', '天亮',
    '不久后', '过了一会儿', '过了许久', '半晌', '片刻后',
    '突然', '忽然', '猛然', '骤然',
]


def detect_time_of_day(text: str) -> str:
    for kw, t in TIME_KEYWORDS.items():
        if kw in text:
            return t
    return 'DAY'


def detect_location(text: str) -> str:
    # 优先匹配"在XXX里/中/上"模式
    m = re.search(r'在([一-鿿]{2,10})(?:里|中|内|外|上|下|旁|边|门口|前)', text[:300])
    if m:
        return m.group(1).strip()
    # 匹配地点关键词
    for kw in LOCATION_KEYWORDS:
        if kw in text[:200]:
            # 找到关键词在文本中的位置，提取前面的修饰词
            idx = text[:200].index(kw)
            prefix = text[max(0, idx - 5):idx].strip()
            if prefix and len(prefix) <= 6:
                return prefix + kw
            return kw
    return '未知地点'


def is_exterior(location: str) -> bool:
    outdoor_words = ['街道', '马路', '路上', '河边', '山上', '公园', '广场', '花园', '操场', '天台', '楼顶']
    return any(w in location for w in outdoor_words)


def is_scene_shift(paragraph: str) -> bool:
    """检测段落是否表示场景切换"""
    first_50 = paragraph[:50]
    # 时间跳转
    for word in SCENE_SHIFT_WORDS:
        if word in first_50:
            return True
    # 段首出现明确位置词
    for kw in LOCATION_KEYWORDS:
        if first_50.startswith(kw) or first_50.startswith('到了' + kw) or first_50.startswith('来到' + kw):
            return True
    return False


def extract_parenthetical(paragraph: str, char_name: str, dialog_text: str) -> str:
    """从对话上下文中提取表演提示"""
    # 在对话前的文本中找情绪/动作提示
    dialog_full = char_name + dialog_text
    idx = paragraph.find(dialog_text)
    if idx < 0:
        return None

    pre_text = paragraph[:idx]

    # 找最近的动作描写（在冒号/引号前的最后一句）
    # 常见模式：他/她 + 动作 + 说/道
    action_match = re.search(
        r'([一-鿿]{1,4})(?:了|着|地)?\s*([^。，,，“「]{2,10})$',
        pre_text
    )
    if action_match:
        hint = action_match.group(2).strip()
        # 过滤掉无意义的词
        skip_words = ['说道', '道', '说', '问', '答', '叫', '喊']
        if hint and hint not in skip_words and len(hint) >= 2:
            return hint[:10]

    # 从说话动词中提取
    verb_match = re.search(r'(低声|轻声|大声|高声|沉声|冷冷|淡淡|幽幽|默默|轻轻|缓缓|狠狠|微微|急忙|慌忙|急急|紧张|焦急|认真|严肃|诚恳|真诚|温柔|关切|担忧|好奇|惊讶|无奈|苦涩|自嘲|嘲讽|冷笑|苦笑|微笑|大笑|哈哈|嘿嘿)', pre_text)
    if verb_match:
        return verb_match.group(1)

    return None


def summarize_scene(lines: list) -> str:
    """从场景内容中生成有意义的摘要"""
    for line in lines:
        if line.line_type == "dialogue" and line.dialogue:
            char = line.dialogue.character
            content = line.dialogue.content
            if len(content) > 10:
                return f"{char}：{content[:40]}"
        elif line.line_type == "action" and line.action:
            text = line.action.content.strip()
            if len(text) > 10:
                return text[:50]
    return ""


def convert_chapter_to_scenes(chapter: Chapter, scene_start: int) -> list[Scene]:
    """将单个章节转换为场景列表"""
    paragraphs = [p.strip() for p in chapter.content.split('\n') if p.strip()]

    if not paragraphs:
        return []

    scenes: list[Scene] = []
    current_lines: list[ScreenplayLine] = []
    current_location = "未知地点"
    current_time = "DAY"
    scene_chars: set = set()

    def flush_scene():
        nonlocal current_lines, scene_chars
        if not current_lines:
            return

        scene_num = scene_start + len(scenes) + 1
        stype = "EXT" if is_exterior(current_location) else "INT"
        heading = f"{stype}. {current_location} - {current_time}"

        summary = summarize_scene(current_lines)

        scenes.append(Scene(
            scene_number=scene_num,
            scene_heading=heading,
            location=current_location,
            scene_type=stype,
            time_of_day=current_time,
            characters=sorted(list(scene_chars)),
            summary=summary,
            lines=list(current_lines)
        ))
        current_lines.clear()
        scene_chars = set()

    for para in paragraphs:
        # 检测场景切换
        scene_shift = is_scene_shift(para)

        if scene_shift and current_lines:
            flush_scene()

        # 更新场景位置和时间
        new_time = detect_time_of_day(para)
        if new_time != 'DAY':
            current_time = new_time
        if scene_shift:
            current_time = detect_time_of_day(para)
            new_loc = detect_location(para)
            if new_loc != '未知地点':
                current_location = new_loc

        # 提取对话
        dialogue_pairs = []  # [(char_name, dialog_text, start_pos, end_pos)]

        # 尝试模式2/3：角色名+说话动词+冒号+引号
        for pattern in [NAME_SPEECH_QUOTE, NAME_SHUO]:
            for m in pattern.finditer(para):
                name = m.group(1).strip()
                text = m.group(3).strip() if m.lastindex >= 3 else m.group(2).strip()
                if name and text and len(name) >= 2:
                    dialogue_pairs.append((name, text, m.start(), m.end()))

        # 尝试模式1：纯引号对话
        for m in QUOTE_DIALOGUE.finditer(para):
            text = m.group(1).strip()
            if text and len(text) >= 2:
                # 检查是否已被模式2/3覆盖
                already_covered = any(
                    m.start() >= dp[2] and m.start() < dp[3]
                    for dp in dialogue_pairs
                )
                if not already_covered:
                    # 尝试从引号前的文本找说话人
                    pre = para[max(0, m.start() - 10):m.start()]
                    name_match = re.search(r'([一-鿿]{2,4})[\s]*(?:说|道|问|答|笑|叹|怒)[着了道]?[：:]*\s*$', pre)
                    if name_match:
                        dialogue_pairs.append((name_match.group(1), text, m.start(), m.end()))
                    else:
                        dialogue_pairs.append(("", text, m.start(), m.end()))

        # 按位置排序
        dialogue_pairs.sort(key=lambda x: x[2])

        if dialogue_pairs:
            last_end = 0
            for char_name, dialog_text, dp_start, dp_end in dialogue_pairs:
                # 对话前的叙述作为动作
                pre_text = para[last_end:dp_start].strip()
                if pre_text and len(pre_text) > 2:
                    # 简化动作文本
                    cleaned = re.sub(r'\s+', ' ', pre_text)
                    if len(cleaned) > 200:
                        cleaned = cleaned[:200] + '...'
                    current_lines.append(ScreenplayLine(
                        line_type="action",
                        action=ActionLine(content=cleaned)
                    ))

                if char_name:
                    scene_chars.add(char_name)
                    # 提取表演提示
                    parenthetical = extract_parenthetical(para, char_name, dialog_text)

                    current_lines.append(ScreenplayLine(
                        line_type="dialogue",
                        dialogue=DialogueLine(
                            character=char_name,
                            parenthetical=parenthetical,
                            content=dialog_text
                        )
                    ))
                else:
                    # 无角色名的对话作为动作
                    current_lines.append(ScreenplayLine(
                        line_type="action",
                        action=ActionLine(content=f'（画外音）{dialog_text}')
                    ))

                last_end = dp_end

            # 对话后的叙述
            post_text = para[last_end:].strip()
            if post_text and len(post_text) > 2:
                cleaned = re.sub(r'\s+', ' ', post_text)
                if len(cleaned) > 200:
                    cleaned = cleaned[:200] + '...'
                current_lines.append(ScreenplayLine(
                    line_type="action",
                    action=ActionLine(content=cleaned)
                ))
        else:
            # 纯叙述段落
            cleaned = re.sub(r'\s+', ' ', para)
            if len(cleaned) > 300:
                cleaned = cleaned[:300] + '...'
            current_lines.append(ScreenplayLine(
                line_type="action",
                action=ActionLine(content=cleaned)
            ))

    flush_scene()
    return scenes


def convert_novel_by_rule(novel_file: NovelFile, novel_title: str = "") -> Screenplay:
    """
    使用规则引擎将小说转换为剧本
    每章最多处理3000字（完整章节内容）
    """
    MAX_CHARS_PER_CHAPTER = 3000
    all_scenes: list[Scene] = []
    all_characters = set()

    for chapter in novel_file.chapters:
        limited_chapter = Chapter(
            index=chapter.index,
            title=chapter.title,
            content=chapter.content[:MAX_CHARS_PER_CHAPTER],
            char_count=min(chapter.char_count, MAX_CHARS_PER_CHAPTER)
        )
        scenes = convert_chapter_to_scenes(limited_chapter, len(all_scenes))
        all_scenes.extend(scenes)
        for scene in scenes:
            all_characters.update(scene.characters)

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


def convert_chapters_to_screenplay_yaml(
    chapters: list[dict],
    novel_title: str = "",
    scene_start: int = 0
) -> str:
    """
    批量接口：接收章节数据列表，返回YAML格式的场景列表
    每章最多处理3000字
    """
    MAX_CHARS = 3000
    all_scenes: list[Scene] = []
    all_characters = set()

    for ch_data in chapters:
        limited_content = ch_data["content"][:MAX_CHARS]
        chapter = Chapter(
            index=ch_data["index"],
            title=ch_data["title"],
            content=limited_content,
            char_count=min(len(limited_content), MAX_CHARS)
        )
        scenes = convert_chapter_to_scenes(chapter, scene_start + len(all_scenes))
        all_scenes.extend(scenes)
        for scene in scenes:
            all_characters.update(scene.characters)

    scenes_data = [s.model_dump() for s in all_scenes]
    return yaml.dump(scenes_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
