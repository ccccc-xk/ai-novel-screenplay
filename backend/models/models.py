"""
数据模型定义
定义小说解析和剧本转换中使用的所有数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class SceneType(str, Enum):
    """场景类型枚举"""
    INTERIOR = "INT"    # 内景
    EXTERIOR = "EXT"    # 外景
    INT_EXT = "INT/EXT" # 内外景


class TimeOfDay(str, Enum):
    """时间枚举"""
    DAY = "DAY"
    NIGHT = "NIGHT"
    MORNING = "MORNING"
    EVENING = "EVENING"
    DAWN = "DAWN"
    DUSK = "DUSK"
    UNKNOWN = "UNKNOWN"


class Chapter(BaseModel):
    """小说章节模型"""
    index: int = Field(..., description="章节序号，从1开始")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节正文内容")
    char_count: int = Field(0, description="字符数")


class NovelFile(BaseModel):
    """上传的小说文件模型"""
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型: txt / docx")
    encoding: str = Field("utf-8", description="文件编码")
    chapters: list[Chapter] = Field(default_factory=list, description="解析后的章节列表")
    total_chars: int = Field(0, description="总字符数")


class ActionLine(BaseModel):
    """动作/描写行"""
    type: str = Field("action", description="行类型: action / description")
    content: str = Field(..., description="动作或描写内容")
    character: Optional[str] = Field(None, description="相关角色名")


class DialogueLine(BaseModel):
    """对白行"""
    character: str = Field(..., description="角色名")
    parenthetical: Optional[str] = Field(None, description="表演提示，如 (低声地)")
    content: str = Field(..., description="对白内容")


class Transition(BaseModel):
    """转场指示"""
    type: str = Field(..., description="转场类型: CUT_TO / FADE_IN / FADE_OUT / DISSOLVE")
    target: Optional[str] = Field(None, description="转场目标描述")


class ScreenplayLine(BaseModel):
    """剧本中的一行内容（多态类型）"""
    line_type: str = Field(..., description="行类型: action / dialogue / transition / scene_heading")
    action: Optional[ActionLine] = None
    dialogue: Optional[DialogueLine] = None
    transition: Optional[Transition] = None
    scene_heading: Optional[str] = None


class Scene(BaseModel):
    """场景模型"""
    scene_number: int = Field(..., description="场景编号")
    scene_heading: str = Field(..., description="场景标题行，如: INT. 咖啡厅 - DAY")
    location: str = Field(..., description="地点")
    scene_type: SceneType = Field(SceneType.INTERIOR, description="内景/外景")
    time_of_day: TimeOfDay = Field(TimeOfDay.DAY, description="时间")
    characters: list[str] = Field(default_factory=list, description="出场角色列表")
    lines: list[ScreenplayLine] = Field(default_factory=list, description="场景内容行")
    summary: Optional[str] = Field(None, description="场景摘要")


class ScreenplayMetadata(BaseModel):
    """剧本元数据"""
    title: str = Field(..., description="剧本标题")
    author: str = Field("", description="原作者")
    adapter: str = Field("", description="改编者")
    genre: str = Field("", description="类型/题材")
    version: str = Field("1.0", description="版本号")
    created_at: str = Field("", description="创建时间")
    source_chapters: int = Field(0, description="来源章节数")
    total_scenes: int = Field(0, description="总场景数")
    characters: list[str] = Field(default_factory=list, description="主要角色列表")
    synopsis: str = Field("", description="故事梗概")


class Screenplay(BaseModel):
    """完整剧本模型"""
    metadata: ScreenplayMetadata = Field(..., description="剧本元数据")
    scenes: list[Scene] = Field(default_factory=list, description="场景列表")


class ConvertRequest(BaseModel):
    """转换请求模型"""
    api_key: str = Field(..., description="API Key")
    api_base: str = Field("https://api.openai.com/v1", description="API Base URL")
    model: str = Field("gpt-4o-mini", description="模型名称")
    novel_title: str = Field("", description="小说标题")
