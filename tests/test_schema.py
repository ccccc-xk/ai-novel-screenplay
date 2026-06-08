"""
YAML Schema 测试
"""

import pytest
import yaml
from backend.models.models import (
    Screenplay, ScreenplayMetadata, Scene, ScreenplayLine,
    ActionLine, DialogueLine, Transition
)
from backend.schema.screenplay_schema import (
    screenplay_to_yaml,
    yaml_to_screenplay,
    validate_screenplay_yaml
)


def make_sample_screenplay() -> Screenplay:
    """创建示例剧本"""
    metadata = ScreenplayMetadata(
        title="测试剧本",
        author="测试作者",
        genre="都市情感",
        characters=["张三", "李四"],
        synopsis="一个测试故事",
        total_scenes=1,
        source_chapters=1
    )

    scene = Scene(
        scene_number=1,
        scene_heading="INT. 咖啡厅 - DAY",
        location="咖啡厅",
        scene_type="INT",
        time_of_day="DAY",
        characters=["张三", "李四"],
        summary="张三和李四在咖啡厅见面",
        lines=[
            ScreenplayLine(
                line_type="action",
                action=ActionLine(content="张三推门走进咖啡厅。")
            ),
            ScreenplayLine(
                line_type="dialogue",
                dialogue=DialogueLine(
                    character="张三",
                    parenthetical="微笑",
                    content="你好，好久不见。"
                )
            ),
            ScreenplayLine(
                line_type="dialogue",
                dialogue=DialogueLine(
                    character="李四",
                    content="是啊，好久不见。"
                )
            )
        ]
    )

    return Screenplay(metadata=metadata, scenes=[scene])


class TestScreenplaySchema:
    """剧本Schema测试"""

    def test_create_screenplay(self):
        """测试创建剧本对象"""
        sp = make_sample_screenplay()
        assert sp.metadata.title == "测试剧本"
        assert len(sp.scenes) == 1
        assert sp.scenes[0].scene_number == 1

    def test_to_yaml(self):
        """测试转YAML"""
        sp = make_sample_screenplay()
        yaml_str = screenplay_to_yaml(sp)

        assert "title: 测试剧本" in yaml_str
        assert "INT. 咖啡厅 - DAY" in yaml_str
        assert "张三" in yaml_str

    def test_from_yaml(self):
        """测试从YAML解析"""
        sp = make_sample_screenplay()
        yaml_str = screenplay_to_yaml(sp)

        sp2 = yaml_to_screenplay(yaml_str)
        assert sp2.metadata.title == sp.metadata.title
        assert len(sp2.scenes) == len(sp.scenes)
        assert sp2.scenes[0].location == sp.scenes[0].location

    def test_validate_valid_yaml(self):
        """测试验证有效YAML"""
        sp = make_sample_screenplay()
        yaml_str = screenplay_to_yaml(sp)

        is_valid, msg = validate_screenplay_yaml(yaml_str)
        assert is_valid == True
        assert msg == "验证通过"

    def test_validate_invalid_yaml(self):
        """测试验证无效YAML"""
        is_valid, msg = validate_screenplay_yaml("这不是有效的YAML: [")
        assert is_valid == False

    def test_validate_missing_fields(self):
        """测试缺少必要字段"""
        is_valid, msg = validate_screenplay_yaml("title: 只有标题")
        assert is_valid == False
        assert "metadata" in msg or "scenes" in msg

    def test_roundtrip(self):
        """测试往返转换：对象→YAML→对象"""
        sp1 = make_sample_screenplay()
        yaml_str = screenplay_to_yaml(sp1)
        sp2 = yaml_to_screenplay(yaml_str)
        yaml_str2 = screenplay_to_yaml(sp2)

        # 再次解析确保稳定
        sp3 = yaml_to_screenplay(yaml_str2)
        assert sp3.metadata.title == sp1.metadata.title
        assert len(sp3.scenes) == len(sp1.scenes)
