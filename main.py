import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(__file__))
 
from dotenv import load_dotenv
from graph.workflow import build_graph
from memory.short_term import get_checkpointer
from memory.long_term import (
    load_preferences, save_preferences,
    save_task, load_recent_tasks,
    create_session, list_sessions, get_session,
    delete_session, rename_session,
    save_message, load_chat_history,
    update_session_timestamp,
)
from state import AgentState
 
load_dotenv()
 
USER_ID = "local_user"
 
def print_banner():
    print("""
╔═══════════════════════════════════════════╗
║        NoCodeCode — Coding Agent          ║
║ Plans · Codes · Executes · Debugs · Tests ║
╚═══════════════════════════════════════════╝
""")
    
def print_divider():
    print("─" * 50)

def show_session_menu(user_id: str) -> dict:
    """
    Show the main menu and return the session the user wants to use.
    A session contains: session_id, title, thread_id.
    """
    while True:
        sessions = list_sessions(user_id)
 
        print("\n📂 SESSIONS")
        print_divider()
 
        if not sessions:
            print("  No sessions yet.\n")
        else:
            for i, s in enumerate(sessions, 1):
                # show date in readable format
                date = s["updated_at"][:10]
                print(f"  [{i}] {s['title']:<35} {date}")
 
        print_divider()
        print("  [n] New chat")
        if sessions:
            print("  [r] Resume a chat")
            print("  [d] Delete a chat")
            print("  [x] Rename a chat")
        print("  [h] Show recent task history")
        print("  [q] Quit")
        print_divider()
 
        choice = input("Choose: ").strip().lower()
 
        if choice == "n":
            return _new_session(user_id)
 
        elif choice == "r" and sessions:
            return _pick_session(sessions, "resume")
 
        elif choice == "d" and sessions:
            session = _pick_session(sessions, "delete")
            if session:
                confirm = input(f"Delete '{session['title']}'? (yes/no): ").strip().lower()
                if confirm in ("yes", "y"):
                    delete_session(session["session_id"])
                    print("✅ Deleted.")
            # loop back to menu after deletion
 
        elif choice == "x" and sessions:
            session = _pick_session(sessions, "rename")
            if session:
                new_title = input("New title: ").strip()
                if new_title:
                    rename_session(session["session_id"], new_title)
                    print("✅ Renamed.")
 
        elif choice == "h":
            _show_task_history(user_id)
 
        elif choice == "q":
            print("Goodbye!")
            sys.exit(0)

def _new_session(user_id: str) -> dict:
    """Ask for a title, create a new session, return it."""
    title = input("Session title (or press Enter for auto title): ").strip()
    if not title:
        from datetime import datetime
        title = f"Chat {datetime.utcnow().strftime('%b %d %H:%M')}"
 
    thread_id = str(uuid.uuid4())
    session_id = create_session(user_id, title, thread_id)
 
    print(f"\n✅ New session: '{title}'")
    return {"session_id": session_id, "title": title, "thread_id": thread_id}

def _pick_session(sessions: list, action: str) -> dict | None:
    """Ask user to pick a session by number."""
    choice = input(f"Enter session number to {action}: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            return sessions[idx]
    except ValueError:
        pass
    print("Invalid choice.")
    return None

def _show_task_history(user_id: str):
    """Print the last 10 tasks across all sessions."""
    tasks = load_recent_tasks(user_id, limit=10)
    print("\n📋 RECENT TASK HISTORY")
    print_divider()
    if not tasks:
        print("  No tasks yet.")
    for t in tasks:
        status = "✅" if t["success"] else "❌"
        date = t["at"][:16].replace("T", " ")
        print(f"  {status} [{date}] {t['task'][:55]}")
    print_divider()
    input("Press Enter to continue...")


def print_chat_history(session_id: str):
    """Print all previous messages in this session."""
    history = load_chat_history(session_id)
    if not history:
        return
    print("\n── Chat history ─────────────────────────────")
    for msg in history:
        prefix = "You  " if msg["role"] == "user" else "Agent"
        # trim long agent messages in the history view
        content = msg["content"]
        if len(content) > 120:
            content = content[:120] + "..."
        print(f"  {prefix}: {content}")
    print("─────────────────────────────────────────────\n")


def build_agent_summary(final_state: AgentState) -> str:
    """Build a short text summary of what the agent did — saved to chat history."""
    lines = []
    result = final_state.get("execution_result", {})
    if result.get("success"):
        lines.append("✅ Code executed successfully.")
        if result.get("stdout"):
            lines.append(f"Output: {result['stdout'][:200]}")
    else:
        lines.append("❌ Execution failed.")
        if result.get("stderr"):
            lines.append(f"Error: {result['stderr'][:200]}")
 
    test = final_state.get("test_result")
    if test:
        lines.append(f"Tests: {test['passed']} passed, {test['failed']} failed.")
 
    if final_state.get("code"):
        lines.append(f"\nFinal code:\n{final_state['code'][:500]}")
 
    return "\n".join(lines)

def print_final_report(state: AgentState):
    print("\n" + "=" * 50)
    print("RESULT")
    print("=" * 50)
 
    result = state.get("execution_result", {})
    if result:
        status = "✅ Success" if result.get("success") else "❌ Failed"
        print(f"Execution : {status}")
        if result.get("stdout"):
            print(f"Output    :\n{result['stdout']}")
        if result.get("stderr"):
            print(f"Errors    :\n{result['stderr']}")
 
    test = state.get("test_result")
    if test:
        print(f"Tests     : {test['passed']} passed, {test['failed']} failed")
        if test.get("output"):
            print(test["output"])
 
    if state.get("debug_attempts", 0) > 0:
        print(f"Debugs    : {state['debug_attempts']} attempt(s)")
 
    print("=" * 50)


def update_preferences(preferences: dict, state: AgentState) -> dict:
    if state.get("language"):
        preferences["language"] = state["language"]
    recent = preferences.get("recent_tasks", [])
    recent.append(state["task"])
    preferences["recent_tasks"] = recent[-10:]
    return preferences


# ---Main ---------------------------------------------------------------
 
 
def main():
    print_banner()
 
    # Load long-term preferences once at startup
    preferences = load_preferences(USER_ID)
 
    # Show session menu — user picks new or existing session
    session = show_session_menu(USER_ID)
    session_id = session["session_id"]
    thread_id  = session["thread_id"]
 
    print(f"\n💬 '{session['title']}'")
 
    # Print chat history for resumed sessions
    print_chat_history(session_id)
 
    # Build graph with persistent SqliteSaver checkpointer
    # Same thread_id → LangGraph resumes from exact last state
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id}}
    graph = build_graph(checkpointer=checkpointer)
 
    print("Type your task below. 'menu' = back to sessions. 'exit' = quit.\n")
 
    # ── Conversation loop ──────────────────────────────────────
    while True:
        try:
            task = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            task = "exit"
 
        if not task:
            continue
 
        if task.lower() in ("exit", "quit", "q"):
            save_preferences(USER_ID, preferences)
            from observability.tracer import flush
            flush()  
            print("\n✅ Memory saved. Goodbye!")
            break
 
        if task.lower() == "menu":
            # save before going back to menu
            save_preferences(USER_ID, preferences)
            session = show_session_menu(USER_ID)
            session_id = session["session_id"]
            thread_id  = session["thread_id"]
            config = {"configurable": {"thread_id": thread_id}}
            print(f"\n💬 '{session['title']}'")
            print_chat_history(session_id)
            continue
 
        if task.lower() == "history":
            print_chat_history(session_id)
            continue
 
        # Save user message to chat history
        save_message(session_id, "user", task)
 
        initial_state: AgentState = {
            "task": task,
            "session_id": session_id, 
            "plan": None,
            "language": None,
            "code": None,
            "execution_result": None,
            "debug_attempts": 0,
            "error_message": None,
            "test_code": None,
            "test_result": None,
            "user_approved": False,
            "is_fixed": False,
            "final_output": None,
            "user_preferences": preferences,
        }
 
        print(f"\n🚀 Running...\n")
 
        final_state = graph.invoke(initial_state, config=config)
 
        # Save agent summary to chat history
        summary = build_agent_summary(final_state)
        save_message(session_id, "agent", summary)
 
        # Update session timestamp so it sorts to top
        update_session_timestamp(session_id)
 
        # Update in-memory preferences
        preferences = update_preferences(preferences, final_state)
 
        # Log task to history
        success = final_state.get("execution_result", {}).get("success", False)
        save_task(USER_ID, session_id, task, final_state.get("language", "unknown"), success)
 
        print_final_report(final_state)
        print("\n── Ready. Type next task, 'menu', or 'exit'. ──\n")
 
 
if __name__ == "__main__":
    main()
