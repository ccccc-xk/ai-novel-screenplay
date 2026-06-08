"""内置模型提供商配置"""
import os

# 内置模型提供商（按推荐顺序排列）
BUILTIN_MODELS = {
    "rule": {
        "name": "规则引擎（离线免费）",
        "api_base": "",
        "model": "rule-engine",
        "api_key": "",
        "need_key": False,
        "description": "不需要任何API Key，纯规则转换，一键使用",
        "tag": "免费·推荐"
    },
    "free_fast": {
        "name": "Groq 免费",
        "api_base": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "api_key": "",
        "need_key": True,
        "description": "免费70B大模型，需注册获取API Key",
        "tag": "免费"
    },
    "free_cn": {
        "name": "硅基流动",
        "api_base": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "api_key": "",
        "need_key": True,
        "description": "国内平台，新用户送14元余额",
        "tag": "免费额度"
    },
    "cheap": {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": "",
        "need_key": True,
        "description": "注册送500万token，效果好",
        "tag": "极便宜"
    },
    "ollama": {
        "name": "Ollama 本地",
        "api_base": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "api_key": "ollama",
        "need_key": False,
        "description": "本地运行，需安装Ollama+下载模型",
        "tag": "本地免费"
    },
    "openai": {
        "name": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "api_key": "",
        "need_key": True,
        "description": "付费API，效果最好",
        "tag": "付费"
    }
}

# 默认使用规则引擎（真正免费，无需Key）
DEFAULT_MODEL = "rule"


def get_builtin_api_key(provider: str) -> str:
    """获取内置API Key（从环境变量读取，支持部署时注入）"""
    model = BUILTIN_MODELS.get(provider, {})
    env_key = os.environ.get(f"{provider.upper()}_API_KEY", "")
    return env_key or model.get("api_key", "")
