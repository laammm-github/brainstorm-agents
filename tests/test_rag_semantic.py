"""RAG 系统测试 - 验证所有 RAG 操作的输出语义"""
import pytest
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tools.rag_tool import rag_tool
from app.rag.loader import DocumentLoader
from app.rag.chunker import chunk_text


class TestRAGSearch:
    """测试知识库检索功能"""
    
    def test_search_empty_knowledge_base(self):
        """测试空知识库检索的语义"""
        # 执行检索
        result = rag_tool.search_knowledge_base("AI Agent 开发", top_k=3)
        
        # 验证语义
        assert result is not None, "检索结果不应为 None"
        assert isinstance(result, str), "检索结果应为字符串"
        
        # 空知识库应返回友好提示
        assert "未找到" in result or "空" in result or "检索失败" in result, \
            f"空知识库应返回提示，实际: {result[:100]}"
        
        print(f"✅ 空知识库检索语义正确: {result}")
    
    def test_search_result_format(self):
        """测试检索结果格式化语义"""
        # 先添加测试文档
        test_doc = Path("knowledge_base/test_search.md")
        test_doc.parent.mkdir(parents=True, exist_ok=True)
        test_doc.write_text("AI Agent 开发是未来趋势，需要掌握 Python、LLM 和 Multi-Agent 系统", encoding="utf-8")
        
        try:
            # 添加文档
            add_result = rag_tool.add_document(str(test_doc))
            assert "成功" in add_result, f"添加文档应成功，实际: {add_result}"
            
            # 执行检索
            result = rag_tool.search_knowledge_base("AI Agent", top_k=3)
            
            # 验证格式化语义
            if "未找到" not in result:
                # 应包含序号
                assert "[1]" in result, "检索结果应包含序号 [1]"
                # 应包含来源信息
                assert "来源" in result, "检索结果应包含来源信息"
                # 应包含相似度
                assert "相似度" in result, "检索结果应包含相似度"
                
                print(f"✅ 检索结果格式化正确:\n{result[:200]}")
        finally:
            # 清理测试文件
            if test_doc.exists():
                test_doc.unlink()


class TestRAGAddDocument:
    """测试添加文档功能"""
    
    def test_add_markdown_document(self):
        """测试添加 Markdown 文档的语义"""
        # 创建测试文档
        test_doc = Path("knowledge_base/test_add.md")
        test_doc.parent.mkdir(parents=True, exist_ok=True)
        test_content = "# 测试文档\n\n这是用于测试添加功能的文档内容。"
        test_doc.write_text(test_content, encoding="utf-8")
        
        try:
            # 执行添加
            result = rag_tool.add_document(str(test_doc))
            
            # 验证语义
            assert result is not None, "添加结果不应为 None"
            assert isinstance(result, str), "添加结果应为字符串"
            
            # 成功情况
            if "成功" in result:
                assert "测试_add.md" in result or "共" in result, \
                    f"成功信息应包含文件名或文档块数量，实际: {result}"
                assert "文档块" in result, "成功信息应包含文档块数量"
            
            # 失败情况
            elif "失败" in result:
                assert "添加失败" in result, "失败信息应明确说明"
            
            print(f"✅ 添加文档语义正确: {result}")
        finally:
            if test_doc.exists():
                test_doc.unlink()
    
    def test_add_nonexistent_file(self):
        """测试添加不存在文件的错误语义"""
        result = rag_tool.add_document("nonexistent_file.md")
        
        # 验证错误语义
        assert "不存在" in result or "失败" in result, \
            f"应返回文件不存在错误，实际: {result}"
        
        print(f"✅ 文件不存在错误语义正确: {result}")
    
    def test_add_unsupported_format(self):
        """测试添加不支持格式的错误语义"""
        # 创建不支持的文件格式
        test_doc = Path("knowledge_base/test.exe")
        test_doc.parent.mkdir(parents=True, exist_ok=True)
        test_doc.write_bytes(b"binary content")
        
        try:
            result = rag_tool.add_document(str(test_doc))
            
            # 应返回失败或跳过信息
            assert "失败" in result or "加载文档失败" in result, \
                f"不支持格式应返回失败信息，实际: {result}"
            
            print(f"✅ 不支持格式错误语义正确: {result}")
        finally:
            if test_doc.exists():
                test_doc.unlink()


class TestRAGListDocuments:
    """测试列出文档功能"""
    
    def test_list_documents_format(self):
        """测试列出文档的格式化语义"""
        result = rag_tool.list_documents()
        
        # 验证语义
        assert result is not None, "列出结果不应为 None"
        assert isinstance(result, str), "列出结果应为字符串"
        
        # 可能的情况
        if "不存在" in result:
            assert "知识库目录不存在" in result, \
                f"目录不存在应明确说明，实际: {result}"
        elif "为空" in result:
            assert "知识库为空" in result, \
                f"知识库为空应明确说明，实际: {result}"
        else:
            # 有文档时应包含列表信息
            assert "文档列表" in result or "." in result, \
                f"应包含文档列表信息，实际: {result[:100]}"
        
        print(f"✅ 列出文档语义正确: {result[:150]}")


class TestRAGStats:
    """测试统计信息功能"""
    
    def test_get_stats_format(self):
        """测试统计信息的格式化语义"""
        result = rag_tool.get_stats()
        
        # 验证语义
        assert result is not None, "统计结果不应为 None"
        assert isinstance(result, str), "统计结果应为字符串"
        
        # 应包含关键统计信息
        if "不存在" not in result:
            assert "统计信息" in result, "应包含'统计信息'标题"
            assert "文档数量" in result, "应包含文档数量"
            assert "向量数量" in result or "向量" in result, "应包含向量数量"
        
        print(f"✅ 统计信息语义正确: {result}")


class TestRAGChunker:
    """测试文本分块功能"""
    
    def test_chunk_text_semantic(self):
        """测试文本分块的语义完整性"""
        text = "这是一段测试文本。" * 100  # 重复 100 次
        
        # 执行分块
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        
        # 验证语义
        assert len(chunks) > 0, "分块结果不应为空"
        assert all(isinstance(chunk, str) for chunk in chunks), "所有分块应为字符串"
        
        # 验证重叠语义
        if len(chunks) > 1:
            # 相邻块应有重叠
            for i in range(len(chunks) - 1):
                overlap_content = chunks[i][-10:]  # 前一块的末尾
                assert overlap_content in chunks[i+1], \
                    f"相邻块应有重叠，但第 {i} 块末尾不在第 {i+1} 块中"
        
        # 验证完整性
        # 所有块拼接应覆盖原文（考虑重叠会重复）
        total_length = sum(len(c) for c in chunks)
        assert total_length >= len(text), "分块总长度应 >= 原文长度"
        
        print(f"✅ 文本分块语义正确: {len(chunks)} 个块")


class TestRAGEdgeCases:
    """测试边界情况和异常处理"""
    
    def test_search_empty_query(self):
        """测试空查询的语义处理"""
        result = rag_tool.search_knowledge_base("", top_k=3)
        
        # 应返回有意义的提示
        assert result is not None, "空查询应返回结果"
        assert "未找到" in result or "失败" in result or "空" in result, \
            f"空查询应返回提示，实际: {result[:100]}"
        
        print(f"✅ 空查询语义正确: {result[:100]}")
    
    def test_search_large_top_k(self):
        """测试大 top_k 值的语义处理"""
        result = rag_tool.search_knowledge_base("test", top_k=100)
        
        # 应正常处理或给出提示
        assert result is not None, "大 top_k 应返回结果"
        assert isinstance(result, str), "结果应为字符串"
        
        print(f"✅ 大 top_k 语义正确: {result[:100]}")
    
    def test_add_empty_file(self):
        """测试添加空文件的语义"""
        test_doc = Path("knowledge_base/empty.md")
        test_doc.parent.mkdir(parents=True, exist_ok=True)
        test_doc.write_text("", encoding="utf-8")
        
        try:
            result = rag_tool.add_document(str(test_doc))
            
            # 应成功或给出提示
            assert result is not None, "空文件应返回结果"
            assert "成功" in result or "失败" in result, \
                f"应明确说明成功或失败，实际: {result}"
            
            print(f"✅ 空文件语义正确: {result}")
        finally:
            if test_doc.exists():
                test_doc.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
