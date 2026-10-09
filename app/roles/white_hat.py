"""白帽 Agent - 只陈述事实和数据"""
from app.roles.base import ThinkingHat
from app.prompts.system_prompts import WHITE_HAT_PROMPT


class WhiteHat(ThinkingHat):
    """白帽思考者 - 客观事实"""
    
    def __init__(self):
        super().__init__(
            name="白帽",
            color="white",
            system_prompt=WHITE_HAT_PROMPT
        )
