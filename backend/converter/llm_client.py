"""
大模型API客户端
封装OpenAI兼容接口，支持多种模型和API提供商
"""

import json
from openai import OpenAI


class LLMClient:
    """大模型API客户端"""

    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> str:
        """
        发送对话请求

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户消息
            temperature: 温度参数，越低越确定性
            max_tokens: 最大输出token数

        Returns:
            模型回复文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def chat_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ):
        """
        流式对话请求

        Yields:
            模型回复的文本片段
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def test_connection(self) -> tuple[bool, str]:
        """测试API连接是否正常"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True, f"连接成功，使用模型: {self.model}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
