import os
import json
import random
import string
from typing import Literal, cast
from openai import OpenAI
from dotenv import load_dotenv
from openai.types.responses import ToolChoiceFunctionParam
from smart_book_seeker.log_config import get_logger
from smart_book_seeker.models import LibrarianAgentState, LibrarianAgentEnvironment, BookSearchHistory, Book
from smart_book_seeker.agents.librarian.tools import *
load_dotenv()

logger = get_logger(__name__)

class LibrarianAgent:
    def __init__(self, book_search_needs: str, strategy: Literal["keyword_query", "boolean_query", "iterative_top_k"]):
        with open(os.path.join(os.path.dirname(__file__), "prompts", f"{strategy}.txt")) as f:
            self.system_prompt = f.read()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.state = LibrarianAgentState.IDLE
        self.messages = []
        self.environment = LibrarianAgentEnvironment(
            initial_book_search_needs=book_search_needs,
            book_search_needs=book_search_needs,
            current_turn=0,
            book_search_count=0,
            book_search_history=[],
            book_selection_history=[],
            user_suggestion_history=[],
            user_current_books=[]
        )
        self.tools = self._load_tools()

        if strategy == "keyword_query":
            self.respond = self._keyword_query_respond
        elif strategy == "boolean_query":
            self.respond = self._boolean_query_respond
        elif strategy == "iterative_top_k":
            self.respond = self._iterative_top_k_respond

        logger.info("Librarian Agent 初始化完成")

    @staticmethod
    def _load_tools():
        definition_dir = os.path.join(os.path.dirname(__file__), "tools", "definitions")
        tools = {}
        for filename in os.listdir(definition_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(definition_dir, filename)
                with open(filepath, encoding="utf-8") as fp:
                    tools[filename[:-5]] = json.load(fp)
        return tools

    def _call_function(self, name, args):
        if name == "prepare_environment_snapshot":
            return prepare_environment_snapshot(**args)
        if name == "infer_book_search_needs":
            return infer_book_search_needs(**args)
        if name == "generate_rationale":
            return generate_rationale(**args)
        if name == "ask_end_of_session":
            self.state = LibrarianAgentState.ASK_TO_CLOSE
            return ask_end_of_session(**args)
        if name == "clarify_book_request":
            self.state = LibrarianAgentState.ASK
            return clarify_book_request(**args)
        if name == "search_library_catalog":
            self.state = LibrarianAgentState.SEARCH
            args["current_turn"] = self.environment.current_turn
            return search_library_catalog(**args)
        return None

    @staticmethod
    def _generate_fake_id(prefix: str, length: int) -> str:
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=length - len(prefix)))
        return f"{prefix}{random_part}"

    @staticmethod
    def _keyword_query_respond(self) -> str:
        return "placeholder_response"

    @staticmethod
    def _boolean_query_respond(self) -> str:
        return "placeholder_response"

    def _iterative_top_k_respond(self, message: str):
        self.messages.append({"role": "user", "content": message})
        # Prepare Environment Snapshot
        fake_call_id = self._generate_fake_id("call_environment_", 29)
        args = self.environment.to_dict()
        self.messages.append({
            "type": "function_call",
            "call_id": fake_call_id,
            "name": "prepare_environment_snapshot",
            "arguments": json.dumps(args, ensure_ascii=False)
        })
        self.messages.append({
            "type": "function_call_output",
            "call_id": fake_call_id,
            "output": self._call_function("prepare_environment_snapshot", args)
        })
        # Infer Book Search Needs
        response = self.client.responses.create(
            input=self.messages,
            instructions=self.system_prompt,
            model="gpt-4.1-mini",
            temperature=0.4,
            top_p=0.9,
            tools=[
                self.tools["prepare_environment_snapshot"],
                self.tools["infer_book_search_needs"]
            ],
            tool_choice=cast(
                ToolChoiceFunctionParam,
                {"type": "function", "name": "infer_book_search_needs"}
            )
        )
        tool_call = response.output[0]
        args = json.loads(tool_call.arguments)
        self.messages.append({
            "type": "function_call",
            "id": tool_call.id,
            "call_id": tool_call.call_id,
            "name": tool_call.name,
            "arguments": json.dumps(args, ensure_ascii=False)
        })
        tool_call_output = self._call_function(tool_call.name, args)
        self.messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": tool_call_output
        })
        # Infer Book Search Needs [Update Environment]
        self.environment.book_search_needs = json.loads(tool_call_output)["value"]["book_search_needs"]
        # Generate Rationale
        available_tools = [
            self.tools["prepare_environment_snapshot"],
            self.tools["infer_book_search_needs"],
            self.tools["generate_rationale"],
            self.tools["clarify_book_request"],
            self.tools["search_library_catalog"]
        ]
        if len(self.environment.user_current_books) == 10:
            available_tools.append(self.tools["ask_end_of_session"])
        response = self.client.responses.create(
            input=self.messages,
            instructions=self.system_prompt,
            model="gpt-4.1-mini",
            temperature=0.4,
            top_p=0.9,
            tools=available_tools,
            tool_choice=cast(
                ToolChoiceFunctionParam,
                {"type": "function", "name": "generate_rationale"}
            )
        )
        tool_call = response.output[0]
        args = json.loads(tool_call.arguments)
        self.messages.append({
            "type": "function_call",
            "id": tool_call.id,
            "call_id": tool_call.call_id,
            "name": tool_call.name,
            "arguments": json.dumps(args, ensure_ascii=False)
        })
        tool_call_output = self._call_function(tool_call.name, args)
        self.messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": tool_call_output
        })
        # Actions
        available_tools = [
            self.tools["clarify_book_request"],
            self.tools["search_library_catalog"]
        ]
        if len(self.environment.user_current_books) == 10:
            available_tools.append(self.tools["ask_end_of_session"])
        response = self.client.responses.create(
            input=self.messages,
            instructions=self.system_prompt,
            model="gpt-4.1-mini",
            temperature=0.4,
            top_p=0.9,
            tools=available_tools,
            tool_choice="required"
        )
        tool_call = response.output[0]
        args = json.loads(tool_call.arguments)
        self.messages.append({
            "type": "function_call",
            "id": tool_call.id,
            "call_id": tool_call.call_id,
            "name": tool_call.name,
            "arguments": json.dumps(args, ensure_ascii=False)
        })
        tool_call_output = self._call_function(tool_call.name, args)
        self.messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": tool_call_output
        })
        # Action [Update Environment]
        if tool_call.name == "search_library_catalog":
            self.environment.book_search_count += 1
            found_books = []
            for book in json.loads(tool_call_output)["value"]["found_books"]:
                found_books.append(Book(
                    id=book["id"],
                    title=book["title"],
                    searched_at_turn=book["searched_at_turn"]
                ))
            self.environment.book_search_history.insert(0, BookSearchHistory(
                search_at_turn=self.environment.current_turn,
                search_query=args["search_query"],
                found_books=found_books
            ))
            reply_message = f"我根據您的需求，搜尋到以下書籍：\n{json.dumps(json.loads(tool_call_output)['value']['found_books'], ensure_ascii=False)}"
        else:
            reply_message = json.loads(tool_call_output)["value"]["question"]
        self.messages.append({
            "role": "assistant",
            "content": reply_message
        })
        return reply_message