"""
Prompt工程模块
构建高质量的提示词，引导LLM将小说转换为结构化剧本
"""

SYSTEM_PROMPT = """你是一位专业的剧本改编师。你的任务是将小说文本转换为标准的电影/电视剧剧本格式。

你需要严格按照以下YAML格式输出剧本，不要输出任何其他内容。

## 输出格式规范

每个场景必须包含以下结构：
```yaml
scene_number: 场景编号（整数）
scene_heading: "INT/EXT. 地点 - 时间" 格式的场景标题行
location: 地点名称
scene_type: INT 或 EXT
time_of_day: DAY/NIGHT/MORNING/EVENING/DAWN/DUSK
characters: [出场角色列表]
summary: 场景简要摘要
lines:
  - line_type: action
    action:
      content: "动作/场景描写内容"
  - line_type: dialogue
    dialogue:
      character: "角色名"
      parenthetical: "表演提示（可选）"
      content: "对白内容"
  - line_type: transition
    transition:
      type: "CUT_TO"
```

## 转换规则

1. **场景划分**：根据地点变化、时间跳跃、叙事节奏划分场景。每个场景应有明确的空间和时间。
2. **对白提取**：将小说中的对话转换为标准剧本对白格式。保留角色原话的语气和情感。
3. **动作描写**：将叙述性文字转化为简洁的动作/场景描写，去除心理独白等不适合影视呈现的内容。
4. **角色名**：统一使用角色的常用名或代号，保持一致性。
5. **表演提示**：根据上下文为对白添加必要的表演提示（如"低声"、"愤怒地"等）。
6. **转场**：在场景切换时添加适当的转场指示。
7. **场景标题行**：严格使用 "INT/EXT. 地点 - 时间" 的标准格式。

## 示例

输入小说片段：
```
李明推开了咖啡厅的门，冷风跟着灌了进来。王芳坐在角落的位置，面前的咖啡已经凉了。
"你来了。"王芳抬起头，眼神里带着一丝疲惫。
李明走过去坐下，"对不起，路上堵车了。"
```

输出：
```yaml
scene_number: 1
scene_heading: "INT. 咖啡厅 - DAY"
location: 咖啡厅
scene_type: INT
time_of_day: DAY
characters: [李明, 王芳]
summary: 李明来到咖啡厅与王芳见面
lines:
  - line_type: action
    action:
      content: "李明推开咖啡厅的门，冷风灌入。王芳坐在角落，面前的咖啡已经凉了。"
  - line_type: dialogue
    dialogue:
      character: "王芳"
      parenthetical: "抬起头，眼神疲惫"
      content: "你来了。"
  - line_type: action
    action:
      content: "李明走过去坐下。"
  - line_type: dialogue
    dialogue:
      character: "李明"
      parenthetical: "略带歉意"
      content: "对不起，路上堵车了。"
```"""


def build_chapter_convert_prompt(
    chapter_title: str,
    chapter_content: str,
    chapter_index: int,
    total_chapters: int,
    previous_context: str = ""
) -> str:
    """
    构建单章节转换的用户提示词

    Args:
        chapter_title: 章节标题
        chapter_content: 章节内容
        chapter_index: 当前章节序号
        total_chapters: 总章节数
        previous_context: 前一章的上下文摘要（用于保持连贯性）

    Returns:
        构建好的用户提示词
    """
    prompt_parts = []

    if previous_context:
        prompt_parts.append(f"## 前文摘要\n{previous_context}\n")

    prompt_parts.append(f"## 待转换内容\n这是小说的第 {chapter_index}/{total_chapters} 章。")
    prompt_parts.append(f"**章节标题**: {chapter_title}\n")
    prompt_parts.append(f"**章节正文**:\n{chapter_content}\n")
    prompt_parts.append("## 要求")
    prompt_parts.append("请将上述小说内容转换为YAML格式的剧本。")
    prompt_parts.append("直接输出YAML内容，不要包含```yaml标记或其他说明文字。")
    prompt_parts.append("确保scene_number从合适的数字开始编号。")

    return "\n".join(prompt_parts)


def build_context_summary_prompt(chapter_content: str, chapter_title: str) -> str:
    """构建提取章节上下文摘要的提示词"""
    return f"""请用2-3句话概括以下章节的核心内容，包括主要角色、关键事件和情感状态。
这将作为下一章转换时的上下文参考。

章节标题: {chapter_title}
章节内容:
{chapter_content}

请直接输出摘要，不要添加任何前缀或格式标记。"""


def build_metadata_prompt(chapters_content: str, novel_title: str = "") -> str:
    """构建提取剧本元数据的提示词"""
    return f"""请分析以下小说内容，提取剧本所需的元数据信息。

小说标题: {novel_title or "未知"}
小说前3000字:
{chapters_content[:3000]}

请以JSON格式输出以下信息（不要包含```json标记）：
{{
    "title": "剧本标题（如未提供则自行根据内容拟定）",
    "genre": "类型/题材（如：都市情感、古装武侠、悬疑推理等）",
    "characters": ["主要角色名列表，按重要性排序，最多10个"],
    "synopsis": "一句话故事梗概（50字以内）"
}}"""
