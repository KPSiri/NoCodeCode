from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from agents.planner import run_planner
from agents.executor import run_executor    
from agents.coder import run_coder
from agents.debugger import run_debugger
from agents.tester import run_tester

#----Routing function----

def after_executor(state: AgentState) -> str:
    """After running code: if denied, end. If error, debug. If success, test."""
    if not state.get("user_approved"):
        return "end"
    result = state.get("execution_result", {})
    if result.get("success"):
        return "tester"
    return "debugger"
 
 
def after_debugger(state: AgentState) -> str:
    """After debugging: if gave up, end. Otherwise re-run the fixed code."""
    if not state.get("is_fixed"):
        return "end"
    if state.get("debug_attempts", 0) >= 3:
        return "end"
    return "executor"

# ── Build graph ────────────────────────────────────────────────────
 
def build_graph(checkpointer=None):

    """
    Build and compile the LangGraph state machine.
 
    checkpointer: pass a MemorySaver (or SqliteSaver) here to enable
                  short-term memory across nodes within a session.
                  If None, graph runs statelessly (fine for testing).
    """
    g = StateGraph(AgentState)
 
    # Register all nodes
    g.add_node("planner",  run_planner)
    g.add_node("coder",    run_coder)
    g.add_node("executor", run_executor)
    g.add_node("debugger", run_debugger)
    g.add_node("tester",   run_tester)
 
    # Entry point
    g.set_entry_point("planner")
 
    # Fixed edges
    g.add_edge("planner", "coder")
    g.add_edge("coder",   "executor")
 
    # Conditional edges (routing logic above)
    g.add_conditional_edges(
        "executor",
        after_executor,
        {
            "tester":   "tester",
            "debugger": "debugger",
            "end":      END,
        }
    )
 
    g.add_conditional_edges(
        "debugger",
        after_debugger,
        {
            "executor": "executor",
            "end":      END,
        }
    )
 
    g.add_edge("tester", END)
 
    return g.compile(checkpointer=checkpointer)