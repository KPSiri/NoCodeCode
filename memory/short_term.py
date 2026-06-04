"""
from langgraph.checkpoint.memory import MemorySaver
 
# MemorySaver stores the full LangGraph state in RAM after every node.
# It uses thread_id to separate different conversations.
#
# How it works:
#   - graph.invoke(state, config={"configurable": {"thread_id": "abc"}})
#   - After each node, LangGraph snapshots the state under that thread_id
#   - If you call invoke again with the same thread_id, it resumes from
#     exactly where it left off
#   - RAM only — gone when the process restarts (that's fine for short-term)
 
def get_checkpointer() -> MemorySaver:
    return MemorySaver()
"""

import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
 
CHECKPOINT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "../data/checkpoints.db"
)
 
def get_checkpointer() -> SqliteSaver:
    """
    SqliteSaver requires an already-open sqlite3 connection.
    We open the connection manually and pass it in directly —
    this avoids the context manager issue in newer LangGraph versions.
    """
    os.makedirs(os.path.dirname(CHECKPOINT_DB_PATH), exist_ok=True)
 
    # open a persistent connection and pass it directly to SqliteSaver
    conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)
