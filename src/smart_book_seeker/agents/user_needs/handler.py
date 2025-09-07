import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from smart_book_seeker.log_config import get_logger
from smart_book_seeker.models import UserNeedsAgentState
load_dotenv()

logger = get_logger(__name__)

class UserNeedsAgent:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "prompts", "general.txt")) as f:
            self.system_prompt = f.read()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.state = UserNeedsAgentState.IDLE
        logger.info(f"User Needs Agent 初始化完成")

    def respond(self, messages: list) -> str:
        if self.state == UserNeedsAgentState.IDLE:
            self.state = UserNeedsAgentState.COLLECT
            logger.info(f"User Needs Agent 的狀態切換為 COLLECT")
        response = self.client.responses.create(
            input=messages,
            instructions=self.system_prompt,
            model="gpt-4o-mini",
            temperature=0.2,
            top_p=0.9
        )
        logger.info(f"User Needs Agent 回應：{response.output_text}")
        if "[總結]" in response.output_text:
            self.state = UserNeedsAgentState.IDLE
            logger.info(f"User Needs Agent 的狀態切換為 IDLE")
        return response.output_text

    @staticmethod
    def parse_response(response: str) -> str:
        if "[詢問]" in response:
            return re.search(r'\[詢問] (.*)', response).group(1)
        return re.search(r'\[總結] (.*)', response).group(1)
