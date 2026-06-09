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

# ===== 角色名验证 =====

# 常见中国姓氏（白名单思路：名字必须以姓氏开头）
SURNAMES = set(
    '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜'
    '戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐'
    '费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄'
    '和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁'
    '杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍'
    '虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚'
    '程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓'
    '牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙'
    '叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双'
    '闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农'
    '温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘'
    '匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空'
    '曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公'
    # 常见复姓
    '司马上官欧阳夏侯诸葛闻人东方赫连皇甫尉迟公羊澹台公冶宗政濮阳淳于'
    '单于太叔申屠公孙仲孙轩辕令狐钟离宇文长孙慕容鲜于闾丘司徒司空亓官'
    '司寇仉督子车颛孙端木巫马公西漆雕乐正壤驷公良拓跋夹谷宰父谷梁段干'
    '百里东郭南门呼延归海羊舌微生梁丘左丘东门西门南宫'
    # 也包含常见名字用字作为fallback
    '林苏陈李张王赵刘周吴郑黄杨朱许何郭马胡罗高谢韩唐冯于董萧程曹袁邓'
)

# 只排除明确的非人名用字（代词、数词、常见动词）
BAD_NAME_CHARS = set(
    '的了吗呢啊吧呀嘛着过还在不也有都人这那我你他她'
    '一二三四五六七八九十百千万'
    '递接看走跑拿放站坐推打开转说笑问答叫喊怒骂喝叹'
)


def _valid_name(name: str) -> bool:
    """严格验证：名字必须2-3字，以姓氏开头"""
    if len(name) < 2 or len(name) > 3:
        return False
    if any(c in BAD_NAME_CHARS for c in name):
        return False
    # 必须以姓氏开头
    if name[0] not in SURNAMES:
        return False
    return True


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
        f'(?:^|[。！？\\n])\\s*([一-鿿]{{2,3}})(?:{SPEECH_VERBS})[着了道]?\\s*[：:]\\s*["「『]([^"」』]+?)["」』]'
    )
    for m in pat_a.finditer(text):
        n, c = m.group(1).strip(), m.group(2).strip()
        if n and c and _valid_name(n):
            results.append((n, c, m.start(), m.end()))
            used.add((m.start(), m.end()))

    # 模式B：句首 人名+冒号+引号
    pat_b = re.compile(
        f'(?:^|[。！？\\n])\\s*([一-鿿]{{2,3}})\\s*[：:]\\s*["「『]([^"」』]+?)["」』]'
    )
    for m in pat_b.finditer(text):
        if any(m.start() >= r[0] and m.start() < r[1] for r in used):
            continue
        n, c = m.group(1).strip(), m.group(2).strip()
        if n and c and _valid_name(n):
            results.append((n, c, m.start(), m.end()))
            used.add((m.start(), m.end()))

    # 模式C：纯引号，只通过向前搜索找说话人（要求有说话动词或冒号）
    pat_c = re.compile('["「『‘]([^"」』’"\\n]{2,})["」』’"]?')
    for m in pat_c.finditer(text):
        if any(m.start() >= r[0] and m.start() < r[1] for r in used):
            continue
        content = m.group(1).strip()
        if not content or len(content) < 2:
            continue

        # 向前50字内找 "人名+说话动词" 或 "人名+冒号"
        pre = text[max(0, m.start() - 50):m.start()]
        name = ""

        # 人名+说话动词+冒号
        pm = re.search(f'([一-鿿]{{2,3}})(?:{SPEECH_VERBS})[着了道]?\\s*[：:]*\\s*$', pre)
        if pm and _valid_name(pm.group(1)):
            name = pm.group(1)

        # 人名+冒号（无说话动词）
        if not name:
            pm = re.search(r'([一-鿿]{2,3})\s*[：:]\s*$', pre)
            if pm and _valid_name(pm.group(1)):
                name = pm.group(1)

        # 找到有效说话人才添加
        if name:
            results.append((name, content, m.start(), m.end()))

    results.sort(key=lambda x: x[2])
    return results


def extract_parenthetical(text: str, dialog_start: int) -> str:
    pre = text[max(0, dialog_start - 40):dialog_start]
    m = re.search(
        '(低声|轻声|大声|高声|沉声|冷冷|淡淡|幽幽|默默|轻轻|缓缓|狠狠|微微|急忙|慌忙|'
        '紧张|认真|严肃|诚恳|温柔|苦笑|微笑|冷笑|惊讶|愤怒|平静|好奇|疑惑|感慨|羞涩|尴尬)',
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
