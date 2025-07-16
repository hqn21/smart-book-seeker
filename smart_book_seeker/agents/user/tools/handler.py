import json
from typing import Any

def prepare_environment_snapshot_for_book_selection(
    book_search_needs: str,
    candidate_books: list[dict[str, Any]],
) -> str:
    environment_snapshot = {
        "meta": {
            "book_search_needs": {
                "type": "string",
                "description": "你對書籍搜尋的需求。"
            },
            "candidate_books": {
                "type": "array",
                "description": "候選書籍列表。",
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
            "book_search_needs": book_search_needs,
            "candidate_books": candidate_books
        }
    }
    return json.dumps(environment_snapshot, ensure_ascii=False)

def generate_rationale_for_book_selection(
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

def select_books(
    accepted_books: list[dict[str, Any]],
    rejected_books: list[dict[str, Any]],
) -> str:
    selection_data = {
        "meta": {
            "accepted_books": {
                "type": "array",
                "description": "candidate_books 中最符合你的需求的 10 本書籍。",
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
                        "reason_for_acceptance": {
                            "type": "string",
                            "description": "你接受該書籍的原因。"
                        }
                    }
                }
            },
            "rejected_books": {
                "type": "array",
                "description": "candidate_books 中不符合你的需求的書籍。",
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
                        "reason_for_rejection": {
                            "type": "string",
                            "description": "你拒絕該書籍的原因。"
                        }
                    }
                }
            }
        },
        "value": {
            "accepted_books": accepted_books,
            "rejected_books": rejected_books
        }
    }
    return json.dumps(selection_data, ensure_ascii=False)

def prepare_environment_snapshot_for_question_answering(
    book_search_needs: str,
    current_books: list[dict[str, Any]],
) -> str:
    environment_snapshot = {
        "meta": {
            "book_search_needs": {
                "type": "string",
                "description": "你對書籍搜尋的需求。"
            },
            "current_books": {
                "type": "array",
                "description": "你當前持有的書籍列表。",
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
            "book_search_needs": book_search_needs,
            "current_books": current_books
        }
    }
    return json.dumps(environment_snapshot, ensure_ascii=False)

def generate_rationale_for_question_answering(
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

def answer_question(
    answer: str,
) -> str:
    answer_data = {
        "meta": {
            "answer": {
                "type": "string",
                "description": "關於圖書館員提出的問題的回答。"
            }
        },
        "value": {
            "answer": answer
        }
    }
    return json.dumps(answer_data, ensure_ascii=False)

def prepare_environment_snapshot_for_termination_request_decision(
    book_search_needs: str,
    current_turn: int,
    book_search_count: int,
    termination_request_received_count: int,
    current_books: list[dict[str, Any]],
    book_search_history: list[dict[str, Any]],
    book_selection_history: list[dict[str, Any]],
    suggestion_history: list[dict[str, Any]],
) -> str:
    environment_snapshot = {
        "meta": {
            "book_search_needs": {
                "type": "string",
                "description": "你對書籍搜尋的需求。"
            },
            "current_turn": {
                "type": "integer",
                "description": "當前對話輪數，從 1 開始計數，每次與圖書館員互動時增加 1。"
            },
            "book_search_count": {
                "type": "integer",
                "description": "圖書館員已進行的書籍搜尋次數，從 0 開始計數，每進行一次搜尋就增加 1。"
            },
            "termination_request_received_count": {
                "type": "integer",
                "description": "你已收到的終止請求次數，從 0 開始計數，每收到一次請求就增加 1。"
            },
            "current_books": {
                "type": "array",
                "description": "你當前持有的書籍列表。",
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
            },
            "book_search_history": {
                "type": "array",
                "description": "圖書館員已進行的書籍搜尋歷史，由近到遠排列。",
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
                "description": "你已進行的書籍選擇歷史，由近到遠排列。",
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
                                        "description": "你對該書籍的選擇結果，可能是 accepted（接受）或 rejected（拒絕）。"
                                    },
                                    "selection_reason": {
                                        "type": "string",
                                        "description": "你接受或拒絕該書籍的原因。"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "suggestion_history": {
                "type": "array",
                "description": "你已提出的建議歷史，由近到遠排列。",
                "items": {
                    "type": "object",
                    "properties": {
                        "suggestion_at_turn": {
                            "type": "integer",
                            "description": "該次建議發生的對話輪數。"
                        },
                        "suggestion_text": {
                            "type": "string",
                            "description": "該次建議的內容。"
                        }
                    }
                }
            }
        },
        "value": {
            "book_search_needs": book_search_needs,
            "current_turn": current_turn,
            "book_search_count": book_search_count,
            "termination_request_received_count": termination_request_received_count,
            "current_books": current_books,
            "book_search_history": book_search_history,
            "book_selection_history": book_selection_history,
            "suggestion_history": suggestion_history
        }
    }
    return json.dumps(environment_snapshot, ensure_ascii=False)

def generate_rationale_for_termination_request_decision(
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

def accept_termination_request(
    reason_for_acceptance: str,
) -> str:
    termination_data = {
        "meta": {
            "reason_for_acceptance": {
                "type": "string",
                "description": "你接受該終止對話請求的原因。"
            }
        },
        "value": {
            "reason_for_acceptance": reason_for_acceptance
        }
    }
    return json.dumps(termination_data, ensure_ascii=False)

def reject_termination_request(
    reason_for_rejection: str,
    suggestion_text: str,
) -> str:
    rejection_data = {
        "meta": {
            "reason_for_rejection": {
                "type": "string",
                "description": "你拒絕該終止對話請求的原因。"
            },
            "suggestion_text": {
                "type": "string",
                "description": "你對圖書館員的建議，提供更多可嘗試且詳細的搜尋方向與建議。"
            }
        },
        "value": {
            "reason_for_rejection": reason_for_rejection,
            "suggestion_text": suggestion_text
        }
    }
    return json.dumps(rejection_data, ensure_ascii=False)