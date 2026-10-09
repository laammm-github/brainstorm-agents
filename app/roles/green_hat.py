"""绿帽 Agent - 只提创意和替代方案"""
from app.roles.base import ThinkingHat
from app.prompts.system_prompts import GREEN_HAT_PROMPT


class GreenHat(ThinkingHat):
    """绿帽思考者 - 创新思维"""
    
    def __init__(self):
        super().__init__(
            name="绿帽",
            color="green",
            system_prompt=GREEN_HAT_PROMPT
        )
