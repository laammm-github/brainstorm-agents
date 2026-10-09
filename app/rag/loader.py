"""文档加载器 - 支持多种格式的文档加载"""
from pathlib import Path
from typing import List
from app.config import settings


class DocumentLoader:
    """文档加载器 - 支持 PDF、TXT、Markdown 格式（用于个人知识库）"""
    
    def __init__(self, documents_path: str = None):
        self.documents_path = Path(documents_path or settings.knowledge_base_path)
        
    def load_all(self) -> List[dict]:
        """
        加载所有文档
        
        Returns:
            文档列表，每个文档为 {"content": "...", "metadata": {...}}
        """
        if not self.documents_path.exists():
            print(f"警告：知识库目录不存在: {self.documents_path}")
            return []
        
        documents = []
        for file_path in self.documents_path.rglob("*"):
            if file_path.is_file():
                doc = self._load_single(file_path)
                if doc:
                    documents.append(doc)
        
        return documents
    
    def _load_single(self, file_path: Path) -> dict | None:
        """加载单个文档"""
        ext = file_path.suffix.lower()
        
        try:
            if ext == ".txt":
                content = self._load_txt(file_path)
            elif ext == ".md":
                content = self._load_txt(file_path)  # Markdown 也按文本处理
            elif ext == ".pdf":
                content = self._load_pdf(file_path)
            else:
                print(f"跳过不支持的文件格式: {file_path}")
                return None
            
            return {
                "content": content,
                "metadata": {
                    "source": str(file_path),
                    "filename": file_path.name,
                }
            }
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return None
    
    def _load_txt(self, file_path: Path) -> str:
        """加载 TXT/Markdown 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _load_pdf(self, file_path: Path) -> str:
        """加载 PDF 文件"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)
        except ImportError:
            print("警告：pypdf 未安装，无法加载 PDF 文件")
            print("请运行: pip install pypdf")
            return ""
