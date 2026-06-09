"""
FastAPI 路由定义
提供文件上传、转换、下载等API接口
"""

import os
import json
import yaml
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.models.models import ConvertRequest, Screenplay, Scene, Chapter
from backend.config import BUILTIN_MODELS, DEFAULT_MODEL, get_builtin_api_key
from backend.utils.file_utils import parse_uploaded_file
from backend.converter.llm_client import LLMClient
from backend.converter.screenplay_converter import ScreenplayConverter
from backend.schema.screenplay_schema import (
    screenplay_to_yaml,
    validate_screenplay_yaml,
    SCREENPLAY_YAML_SCHEMA
)

app = FastAPI(
    title="AI小说转剧本工具",
    description="将小说文本自动转换为结构化YAML剧本",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/")
async def root():
    """服务主页"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        from fastapi.responses import FileResponse
        return FileResponse(index_path)
    return {"message": "AI小说转剧本工具 API", "version": "1.0.0"}


@app.get("/api/models")
async def get_models():
    """获取内置模型列表"""
    models = []
    for key, cfg in BUILTIN_MODELS.items():
        builtin_key = get_builtin_api_key(key)
        models.append({
            "key": key,
            "name": cfg["name"],
            "description": cfg["description"],
            "api_base": cfg["api_base"],
            "model": cfg["model"],
            "need_key": cfg["need_key"],
            "tag": cfg["tag"],
            "has_builtin_key": bool(builtin_key),
            # 返回内置Key供前端自动填充（如果有的话）
            "builtin_key": builtin_key if builtin_key else "",
        })
    return {"default": DEFAULT_MODEL, "models": models}


@app.get("/api/schema")
async def get_schema():
    """获取YAML Schema定义"""
    return JSONResponse(content=SCREENPLAY_YAML_SCHEMA)


@app.post("/api/parse")
async def parse_novel(file: UploadFile = File(...)):
    """
    解析上传的小说文件

    - 支持 .txt 和 .docx 格式
    - 自动检测编码和章节结构
    - 返回章节统计信息
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".txt", ".docx"):
        raise HTTPException(status_code=400, detail="仅支持 .txt 和 .docx 格式")

    try:
        file_bytes = await file.read()
        novel_file = parse_uploaded_file(file_bytes, file.filename)

        if len(novel_file.chapters) < 1:
            raise HTTPException(status_code=400, detail="未能检测到有效章节，请检查文件内容")

        return {
            "success": True,
            "filename": novel_file.filename,
            "file_type": novel_file.file_type,
            "encoding": novel_file.encoding,
            "total_chars": novel_file.total_chars,
            "chapter_count": len(novel_file.chapters),
            "chapters": [
                {
                    "index": ch.index,
                    "title": ch.title,
                    "char_count": ch.char_count
                }
                for ch in novel_file.chapters
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")


@app.post("/api/convert")
async def convert_novel(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    api_base: str = Form("https://api.openai.com/v1"),
    model: str = Form("gpt-4o-mini"),
    novel_title: str = Form("")
):
    """
    完整转换流程：解析文件 + AI转换为剧本

    返回流式进度和最终结果
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    try:
        # 1. 解析文件
        file_bytes = await file.read()
        novel_file = parse_uploaded_file(file_bytes, file.filename)

        if len(novel_file.chapters) < 1:
            raise HTTPException(status_code=400, detail="未能检测到有效章节")

        if not novel_title:
            novel_title = os.path.splitext(file.filename)[0]

        # 2. 创建LLM客户端
        llm_client = LLMClient(api_key=api_key, api_base=api_base, model=model)

        # 3. 测试连接
        ok, msg = llm_client.test_connection()
        if not ok:
            raise HTTPException(status_code=400, detail=f"API连接失败: {msg}")

        # 4. 创建转换器
        converter = ScreenplayConverter(llm_client)

        # 5. 执行转换
        screenplay = converter.convert_novel(novel_file)

        # 6. 转为YAML
        yaml_output = screenplay_to_yaml(screenplay)

        return {
            "success": True,
            "metadata": screenplay.metadata.model_dump(),
            "scene_count": len(screenplay.scenes),
            "yaml": yaml_output,
            "screenplay": screenplay.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


@app.post("/api/convert/stream")
async def convert_novel_stream(
    file: UploadFile = File(...),
    api_key: str = Form(""),
    api_base: str = Form(""),
    model: str = Form(""),
    novel_title: str = Form(""),
    batch_size: int = Form(5),
    provider: str = Form("free_fast")
):
    """
    流式转换：批量处理，实时返回进度

    provider: 内置模型提供商key，如 free_fast / cheap / rule
    api_key/api_base/model: 用户自定义配置（优先级高于provider）

    batch_size: 每批合并的章节数（默认5），越大越快但单次token越多
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    async def event_generator():
        try:
            yield f"data: {json.dumps({'step': 'parsing', 'detail': '正在解析文件...'}, ensure_ascii=False)}\n\n"

            file_bytes = await file.read()
            novel_file = parse_uploaded_file(file_bytes, file.filename)

            if len(novel_file.chapters) < 1:
                yield f"data: {json.dumps({'step': 'error', 'detail': '未能检测到有效章节'}, ensure_ascii=False)}\n\n"
                return

            if not novel_title:
                novel_title_val = os.path.splitext(file.filename)[0]
            else:
                novel_title_val = novel_title

            chapter_count = len(novel_file.chapters)
            total_batches = (chapter_count + batch_size - 1) // batch_size

            yield f"data: {json.dumps({'step': 'parsed', 'detail': f'解析完成，共 {chapter_count} 章，{novel_file.total_chars} 字，将分 {total_batches} 批处理'}, ensure_ascii=False)}\n\n"

            # 根据provider自动填充配置
            cfg = BUILTIN_MODELS.get(provider, BUILTIN_MODELS[DEFAULT_MODEL])
            final_api_key = api_key or get_builtin_api_key(provider) or cfg["api_key"]
            final_api_base = api_base or cfg["api_base"]
            final_model = model or cfg["model"]

            if not final_api_key and provider not in ("ollama", "rule"):
                yield f"data: {json.dumps({'step': 'error', 'detail': f'该模型需要API Key，请填写或切换到免费模型'}, ensure_ascii=False)}\n\n"
                return

            yield f"data: {json.dumps({'step': 'metadata', 'detail': f'使用 {cfg["name"]} ({final_model})，批量 {batch_size} 章/批'}, ensure_ascii=False)}\n\n"

            # 创建LLM客户端和转换器
            llm_client = LLMClient(api_key=final_api_key, api_base=final_api_base, model=final_model)
            converter = ScreenplayConverter(llm_client, batch_size=batch_size)

            # 提取元数据
            yield f"data: {json.dumps({'step': 'metadata', 'detail': '正在提取元数据...'}, ensure_ascii=False)}\n\n"
            metadata = converter.extract_metadata(novel_file)
            metadata.title = novel_title_val

            # 批量转换
            all_scenes: list[Scene] = []
            scene_counter = 0

            batches: list[list[Chapter]] = []
            for i in range(0, chapter_count, batch_size):
                batches.append(novel_file.chapters[i:i + batch_size])

            for batch_idx, batch in enumerate(batches):
                ch_range = f"{batch[0].title} ~ {batch[-1].title}"
                yield f"data: {json.dumps({'step': 'converting', 'current': batch_idx+1, 'total': total_batches, 'detail': f'第 {batch_idx+1}/{total_batches} 批: {ch_range}'}, ensure_ascii=False)}\n\n"

                try:
                    scenes = converter.convert_batch(batch, batch_idx + 1, total_batches)

                    for scene in scenes:
                        scene_counter += 1
                        scene.scene_number = scene_counter

                    all_scenes.extend(scenes)

                    yield f"data: {json.dumps({'step': 'chapter_done', 'current': batch_idx+1, 'total': total_batches, 'detail': f'第 {batch_idx+1} 批完成，生成 {len(scenes)} 个场景'}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'step': 'chapter_done', 'current': batch_idx+1, 'total': total_batches, 'detail': f'第 {batch_idx+1} 批失败: {str(e)}，跳过'}, ensure_ascii=False)}\n\n"
                    continue

            # 构建最终结果
            metadata.total_scenes = len(all_scenes)
            all_characters = set()
            for scene in all_scenes:
                all_characters.update(scene.characters)
            if not metadata.characters:
                metadata.characters = sorted(list(all_characters))

            screenplay = Screenplay(metadata=metadata, scenes=all_scenes)
            yaml_output = screenplay_to_yaml(screenplay)

            yield f"data: {json.dumps({'step': 'done', 'yaml': yaml_output, 'scene_count': len(all_scenes), 'metadata': screenplay.metadata.model_dump()}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'detail': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/validate")
async def validate_yaml(yaml_content: str = Form(...)):
    """验证YAML内容是否符合剧本Schema"""
    is_valid, message = validate_screenplay_yaml(yaml_content)
    return {"valid": is_valid, "message": message}


@app.post("/api/convert/rule")
async def convert_novel_by_rule(
    file: UploadFile = File(...),
    novel_title: str = Form("")
):
    """
    规则引擎转换：不调用AI，使用正则规则转换

    完全免费、离线可用，效果有限但零成本
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    try:
        file_bytes = await file.read()
        novel_file = parse_uploaded_file(file_bytes, file.filename)

        if len(novel_file.chapters) < 1:
            raise HTTPException(status_code=400, detail="未能检测到有效章节")

        if not novel_title:
            novel_title = os.path.splitext(file.filename)[0]

        from backend.converter.rule_converter import convert_novel_by_rule
        screenplay = convert_novel_by_rule(novel_file, novel_title)
        yaml_output = screenplay_to_yaml(screenplay)

        return {
            "success": True,
            "metadata": screenplay.metadata.model_dump(),
            "scene_count": len(screenplay.scenes),
            "yaml": yaml_output,
            "screenplay": screenplay.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"规则转换失败: {str(e)}")


@app.post("/api/convert/batch")
async def convert_batch(
    novel_title: str = Form(""),
    chapters_json: str = Form("[]"),
    scene_start: int = Form(0)
):
    """
    批量规则转换：接收JSON格式的章节数据，返回YAML场景
    用于大文件客户端解析后分批发送，避免整个文件上传超时
    """
    try:
        chapters = json.loads(chapters_json)
        if not chapters:
            raise HTTPException(status_code=400, detail="没有章节数据")

        from backend.converter.rule_converter import convert_chapters_to_screenplay_yaml
        yaml_output = convert_chapters_to_screenplay_yaml(chapters, novel_title, scene_start)

        # 从YAML中提取实际出现的角色（只取对话中的角色名）
        import re as _re
        characters = set()
        for m in _re.finditer(r'character:\s*(.+)', yaml_output):
            name = m.group(1).strip()
            if name and len(name) >= 2:
                characters.add(name)

        return {
            "success": True,
            "yaml": yaml_output,
            "scene_count": yaml_output.count("scene_number:"),
            "characters": sorted(list(characters))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量转换失败: {str(e)}")
