import os
import json
import random
import string
from typing import Literal, cast
from openai import OpenAI
from dotenv import load_dotenv
from openai.types.responses import ToolChoiceFunctionParam
from smart_book_seeker.log_config import get_logger
from smart_book_seeker.models import UserAgentState, UserAgentEnvironment, LibrarianAgentState, Book, BookSelectionHistory, CandidateBook, UserSuggestionHistory
from smart_book_seeker.agents.user.tools import *
load_dotenv()

logger = get_logger(__name__)

class UserAgent:
    def __init__(self, book_search_needs: str, strategy: Literal["keyword_query", "boolean_query", "iterative_top_k"]):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(os.path.join(os.path.dirname(__file__), "prompts", f"{strategy}.txt")) as f:
            self.system_prompt = f"# 關於對話主題\n你是一位正在與圖書館員對話的使用者。{self._convert_to_second_person(book_search_needs)}{f.read()}"
        self.state = UserAgentState.IDLE
        self.messages = []
        self.environment = UserAgentEnvironment(
            book_search_needs=book_search_needs,
            current_turn=0,
            book_search_count=0,
            termination_request_received_count=0,
            current_books=[],
            current_books_count=0,
            book_search_history=[],
            book_selection_history=[],
            suggestion_history=[],
            candidate_books=[]
        )
        self.tools = self._load_tools()

        if strategy == "keyword_query":
            self.respond = self._keyword_query_respond
        elif strategy == "boolean_query":
            self.respond = self._boolean_query_respond
        elif strategy == "iterative_top_k":
            self.respond = self._iterative_top_k_respond

        logger.info("User Agent 初始化完成")

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

    def _convert_to_second_person(self, sentence: str) -> str:
        response = self.client.responses.create(
            input=f"請將「{sentence}」轉為第一人稱角度，不需增加或減少任何資訊。你只需要回傳修改後的句子即可。",
            model="gpt-4o-mini",
            temperature=0.2,
            top_p=0.9
        )
        return response.output[0].content[0].text

    def _call_function(self, name, args):
        if name == "prepare_environment_snapshot_for_book_selection":
            return prepare_environment_snapshot_for_book_selection(**args)
        if name == "generate_rationale_for_book_selection":
            return generate_rationale_for_book_selection(**args)
        if name == "select_books":
            self.state = UserAgentState.SELECT
            return select_books(**args)
        if name == "prepare_environment_snapshot_for_question_answering":
            return prepare_environment_snapshot_for_question_answering(**args)
        if name == "generate_rationale_for_question_answering":
            return generate_rationale_for_question_answering(**args)
        if name == "answer_question":
            self.state = UserAgentState.ANSWER
            return answer_question(**args)
        if name == "prepare_environment_snapshot_for_termination_request_decision":
            return prepare_environment_snapshot_for_termination_request_decision(**args)
        if name == "generate_rationale_for_termination_request_decision":
            return generate_rationale_for_termination_request_decision(**args)
        if name == "accept_termination_request":
            self.state = UserAgentState.ACCEPT_TERMINATION
            return accept_termination_request(**args)
        if name == "reject_termination_request":
            self.state = UserAgentState.REJECT_TERMINATION
            return reject_termination_request(**args)
        raise ValueError(f"Unknown function name: {name}")

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

    def _iterative_top_k_respond(self, message: str, librarian_agent_state: LibrarianAgentState) -> str:
        self.messages.append({"role": "user", "content": message})
        reply_message = "遇到預料外的情況。"
        environment_dict = self.environment.to_dict()
        if librarian_agent_state == LibrarianAgentState.SEARCH:
            # Prepare Environment Snapshot for Book Selection
            fake_call_id = self._generate_fake_id("call_environment_", 29)
            args = {key: environment_dict[key] for key in {"book_search_needs", "candidate_books"} if key in environment_dict}
            self.messages.append({
                "type": "function_call",
                "call_id": fake_call_id,
                "name": "prepare_environment_snapshot_for_book_selection",
                "arguments": json.dumps(args, ensure_ascii=False)
            })
            self.messages.append({
                "type": "function_call_output",
                "call_id": fake_call_id,
                "output": self._call_function("prepare_environment_snapshot_for_book_selection", args)
            })
            # Generate Rationale for Book Selection
            response = self.client.responses.create(
                input=self.messages,
                instructions=self.system_prompt,
                model="gpt-4.1-mini",
                temperature=0.2,
                top_p=0.9,
                tools=[
                    self.tools["prepare_environment_snapshot_for_book_selection"],
                    self.tools["generate_rationale_for_book_selection"],
                    self.tools["select_books"]
                ],
                tool_choice=cast(
                    ToolChoiceFunctionParam,
                    {"type": "function", "name": "generate_rationale_for_book_selection"}
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
            # Book Selection
            response = self.client.responses.create(
                input=self.messages,
                instructions=self.system_prompt,
                model="gpt-4.1-mini",
                temperature=0.2,
                top_p=0.9,
                tools=[
                    self.tools["prepare_environment_snapshot_for_book_selection"],
                    self.tools["generate_rationale_for_book_selection"],
                    self.tools["select_books"]
                ],
                tool_choice=cast(
                    ToolChoiceFunctionParam,
                    {"type": "function", "name": "select_books"}
                )
            )
            logger.info(f"Book Selection Response: {response}")
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
            # Book Selection [Update Environment]
            self.environment.current_books = []
            self.environment.current_books_count = 0
            self.environment.book_selection_history.insert(0, BookSelectionHistory(
                selection_at_turn=self.environment.current_turn,
                candidate_books=[]
            ))
            for book in json.loads(tool_call_output)["value"]["accepted_books"]:
                self.environment.current_books.append(Book(
                    id=book["id"],
                    title=book["title"],
                    searched_at_turn=book["searched_at_turn"]
                ))
                self.environment.book_selection_history[0].candidate_books.append(CandidateBook(
                    book=Book(
                        id=book["id"],
                        title=book["title"],
                        searched_at_turn=book["searched_at_turn"]
                    ),
                    selection_result="accepted",
                    selection_reason=book["reason_for_acceptance"]
                ))
            self.environment.current_books_count = len(self.environment.current_books)
            for book in json.loads(tool_call_output)["value"]["rejected_books"]:
                self.environment.book_selection_history[0].candidate_books.append(CandidateBook(
                    book=Book(
                        id=book["id"],
                        title=book["title"],
                        searched_at_turn=book["searched_at_turn"]
                    ),
                    selection_result="rejected",
                    selection_reason=book["reason_for_rejection"]
                ))
            self.environment.candidate_books = []
            reply_message = f"我已根據我的需求，對你提供的書籍進行篩選，篩選結果如下：\n{json.dumps(self.environment.book_selection_history[0].to_dict(), ensure_ascii=False)}"
        elif librarian_agent_state == LibrarianAgentState.ASK:
            # Prepare Environment Snapshot for Question Answering
            fake_call_id = self._generate_fake_id("call_environment_", 29)
            args = {key: environment_dict[key] for key in {"book_search_needs", "current_books", "current_books_count"} if key in environment_dict}
            self.messages.append({
                "type": "function_call",
                "call_id": fake_call_id,
                "name": "prepare_environment_snapshot_for_question_answering",
                "arguments": json.dumps(args, ensure_ascii=False)
            })
            self.messages.append({
                "type": "function_call_output",
                "call_id": fake_call_id,
                "output": self._call_function("prepare_environment_snapshot_for_question_answering", args)
            })
            # Generate Rationale for Question Answering
            response = self.client.responses.create(
                input=self.messages,
                instructions=self.system_prompt,
                model="gpt-4.1-mini",
                temperature=0.2,
                top_p=0.9,
                tools=[
                    self.tools["prepare_environment_snapshot_for_question_answering"],
                    self.tools["generate_rationale_for_question_answering"],
                    self.tools["answer_question"]
                ],
                tool_choice=cast(
                    ToolChoiceFunctionParam,
                    {"type": "function", "name": "generate_rationale_for_question_answering"}
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
            # Answer Question
            response = self.client.responses.create(
                input=self.messages,
                instructions=self.system_prompt,
                model="gpt-4.1-mini",
                temperature=0.2,
                top_p=0.9,
                tools=[
                    self.tools["prepare_environment_snapshot_for_question_answering"],
                    self.tools["generate_rationale_for_question_answering"],
                    self.tools["answer_question"]
                ],
                tool_choice=cast(
                    ToolChoiceFunctionParam,
                    {"type": "function", "name": "answer_question"}
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
            reply_message = json.loads(tool_call_output)["value"]["answer"]
        elif librarian_agent_state == LibrarianAgentState.ASK_TO_CLOSE:
            # Prepare Environment Snapshot for Termination Request Decision
            fake_call_id = self._generate_fake_id("call_environment_", 29)
            args = {key: environment_dict[key] for key in {"book_search_needs", "current_turn", "book_search_count", "termination_request_received_count", "current_books", "current_books_count", "book_search_history", "book_selection_history", "suggestion_history"} if key in environment_dict}
            self.messages.append({
                "type": "function_call",
                "call_id": fake_call_id,
                "name": "prepare_environment_snapshot_for_termination_request_decision",
                "arguments": json.dumps(args, ensure_ascii=False)
            })
            self.messages.append({
                "type": "function_call_output",
                "call_id": fake_call_id,
                "output": self._call_function("prepare_environment_snapshot_for_termination_request_decision", args)
            })
            # Generate Rationale for Termination Request Decision
            response = self.client.responses.create(
                input=self.messages,
                instructions=self.system_prompt,
                model="gpt-4.1-mini",
                temperature=0.2,
                top_p=0.9,
                tools=[
                    self.tools["prepare_environment_snapshot_for_termination_request_decision"],
                    self.tools["generate_rationale_for_termination_request_decision"],
                    self.tools["accept_termination_request"],
                    self.tools["reject_termination_request"]
                ],
                tool_choice=cast(
                    ToolChoiceFunctionParam,
                    {"type": "function", "name": "generate_rationale_for_termination_request_decision"}
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
            # Accept or Reject Termination Request
            response = self.client.responses.create(
                input=self.messages,
                instructions=self.system_prompt,
                model="gpt-4.1-mini",
                temperature=0.2,
                top_p=0.9,
                tools=[
                    self.tools["accept_termination_request"],
                    self.tools["reject_termination_request"]
                ],
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
            if tool_call.name == "accept_termination_request":
                reply_message = json.loads(tool_call_output)["value"]["reason_for_acceptance"]
            else:
                self.environment.termination_request_received_count += 1
                self.environment.suggestion_history.insert(0, UserSuggestionHistory(
                    suggestion_at_turn=self.environment.current_turn,
                    suggestion_text=json.loads(tool_call_output)["value"]["suggestion_text"]
                ))
                reply_message = f"{json.loads(tool_call_output)['value']['reason_for_rejection']}\n{json.loads(tool_call_output)['value']['suggestion_text']}"
        self.messages.append({
            "role": "assistant",
            "content": reply_message
        })
        return reply_message