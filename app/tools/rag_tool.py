"""RAG 工具逻辑 - 知识库管理"""
from pathlib import Path
from app.rag.retriever import Retriever
from app.rag.loader import DocumentLoader
from app.rag.chunker import chunk_text
from app.config import settings


class RAGTool:
    """RAG 知识库工具"""
    
    def __init__(self):
        self.retriever = Retriever()
    
    def search_knowledge_base(self, query: str, top_k: int = 3) -> str:
        """
        检索知识库
        
        Args:
            query: 检索关键词
            top_k: 返回结果数量
        
        Returns:
            格式化的检索结果
        """
        try:
            results = self.retriever.search(query, top_k=top_k)
            
            if not results:
                return "知识库中未找到相关内容"
            
            # 格式化结果
            formatted = []
            for i, (text, score, metadata) in enumerate(results, 1):
                source = metadata.get("filename", "未知来源")
                formatted.append(
                    f"[{i}] {text}\n    来源：{source}\n    相似度：{score:.2%}"
                )
            
            return "\n\n".join(formatted)
        
        except Exception as e:
            # 确保错误信息是 ASCII 安全的字符串
            error_msg = str(e)
            # 如果是 HTTP 错误，提取关键信息
            if "404" in error_msg or "Not Found" in error_msg:
                return "知识库搜索服务暂时不可用（ embeddings API 未配置）"
            return f"检索失败：{error_msg}"
    
    def add_document(self, file_path: str) -> str:
        """
        添加文档到知识库
        
        Args:
            file_path: 文档文件路径
        
        Returns:
            操作结果
        """
        try:
            # 检查文件是否存在
            path = Path(file_path)
            if not path.exists():
                return f"文件不存在：{file_path}"
            
            # 加载文档
            loader = DocumentLoader()
            doc = loader._load_single(path)
            
            if not doc:
                return f"加载文档失败：{file_path}"
            
            # 分块
            chunks = chunk_text(doc["content"], chunk_size=500, overlap=50)
            
            # 添加到检索器
            self.retriever.add_documents(
                chunks, 
                metadata=[{"source": str(path), "filename": path.name}] * len(chunks)
            )
            
            return f"成功添加文档：{path.name}，共 {len(chunks)} 个文档块"
        
        except Exception as e:
            error_msg = str(e)
            return f"添加失败：{error_msg}"
    
    def list_documents(self) -> str:
        """
        列出所有文档
        
        Returns:
            文档列表
        """
        try:
            kb_path = Path(settings.knowledge_base_path)
            
            if not kb_path.exists():
                return "知识库目录不存在"
            
            documents = list(kb_path.rglob("*"))
            documents = [d for d in documents if d.is_file()]
            
            if not documents:
                return "知识库为空"
            
            formatted = ["知识库文档列表：\n"]
            for i, doc in enumerate(documents, 1):
                formatted.append(f"{i}. {doc.name} ({doc.suffix})")
            
            return "\n".join(formatted)
        
        except Exception as e:
            error_msg = str(e)
            return f"列出文档失败：{error_msg}"
    
    def get_stats(self) -> str:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        try:
            kb_path = Path(settings.knowledge_base_path)
            
            if not kb_path.exists():
                return "知识库目录不存在"
            
            # 统计文件数量
            documents = list(kb_path.rglob("*"))
            documents = [d for d in documents if d.is_file()]
            
            # 统计向量存储
            stats = self.retriever.store.get_stats()
            
            formatted = [
                "知识库统计信息：",
                f"- 文档数量：{len(documents)}",
                f"- 向量数量：{stats.get('total_vectors', 0)}",
                f"- 知识库路径：{kb_path}"
            ]
            
            return "\n".join(formatted)
        
        except Exception as e:
            error_msg = str(e)
            return f"获取统计信息失败：{error_msg}"


# 全局实例
rag_tool = RAGTool()
