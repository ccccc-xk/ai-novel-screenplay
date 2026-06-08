"""
YAML Schema 定义与验证
定义剧本的YAML结构规范，并提供验证功能
"""

import yaml
from datetime import datetime
from backend.models.models import (
    Screenplay, ScreenplayMetadata, Scene, ScreenplayLine,
    ActionLine, DialogueLine, Transition, SceneType, TimeOfDay
)


# YAML Schema 定义（用于文档生成和前端展示）
SCREENPLAY_YAML_SCHEMA = {
    "type": "object",
    "required": ["metadata", "scenes"],
    "properties": {
        "metadata": {
            "type": "object",
            "description": "剧本元数据",
            "required": ["title"],
            "properties": {
                "title": {"type": "string", "description": "剧本标题"},
                "author": {"type": "string", "description": "原作者"},
                "adapter": {"type": "string", "description": "改编者"},
                "genre": {"type": "string", "description": "类型/题材"},
                "version": {"type": "string", "description": "版本号"},
                "created_at": {"type": "string", "description": "创建时间 (ISO 8601)"},
                "source_chapters": {"type": "integer", "description": "来源章节数"},
                "total_scenes": {"type": "integer", "description": "总场景数"},
                "characters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "主要角色列表"
                },
                "synopsis": {"type": "string", "description": "故事梗概"}
            }
        },
        "scenes": {
            "type": "array",
            "description": "场景列表",
            "items": {
                "type": "object",
                "required": ["scene_number", "scene_heading", "location", "lines"],
                "properties": {
                    "scene_number": {"type": "integer", "description": "场景编号"},
                    "scene_heading": {"type": "string", "description": "场景标题行"},
                    "location": {"type": "string", "description": "地点"},
                    "scene_type": {
                        "type": "string",
                        "enum": ["INT", "EXT", "INT/EXT"],
                        "description": "内景/外景"
                    },
                    "time_of_day": {
                        "type": "string",
                        "enum": ["DAY", "NIGHT", "MORNING", "EVENING", "DAWN", "DUSK", "UNKNOWN"],
                        "description": "时间"
                    },
                    "characters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "出场角色列表"
                    },
                    "summary": {"type": "string", "description": "场景摘要"},
                    "lines": {
                        "type": "array",
                        "description": "场景内容行列表",
                        "items": {
                            "type": "object",
                            "required": ["line_type"],
                            "properties": {
                                "line_type": {
                                    "type": "string",
                                    "enum": ["scene_heading", "action", "dialogue", "transition"],
                                    "description": "行类型"
                                },
                                "action": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string", "default": "action"},
                                        "content": {"type": "string", "description": "动作/描写内容"},
                                        "character": {"type": "string", "description": "相关角色"}
                                    }
                                },
                                "dialogue": {
                                    "type": "object",
                                    "properties": {
                                        "character": {"type": "string", "description": "角色名"},
                                        "parenthetical": {"type": "string", "description": "表演提示"},
                                        "content": {"type": "string", "description": "对白内容"}
                                    }
                                },
                                "transition": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string", "description": "转场类型"},
                                        "target": {"type": "string", "description": "转场目标"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def screenplay_to_yaml(screenplay: Screenplay) -> str:
    """将剧本对象转换为YAML字符串"""
    data = screenplay.model_dump(mode="json", exclude_none=True)
    return yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
        indent=2
    )


def yaml_to_screenplay(yaml_str: str) -> Screenplay:
    """将YAML字符串解析为剧本对象"""
    data = yaml.safe_load(yaml_str)
    return Screenplay(**data)


def validate_screenplay_yaml(yaml_str: str) -> tuple[bool, str]:
    """
    验证YAML字符串是否符合剧本Schema
    返回: (是否有效, 错误信息)
    """
    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            return False, "YAML根节点必须是对象"
        if "metadata" not in data:
            return False, "缺少 metadata 字段"
        if "scenes" not in data:
            return False, "缺少 scenes 字段"
        if not isinstance(data["scenes"], list):
            return False, "scenes 必须是数组"
        # 尝试解析为完整模型
        Screenplay(**data)
        return True, "验证通过"
    except yaml.YAMLError as e:
        return False, f"YAML解析错误: {str(e)}"
    except Exception as e:
        return False, f"数据验证错误: {str(e)}"


def get_schema_markdown() -> str:
    """生成Schema的Markdown文档（供前端展示）"""
    return yaml.dump(
        SCREENPLAY_YAML_SCHEMA,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False
    )
