"""紫帽 Agent - 只看全局和长期影响"""
from app.roles.base import ThinkingHat
from app.prompts.system_prompts import PURPLE_HAT_PROMPT


class PurpleHat(ThinkingHat):
    """紫帽思考者 - 全局视角"""
    
    def __init__(self):
        super().__init__(
            name="紫帽",
            color="purple",
            system_prompt=PURPLE_HAT_PROMPT
        )
