"""应用配置管理 - 使用 Pydantic Settings 统一管理环境变量"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # LLM 配置
    llm_api_key: str
    llm_base_url: str = "https://api.siliconflow.cn/v1"
    llm_model_strong: str = "Qwen/Qwen2.5-7B-Instruct"  # 协调者用强模型
    llm_model_fast: str = "Qwen/Qwen2.5-7B-Instruct"    # 角色 Agent 用快模型
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    llm_timeout: int = 120  # LLM 请求超时时间（秒）
    
    # Agent 配置
    max_debate_rounds: int = 2  # 最大辩论轮次
    agent_temperature: float = 0.8  # 角色 Agent 更高温度以增加多样性
    coordinator_temperature: float = 0.5  # 协调者较低温度以保持理性
    enable_parallel_execution: bool = True  # 启用并行执行角色思考
    
    # RAG 配置（个人知识库）
    chunk_size: int = 500
    chunk_overlap: int = 50
    vector_store_path: str = "./data/vector_store"
    knowledge_base_path: str = "./knowledge_base"
    
    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8001  # 与 investment-agent 区分
    api_debug: bool = True
    
    # 成本控制
    enable_cost_control: bool = True
    max_tokens_per_session: int = 50000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()
