"""LLM 适配器 - 支持多模型路由（强模型/快模型）"""
import requests
from app.config import settings


def chat(messages: list[dict], use_strong_model: bool = True, **kwargs) -> str:
    """
    调用 LLM API 进行对话
    
    Args:
        messages: 对话消息列表
        use_strong_model: 是否使用强模型（True=协调者，False=角色Agent）
        **kwargs: 可选参数
        
    Returns:
        LLM 返回的文本内容
    """
    # 根据场景选择模型
    model = settings.llm_model_strong if use_strong_model else settings.llm_model_fast
    temperature = kwargs.get("temperature", 
                           settings.coordinator_temperature if use_strong_model 
                           else settings.agent_temperature)
    
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": kwargs.get("max_tokens", settings.llm_max_tokens),
    }
    
    resp = requests.post(
        f"{settings.llm_base_url}/chat/completions", 
        json=payload, 
        headers=headers
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
