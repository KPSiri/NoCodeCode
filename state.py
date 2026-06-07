from typing import TypedDict, Optional


class AgentState(TypedDict):
    # --- Input ---
    task: str
    session_id: str            

    # --- Planner output ---
    plan: Optional[str]
    language: Optional[str]

    # --- Coder output ---
    code: Optional[str]

    # --- Executor output ---
    execution_result: Optional[dict]

    # --- Debugger output ---
    debug_attempts: int
    error_message: Optional[str]

    # --- Tester output ---
    test_code: Optional[str]
    test_result: Optional[dict]

    # --- Control ---
    user_approved: bool
    is_fixed: bool
    final_output: Optional[str]

    # --- Memory ---
    user_preferences: Optional[dict]