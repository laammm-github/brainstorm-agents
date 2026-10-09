"""文本分块器 - 支持固定长度和语义切分"""
from app.config import settings


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    按固定长度分块
    
    Args:
        text: 待分块的文本
        chunk_size: 每块大小（字符数），默认使用配置值
        overlap: 重叠大小（字符数），默认使用配置值
        
    Returns:
        分块后的文本列表
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def chunk_by_paragraphs(text: str, max_chunk_size: int = None) -> list[str]:
    """
    按段落分块（更自然的切分方式）
    
    Args:
        text: 待分块的文本
        max_chunk_size: 最大块大小，默认使用配置值
        
    Returns:
        分块后的文本列表
    """
    if max_chunk_size is None:
        max_chunk_size = settings.chunk_size
        
    # 按段落分割
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
