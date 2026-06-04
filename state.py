from typing import TypedDict, Optional
 
 
class AgentState(TypedDict):
    # --- Input ---
    task: str                        # the user's original request
 
    # --- Planner output ---
    plan: Optional[str]              # step-by-step breakdown
    language: Optional[str]          # detected language (python, js, etc.)
 
    # --- Coder output ---
    code: Optional[str]              # generated code
 
    # --- Executor output ---
    execution_result: Optional[dict] # {"stdout": ..., "stderr": ..., "success": bool}
 
    # --- Debugger output ---
    debug_attempts: int              # how many times we've tried to fix
    error_message: Optional[str]     # last error seen
 
    # --- Tester output ---
    test_code: Optional[str]         # generated test cases
    test_result: Optional[dict]      # {"passed": int, "failed": int, "output": str}
 
    # --- Control ---
    user_approved: bool              # did user approve execution?
    is_fixed: bool                   # did debugger fix the error?
    final_output: Optional[str]      # final summary shown to user
 
    # --- Memory ---
    # Long-term preferences loaded at session start and injected into planner.
    # Example: {"language": "python", "style": "functional", "past_tasks": [...]}
    user_preferences: Optional[dict]