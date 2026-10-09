"""配置管理单元测试"""
import pytest
from app.config import settings


def test_settings_loads():
    """测试配置加载"""
    assert settings.llm_base_url is not None
    assert settings.max_debate_rounds == 2


def test_temperature_settings():
    """测试温度配置"""
    assert settings.agent_temperature > settings.coordinator_temperature
