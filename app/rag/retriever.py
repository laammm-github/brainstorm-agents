"""检索器 - 结合向量存储和重排序"""
import numpy as np
from app.rag.embedder import embed
from app.rag.store import VectorStore
from app.config import settings


class Retriever:
    """混合检索器 - 支持向量检索（用于个人知识库）"""
    
    def __init__(self, store: VectorStore = None):
        self.store = store or VectorStore()
    
    def add_documents(self, chunks: list[str], metadata: list[dict] = None):
        """
        添加文档到检索器
        
        Args:
            chunks: 文本块列表
            metadata: 元数据列表（可选）
        """
        # 批量编码
        embeddings = embed(chunks)
        
        # 添加到向量存储
        self.store.add_documents(chunks, embeddings, metadata)
    
    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float, dict]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回最相关的 K 个结果
            
        Returns:
            [(文本块, 相似度分数, 元数据), ...]
        """
        # 编码查询
        query_embedding = embed([query])[0]
        
        # 向量检索
        results = self.store.search(query_embedding, top_k)
        
        return results
    
    def search_with_rerank(self, query: str, top_k: int = 5) -> list[tuple[str, float, dict]]:
        """
        带重排序的检索（预留接口）
        
        TODO: 集成 BGE-Reranker 进行重排序
        当前直接返回向量检索结果
        """
        return self.search(query, top_k)
