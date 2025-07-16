import os
import json
import requests
from typing import Any
from dotenv import load_dotenv

from smart_book_seeker.models import Book

load_dotenv()

ES_API_URL = os.getenv("ES_API_URL")
ES_API_KEY = os.getenv("ES_API_KEY")

def prepare_environment_snapshot(
    initial_book_search_needs: str,
    book_search_needs: str,
    current_turn: int,
    book_search_count: int,
    book_search_history: list[dict[str, Any]],
    book_selection_history: list[dict[str, Any]],
    user_suggestion_history: list[dict[str, Any]]
) -> str:
    environment_snapshot = {
        "meta": {
            "initial_book_search_needs": {
                "type": "string",
                "description": "使用者對書籍搜尋的初始需求。"
            },
            "book_search_needs": {
                "type": "string",
                "description": "使用者對書籍搜尋的當前需求，可能會隨著對話進行而變化。"
            },
            "current_turn": {
                "type": "integer",
                "description": "當前對話輪數，從 1 開始計數，每次與使用者互動時增加 1。"
            },
            "book_search_count": {
                "type": "integer",
                "description": "你已進行的書籍搜尋次數，從 0 開始計數，每進行一次搜尋就增加 1。"
            },
            "book_search_history": {
                "type": "array",
                "description": "你已進行的書籍搜尋歷史，由近到遠排列。",
                "items": {
                    "type": "object",
                    "properties": {
                        "search_at_turn": {
                            "type": "integer",
                            "description": "該次搜尋發生的對話輪數。"
                        },
                        "search_query": {
                            "type": "string",
                            "description": "該次搜尋所使用的查詢字串。"
                        },
                        "found_books": {
                            "type": "array",
                            "description": "該次搜尋所獲得的書籍列表。",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "該書籍的唯一識別碼。"
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "該書籍的標題。"
                                    },
                                    "searched_at_turn": {
                                        "type": "integer",
                                        "description": "該書被搜尋到時的對話輪數。"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "book_selection_history": {
                "type": "array",
                "description": "使用者已進行的書籍選擇歷史，由近到遠排列。",
                "items": {
                    "type": "object",
                    "properties": {
                        "selection_at_turn": {
                            "type": "integer",
                            "description": "該次選擇發生的對話輪數。"
                        },
                        "candidate_books": {
                            "type": "array",
                            "description": "該次選擇的候選書籍列表。",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "該書籍的唯一識別碼。"
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "該書籍的標題。"
                                    },
                                    "searched_at_turn": {
                                        "type": "integer",
                                        "description": "該書被搜尋到時的對話輪數。"
                                    },
                                    "selection_result": {
                                        "type": "string",
                                        "enum": ["accepted", "rejected"],
                                        "description": "使用者對該書籍的選擇結果，可能是 accepted（接受）或 rejected（拒絕）。"
                                    },
                                    "selection_reason": {
                                        "type": "string",
                                        "description": "使用者接受或拒絕該書籍的原因。"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "user_suggestion_history": {
                "type": "array",
                "description": "使用者已提出的建議歷史，由近到遠排列。",
                "items": {
                    "type": "object",
                    "properties": {
                        "suggestion_at_turn": {
                            "type": "integer",
                            "description": "該次建議發生時的對話輪數。"
                        },
                        "suggestion_text": {
                            "type": "string",
                            "description": "使用者提出的建議內容。"
                        }
                    }
                }
            }
        },
        "value": {
            "initial_book_search_needs": initial_book_search_needs,
            "book_search_needs": book_search_needs,
            "current_turn": current_turn,
            "book_search_count": book_search_count,
            "book_search_history": book_search_history,
            "book_selection_history": book_selection_history,
            "user_suggestion_history": user_suggestion_history
        }
    }
    return json.dumps(environment_snapshot, ensure_ascii=False)

def infer_book_search_needs(
    book_search_needs: str
) -> str:
    book_search_needs = {
        "meta": {
            "book_search_needs": {
                "type": "string",
                "description": "使用者進一步的書籍搜尋需求。"
            }
        },
        "value": {
            "book_search_needs": book_search_needs
        }
    }
    return json.dumps(book_search_needs, ensure_ascii=False)

def generate_rationale(
    rationale: str
) -> str:
    rationale_data = {
        "meta": {
            "rationale": {
                "type": "string",
                "description": "推理的內容。"
            }
        },
        "value": {
            "rationale": rationale
        }
    }
    return json.dumps(rationale_data, ensure_ascii=False)

def ask_end_of_session(
    question: str
) -> str:
    question = {
        "meta": {
            "question": {
                "type": "string",
                "description": "詢問使用者是否結束本次會話的問題。"
            }
        },
        "value": {
            "question": question
        }
    }
    return json.dumps(question, ensure_ascii=False)

def clarify_book_request(
    question: str
) -> str:
    question = {
        "meta": {
            "question": {
                "type": "string",
                "description": "根據多次書籍搜尋結果自動產生的關鍵澄清問題，用以引導使用者更精確、貼合圖書館館藏地描述需求"
            }
        },
        "value": {
            "question": question
        }
    }
    return json.dumps(question, ensure_ascii=False)

def search_library_catalog(
    search_query: str,
    current_turn: int
) -> str:
    header = {
        "Authorization": f"Apikey {ES_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "query": {
            "simple_query_string": {
                "query": search_query,
            }
        }
    }
    response = requests.get(f"{ES_API_URL}/books/_search?size=10", headers=header, json=data)
    found_books = []
    for hit in response.json()["hits"]["hits"]:
        hit["_source"]["searched_at_turn"] = current_turn
        found_books.append(hit["_source"])

    search_result = {
        "meta": {
            "found_books": {
                "type": "array",
                "description": "搜尋所獲得的書籍列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "該書籍的唯一識別碼。"
                        },
                        "title": {
                            "type": "string",
                            "description": "該書籍的標題。"
                        },
                        "searched_at_turn": {
                            "type": "integer",
                            "description": "該書被搜尋到時的對話輪數。"
                        }
                    }
                }
            }
        },
        "value": {
            "found_books": found_books
        }
    }
    return json.dumps(search_result, ensure_ascii=False)