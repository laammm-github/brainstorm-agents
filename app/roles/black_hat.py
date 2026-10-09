"""黑帽 Agent - 只挑毛病和风险"""
from app.roles.base import ThinkingHat
from app.prompts.system_prompts import BLACK_HAT_PROMPT


class BlackHat(ThinkingHat):
    """黑帽思考者 - 批判风险"""
    
    def __init__(self):
        super().__init__(
            name="黑帽",
            color="black",
            system_prompt=BLACK_HAT_PROMPT
        )
