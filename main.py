"""
AI小说转剧本工具 - 主入口
启动FastAPI服务器
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
