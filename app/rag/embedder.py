"""Embedding 编码器 - 支持批量编码"""
import requests
from app.config import settings


def embed(texts: list[str]) -> list[list[float]]:
    """
    将文本转换为向量
    
    Args:
        texts: 文本列表
        
    Returns:
        向量列表，每个向量是 float 数组
    """
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    
    # 硅基流动 Embedding API
    embedding_url = f"{settings.llm_base_url}/embeddings"
    
    payload = {
        "model": "BAAI/bge-large-zh-v1.5",  # 默认使用 BGE 模型
        "input": texts,
    }
    
    resp = requests.post(embedding_url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return [item["embedding"] for item in data["data"]]


def embed_single(text: str) -> list[float]:
    """编码单个文本"""
    return embed([text])[0]
