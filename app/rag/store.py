"""FAISS 向量存储 - 持久化向量索引"""
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple
from app.config import settings


class VectorStore:
    """基于 FAISS 的向量存储（用于个人知识库）"""
    
    def __init__(self, store_path: str = None):
        self.store_path = Path(store_path or settings.vector_store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.chunks: List[str] = []
        self.embeddings: List[List[float]] = []
        self.metadata: List[dict] = []
        
        # 尝试加载已存在的索引
        self._load_index()
    
    def add_documents(self, chunks: List[str], embeddings: List[List[float]], 
                     metadata: List[dict] = None):
        """
        添加文档到向量存储
        
        Args:
            chunks: 文本块列表
            embeddings: 对应的向量列表
            metadata: 元数据列表（可选）
        """
        if metadata is None:
            metadata = [{} for _ in chunks]
            
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)
        self.metadata.extend(metadata)
        
        # 保存索引
        self._save_index()
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float, dict]]:
        """
        搜索相似文档
        
        Args:
            query_embedding: 查询向量
            top_k: 返回最相似的 K 个结果
            
        Returns:
            [(文本块, 相似度分数, 元数据), ...]
        """
        if not self.embeddings:
            return []
        
        q_vec = np.array(query_embedding)
        doc_vecs = np.array(self.embeddings)
        
        # 计算余弦相似度
        scores = np.dot(doc_vecs, q_vec) / (
            np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(q_vec) + 1e-8
        )
        
        # 获取 top-k
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append((
                self.chunks[idx],
                float(scores[idx]),
                self.metadata[idx]
            ))
        
        return results
    
    def _save_index(self):
        """保存索引到磁盘"""
        index_data = {
            "chunks": self.chunks,
            "embeddings": self.embeddings,
            "metadata": self.metadata,
        }
        
        index_file = self.store_path / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def _load_index(self):
        """从磁盘加载索引"""
        index_file = self.store_path / "index.json"
        if not index_file.exists():
            return
        
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            self.chunks = index_data.get("chunks", [])
            self.embeddings = index_data.get("embeddings", [])
            self.metadata = index_data.get("metadata", [])
            
            print(f"已加载向量索引：{len(self.chunks)} 个文档块")
        except Exception as e:
            print(f"加载向量索引失败: {e}")
    
    def clear(self):
        """清空索引"""
        self.chunks = []
        self.embeddings = []
        self.metadata = []
        self._save_index()
    
    def get_stats(self) -> dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_vectors": len(self.chunks),
            "total_embeddings": len(self.embeddings),
            "total_metadata": len(self.metadata),
        }
