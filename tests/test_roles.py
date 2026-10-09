"""角色 Agent 单元测试"""
import pytest
from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat


def test_white_hat_initialization():
    """测试白帽初始化"""
    hat = WhiteHat()
    assert hat.name == "白帽"
    assert hat.color == "white"
    assert "事实" in hat.system_prompt


def test_red_hat_initialization():
    """测试红帽初始化"""
    hat = RedHat()
    assert hat.name == "红帽"
    assert hat.color == "red"
    assert "感受" in hat.system_prompt
