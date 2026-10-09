"""黄帽 Agent - 只说好处和可能性"""
from app.roles.base import ThinkingHat
from app.prompts.system_prompts import YELLOW_HAT_PROMPT


class YellowHat(ThinkingHat):
    """黄帽思考者 - 乐观积极"""
    
    def __init__(self):
        super().__init__(
            name="黄帽",
            color="yellow",
            system_prompt=YELLOW_HAT_PROMPT
        )
