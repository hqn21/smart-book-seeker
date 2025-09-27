import re
import copy
import os
import json
import time
from typing import Literal
from openai import OpenAI
from dotenv import load_dotenv
from smart_book_seeker.models import UserNeedsAgentState, UserAgentState, LibrarianAgentState
from smart_book_seeker.log_config import get_logger
from smart_book_seeker.agents import UserNeedsAgent, LibrarianAgent, UserAgent
load_dotenv()

logger = get_logger(__name__)

class ConversationManager:
    def __init__(self, strategy: Literal["keyword_query", "boolean_query", "iterative_top_k"]):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.messages = []
        self.strategy = strategy
        self.user_needs_agent = UserNeedsAgent()
        self.librarian_agent = LibrarianAgent(book_search_needs="", strategy=strategy)
        self.user_agent = UserAgent(book_search_needs="", strategy=strategy)
        self.user_needs_agent_messages = []
        self.last_discuss_time = 0.0

    def _convert_to_first_person(self, sentence: str) -> str:
        response = self.client.responses.create(
            input=f"請將「{sentence}」轉為第一人稱角度，不需增加或減少任何資訊。你只需要回傳修改後的句子即可。",
            model="gpt-4o-mini",
            temperature=0.2,
            top_p=0.9
        )
        return response.output[0].content[0].text

    def understand_user_needs(self, message: str):
        logger.info(f"理解用戶需求：{message}")
        self.messages.append({"role": "user", "content": message})
        self.user_needs_agent_messages.append({"role": "user", "content": message})
        user_needs_agent_response = self.user_needs_agent.respond(messages=self.user_needs_agent_messages)
        self.user_needs_agent_messages.append({"role": "assistant", "content": user_needs_agent_response})
        user_needs_agent_response_parsed = self.user_needs_agent.parse_response(response=user_needs_agent_response)
        self.messages.append({"role": "user_needs_agent", "content": user_needs_agent_response_parsed})
        yield user_needs_agent_response_parsed

    def discuss(self, book_search_needs: str):
        start_time = time.time()
        self.librarian_agent = LibrarianAgent(book_search_needs=book_search_needs, strategy=self.strategy)
        self.user_agent = UserAgent(book_search_needs=book_search_needs, strategy=self.strategy)
        user_agent_response = self._convert_to_first_person(book_search_needs)
        while True:
            self.librarian_agent.environment.current_turn += 1
            self.user_agent.environment.current_turn += 1
            librarian_agent_response = self.librarian_agent.respond(message=user_agent_response)
            yield f"[Librarian Agent] {librarian_agent_response}"

            # Update Environment
            self.user_agent.environment.book_search_count = self.librarian_agent.environment.book_search_count
            self.user_agent.environment.book_search_history = self.librarian_agent.environment.book_search_history
            if self.librarian_agent.state == LibrarianAgentState.SEARCH:
                self.user_agent.environment.candidate_books = copy.deepcopy(self.user_agent.environment.current_books)
                for book in self.librarian_agent.environment.book_search_history[0].found_books:
                    book_duplicated = False
                    for candidate_book in self.user_agent.environment.candidate_books:
                        if book.id == candidate_book.id:
                            book_duplicated = True
                            break
                    if not book_duplicated:
                        self.user_agent.environment.candidate_books.append(book)

            user_agent_response = self.user_agent.respond(message=librarian_agent_response, librarian_agent_state=self.librarian_agent.state)
            yield f"[User Agent] {user_agent_response}"
            if self.user_agent.state == UserAgentState.ACCEPT_TERMINATION:
                break

            # Update Environment
            self.librarian_agent.environment.book_selection_history = self.user_agent.environment.book_selection_history
            self.librarian_agent.environment.user_suggestion_history = self.user_agent.environment.suggestion_history
            self.librarian_agent.environment.user_current_books = self.user_agent.environment.current_books
            self.librarian_agent.environment.user_current_books_count = self.user_agent.environment.current_books_count
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.last_discuss_time = elapsed_time
        logger.info(f"[User Agent] 持有書籍清單：\n{json.dumps([book.to_dict() for book in self.user_agent.environment.current_books], indent=2, ensure_ascii=False)}")
        logger.info(f"整個對話過程花費時間：{elapsed_time:.2f} 秒")

    def search_only(self, book_search_needs: str):
        start_time = time.time()
        self.librarian_agent = LibrarianAgent(book_search_needs=book_search_needs, strategy="search_only")
        self.librarian_agent.environment.current_turn += 1
        user_agent_response = self._convert_to_first_person(book_search_needs)
        librarian_agent_response = self.librarian_agent.respond(message=user_agent_response)
        yield f"[Librarian Agent] {librarian_agent_response}"
        self.user_agent.environment.current_books = self.librarian_agent.environment.book_search_history[0].found_books
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.last_discuss_time = elapsed_time
        logger.info(f"[User Agent] 持有書籍清單：\n{json.dumps([book.to_dict() for book in self.user_agent.environment.current_books], indent=2, ensure_ascii=False)}")

    def route(self, message: str):
        yield from self.understand_user_needs(message=message)
        if self.user_needs_agent.state == UserNeedsAgentState.IDLE:
            book_search_needs = re.search(r'\[總結] (.*)', self.user_needs_agent_messages[-1]["content"]).group(1)
            self.user_needs_agent_messages = []
            logger.info("User Needs Agent 已生成需求總結，清空 User Needs Agent 的訊息歷史，並準備進行下一步操作")
            yield from self.discuss(book_search_needs=book_search_needs)