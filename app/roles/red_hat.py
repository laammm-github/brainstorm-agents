"""红帽 Agent - 只表达感受和直觉"""
from app.roles.base import ThinkingHat
from app.prompts.system_prompts import RED_HAT_PROMPT


class RedHat(ThinkingHat):
    """红帽思考者 - 情感直觉"""
    
    def __init__(self):
        super().__init__(
            name="红帽",
            color="red",
            system_prompt=RED_HAT_PROMPT
        )
