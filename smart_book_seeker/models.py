from typing import Literal
from dataclasses import dataclass, asdict
from enum import Enum, unique, auto

@unique
class UserNeedsAgentState(Enum):
    IDLE = auto()
    COLLECT = auto()

@unique
class UserAgentState(Enum):
    IDLE = auto()
    SELECT = auto()
    ANSWER = auto()
    ACCEPT_TERMINATION = auto()
    REJECT_TERMINATION = auto()

@unique
class LibrarianAgentState(Enum):
    IDLE = auto()
    ASK = auto()
    ASK_TO_CLOSE = auto()
    SEARCH = auto()

@dataclass
class Book:
    id: str
    title: str
    searched_at_turn: int

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class CandidateBook:
    book: Book
    selection_result: Literal["accepted", "rejected"]
    selection_reason: str

@dataclass
class BookSearchHistory:
    search_at_turn: int
    search_query: str
    found_books: list[Book]

@dataclass
class BookSelectionHistory:
    selection_at_turn: int
    candidate_books: list[CandidateBook]

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class UserSuggestionHistory:
    suggestion_at_turn: int
    suggestion_text: str

@dataclass
class LibrarianAgentEnvironment:
    initial_book_search_needs: str
    book_search_needs: str
    current_turn: int
    book_search_count: int
    book_search_history: list[BookSearchHistory]
    book_selection_history: list[BookSelectionHistory]
    user_suggestion_history: list[UserSuggestionHistory]
    user_current_books: list[Book]

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class UserAgentEnvironment:
    book_search_needs: str
    current_turn: int
    book_search_count: int
    termination_request_received_count: int
    current_books: list[Book]
    book_search_history: list[BookSearchHistory]
    book_selection_history: list[BookSelectionHistory]
    suggestion_history: list[UserSuggestionHistory]
    candidate_books: list[Book]

    def to_dict(self) -> dict:
        return asdict(self)