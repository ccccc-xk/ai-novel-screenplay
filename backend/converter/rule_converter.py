"""
规则引擎转换器
使用正则表达式和规则将小说转换为剧本格式
"""

import re
import yaml
from datetime import datetime
from backend.models.models import (
    Chapter, NovelFile, Screenplay, ScreenplayMetadata,
    Scene, ScreenplayLine, ActionLine, DialogueLine, Transition
)

# ===== 常量 =====

SPEECH_VERBS = (
    '低声说|轻声说|大声说|高声说|急忙说|慌忙说|冷冷说|淡淡说|幽幽说|默默说|轻轻说|缓缓说|'
    '狠狠说|慢慢说|急忙道|慌忙道|冷冷道|淡淡道|幽幽道|轻轻道|缓缓道|'
    '说|道|喊|问|答|叫|嚷|吼|笑|叹|怒|骂|喝|唤|'
    '笑道|叹道|怒道|骂道|喝道|吼道|叫道|问道|答道|'
    '冷笑道|苦笑道|微笑道|轻声道|低声道|大声道|高声道|沉声道|'
    '冷冷道|淡淡道|幽幽道|狠狠道|缓缓道|急忙道|慌忙道'
)

TIME_KEYWORDS = {
    '清晨': 'MORNING', '早上': 'MORNING', '早晨': 'MORNING', '上午': 'MORNING',
    '中午': 'DAY', '下午': 'DAY',
    '傍晚': 'EVENING', '黄昏': 'DUSK',
    '深夜': 'NIGHT', '夜晚': 'NIGHT', '夜里': 'NIGHT', '晚上': 'NIGHT',
    '半夜': 'NIGHT', '凌晨': 'NIGHT',
}

SCENE_SHIFT_WORDS = [
    '第二天', '次日', '当天晚上', '当天下午', '当天上午',
    '一周后', '一个月后', '一年后', '几年后', '几天后',
    '此时', '与此同时', '另一边',
    '回到家', '来到', '走进', '走出', '推开',
    '入夜', '天亮', '天黑',
    '不久后', '过了一会儿', '片刻后',
]

EXT_LOCATIONS = ['街道', '马路', '路上', '河边', '山上', '公园', '广场', '花园', '操场', '天台', '楼顶']

BAD_NAME_CHARS = set('的了吗呢啊吧呀嘛着过还在不也有都人这那我你他她一二三四五六七八九十递接看走跑拿放站坐推打开转')
BAD_NAME_SUFFIXES = set('慌忙急忙急急冷冷淡淡轻轻缓缓慢慢狠狠微微默默悄悄偷偷认真紧张着急')


def _valid_name(name: str) -> bool:
    if len(name) < 2 or len(name) > 4:
        return False
    if any(c in BAD_NAME_CHARS for c in name):
        return False
    if name in BAD_NAME_SUFFIXES:
        return False
    return True


def _clean_name(name: str) -> str:
    """清理可能包含动作后缀的名字（如 '苏然慌忙' → '苏然'）"""
    # 尝试从长名字中提取有效人名（2-3字）
    for length in [2, 3]:
        candidate = name[:length]
        rest = name[length:]
        if _valid_name(candidate) and rest and rest[0] in '慌忙急冷淡轻轻缓慢狠微默悄偷认紧':
            return candidate
    return name if _valid_name(name) else ""


# ===== 场景检测 =====

def detect_time_of_day(text: str) -> str:
    for kw, t in TIME_KEYWORDS.items():
        if kw in text:
            return t
    return 'DAY'


def detect_location(text: str) -> str:
    m = re.search(r'在([一-鿿]{2,12}?)(?:里|中|内|外|上|下|旁|边|门口|前|后)', text[:300])
    if m:
        return m.group(1).strip()
    nouns = [
        '办公室', '会议室', '教室', '宿舍', '家里', '家中', '医院', '学校',
        '餐厅', '饭店', '咖啡馆', '酒吧', '商场', '书店', '图书馆',
        '机场', '车站', '地铁站', '酒店', '公园', '河边',
        '街道', '马路', '路上', '车里', '车上', '门口', '楼下',
        '卧室', '客厅', '厨房', '阳台', '公司', '大厦', '广场',
        '大厅', '走廊', '操场', '食堂', '包间',
    ]
    for n in nouns:
        if n in text[:200]:
            return n
    return '未知地点'


def is_exterior(loc: str) -> bool:
    return any(w in loc for w in EXT_LOCATIONS)


def is_scene_shift(para: str) -> bool:
    f = para[:50]
    return any(w in f for w in SCENE_SHIFT_WORDS)


# ===== 对话提取 =====

def extract_all_dialogues(text: str) -> list:
    results = []
    used = set()

    # 模式A：句首 人名+说话动词+冒号+引号
    pat_a = re.compile(
        f'(?:^|[。！？\\n])\\s*([一-鿿]{{2,4}})(?:{SPEECH_VERBS})[着了道]?\\s*[：:]\\s*["「『]([^"」』]+?)["」』]'
    )
    for m in pat_a.finditer(text):
        n, c = m.group(1).strip(), m.group(2).strip()
        if n and c and _valid_name(n):
            results.append((n, c, m.start(), m.end()))
            used.add((m.start(), m.end()))

    # 模式B：句首 人名+冒号+引号（无说话动词）
    pat_b = re.compile(
        f'(?:^|[。！？\\n])\\s*([一-鿿]{{2,4}})\\s*[：:]\\s*["「『]([^"」』]+?)["」』]'
    )
    for m in pat_b.finditer(text):
        if any(m.start() >= r[0] and m.start() < r[1] for r in used):
            continue
        n, c = m.group(1).strip(), m.group(2).strip()
        if n and c and _valid_name(n):
            results.append((n, c, m.start(), m.end()))
            used.add((m.start(), m.end()))

    # 模式B2：任意位置 人名+冒号+引号（处理"她尽量保持平静：\"xxx\""）
    pat_b2 = re.compile(
        f'([一-鿿]{{2,4}})\\s*[：:]\\s*["「『]([^"」』]+?)["」』]'
    )
    for m in pat_b2.finditer(text):
        if any(m.start() >= r[0] and m.start() < r[1] for r in used):
            continue
        n, c = m.group(1).strip(), m.group(2).strip()
        if n and c and _valid_name(n):
            results.append((n, c, m.start(), m.end()))
            used.add((m.start(), m.end()))

    # 模式C：纯引号，向前/向后搜索说话人
    pat_c = re.compile('["「『‘]([^"」』’"\\n]{2,})["」』’"]?')
    for m in pat_c.finditer(text):
        if any(m.start() >= r[0] and m.start() < r[1] for r in used):
            continue
        content = m.group(1).strip()
        if not content or len(content) < 2:
            continue

        # 向前搜索：XXX说/道/笑 + 冒号
        pre = text[max(0, m.start() - 50):m.start()]
        name = ""
        pm = re.search(f'([一-鿿]{{2,4}})(?:{SPEECH_VERBS})[着了道]?\\s*[：:]*\\s*$', pre)
        if pm and _valid_name(pm.group(1)):
            name = pm.group(1)

        # 向前搜索：XXX（动作）。
        if not name:
            pm = re.search(r'([一-鿿]{2,4})[^\n。！？]{0,20}[。！？]\s*$', pre)
            if pm and _valid_name(pm.group(1)):
                name = pm.group(1)

        # 向后搜索：引号后紧跟 人名+动作/说话动词
        if not name:
            post = text[m.end():m.end() + 30]
            pm = re.match(r'([一-鿿]{2,4})', post)
            if pm:
                name = _clean_name(pm.group(1))

        results.append((name, content, m.start(), m.end()))

    results.sort(key=lambda x: x[2])
    return results


def extract_parenthetical(text: str, dialog_start: int) -> str:
    pre = text[max(0, dialog_start - 60):dialog_start]
    m = re.search(
        '(低声|轻声|大声|高声|沉声|冷冷|淡淡|幽幽|默默|轻轻|缓缓|狠狠|微微|急忙|慌忙|'
        '紧张|认真|严肃|诚恳|温柔|无奤|苦笑|微笑|冷笑|惊讶|愤怒|平静|好奇|疑惑|感慨|羞涩|尴尬)',
        pre
    )
    return m.group(1) if m else None


def summarize_scene(lines: list) -> str:
    for line in lines:
        if line.line_type == "dialogue" and line.dialogue:
            return f"{line.dialogue.character}：{line.dialogue.content[:40]}"
        elif line.line_type == "action" and line.action:
            t = line.action.content.strip()
            if len(t) > 10:
                return t[:50]
    return ""


# ===== 主转换 =====

def convert_chapter_to_scenes(chapter: Chapter, scene_start: int) -> list[Scene]:
    paragraphs = [p.strip() for p in chapter.content.split('\n') if p.strip()]
    if not paragraphs:
        return []

    scenes = []
    cur_lines = []
    cur_loc = "未知地点"
    cur_time = "DAY"
    cur_chars = set()

    def flush():
        nonlocal cur_lines, cur_chars
        if not cur_lines:
            return
        num = scene_start + len(scenes) + 1
        stype = "EXT" if is_exterior(cur_loc) else "INT"
        scenes.append(Scene(
            scene_number=num, scene_heading=f"{stype}. {cur_loc} - {cur_time}",
            location=cur_loc, scene_type=stype, time_of_day=cur_time,
            characters=sorted(cur_chars), summary=summarize_scene(cur_lines),
            lines=list(cur_lines)
        ))
        cur_lines.clear()
        cur_chars = set()

    for para in paragraphs:
        shift = is_scene_shift(para)
        if shift and cur_lines:
            flush()

        t = detect_time_of_day(para)
        if t != 'DAY' or shift:
            cur_time = t
        if shift:
            loc = detect_location(para)
            if loc != '未知地点':
                cur_loc = loc

        dial = extract_all_dialogues(para)
        if dial:
            last = 0
            for name, text, ds, de in dial:
                pre = para[last:ds].strip()
                if pre and len(pre) > 2:
                    cl = re.sub(r'\s+', ' ', pre)
                    if len(cl) > 200: cl = cl[:200] + '...'
                    cur_lines.append(ScreenplayLine(line_type="action", action=ActionLine(content=cl)))

                if name:
                    cur_chars.add(name)
                    pt = extract_parenthetical(para, ds)
                    cur_lines.append(ScreenplayLine(
                        line_type="dialogue",
                        dialogue=DialogueLine(character=name, parenthetical=pt, content=text)
                    ))
                else:
                    cur_lines.append(ScreenplayLine(
                        line_type="action", action=ActionLine(content=f'（画外音）{text}')
                    ))
                last = de

            post = para[last:].strip()
            if post and len(post) > 2:
                cl = re.sub(r'\s+', ' ', post)
                if len(cl) > 200: cl = cl[:200] + '...'
                cur_lines.append(ScreenplayLine(line_type="action", action=ActionLine(content=cl)))
        else:
            cl = re.sub(r'\s+', ' ', para)
            if len(cl) > 300: cl = cl[:300] + '...'
            cur_lines.append(ScreenplayLine(line_type="action", action=ActionLine(content=cl)))

    flush()
    return scenes


def convert_novel_by_rule(novel_file: NovelFile, novel_title: str = "") -> Screenplay:
    MAX = 3000
    all_s, all_c = [], set()
    for ch in novel_file.chapters:
        lc = Chapter(index=ch.index, title=ch.title, content=ch.content[:MAX], char_count=min(ch.char_count, MAX))
        ss = convert_chapter_to_scenes(lc, len(all_s))
        all_s.extend(ss)
        for s in ss: all_c.update(s.characters)
    title = novel_title or novel_file.filename.rsplit('.', 1)[0]
    meta = ScreenplayMetadata(title=title, genre="", characters=sorted(all_c), synopsis="",
        source_chapters=len(novel_file.chapters), total_scenes=len(all_s),
        created_at=datetime.now().isoformat(), version="1.0")
    return Screenplay(metadata=meta, scenes=all_s)


def convert_chapters_to_screenplay_yaml(chapters: list[dict], novel_title: str = "", scene_start: int = 0) -> str:
    MAX = 3000
    all_s = []
    for ch in chapters:
        c = ch["content"][:MAX]
        lc = Chapter(index=ch["index"], title=ch["title"], content=c, char_count=min(len(c), MAX))
        all_s.extend(convert_chapter_to_scenes(lc, scene_start + len(all_s)))
    return yaml.dump([s.model_dump() for s in all_s], allow_unicode=True, default_flow_style=False, sort_keys=False)
