import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from observability.tracer import log, get_langfuse_handler
from state import AgentState
from dotenv import load_dotenv
from utils import extract_text
 
load_dotenv()
 
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
 
PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a coding task planner. Given a programming task, you:
1. Detect the best programming language (default Python if unspecified)
2. Break the task into clear implementation steps
3. Mention any edge cases to handle

User preferences (from memory — respect these):
{preferences}
     
Keep your plan concise and practical. Format:
LANGUAGE: <language>
STEPS:
1. ...
2. ...
EDGE CASES:
- ...
"""),
    ("human", "Task: {task}")
])
 
chain = PROMPT | llm

def _format_preferences(prefs: dict) -> str:
    """
    Turn the preferences dict into a readable string for the prompt.
    If no preferences exist yet, tell the model to use defaults.
    """
    if not prefs:
        return "No preferences saved yet. Use sensible defaults."
 
    lines = []
    if prefs.get("language"):
        lines.append(f"- Preferred language: {prefs['language']}")
    if prefs.get("style"):
        lines.append(f"- Code style: {prefs['style']}")
    if prefs.get("recent_tasks"):
        tasks = ", ".join(prefs["recent_tasks"][-3:])  # last 3 tasks
        lines.append(f"- Recent tasks: {tasks}")
 
    return "\n".join(lines) if lines else "No specific preferences."

def run_planner(state: AgentState) -> AgentState:
    log("planner", "started", {"task": state["task"]})
    print("\n[Planner] Analysing task...")
 
    start = time.time()
 
    # get LangFuse handler — None if keys not set, chain still works
    handler = get_langfuse_handler(
        session_id=state.get("session_id", "unknown"),
        task=state["task"]
    )
 
    preferences = state.get("user_preferences") or {}
    pref_text = _format_preferences(preferences)
 
    # pass handler in config — LangFuse records this LLM call automatically
    invoke_config = {"callbacks": [handler]} if handler else {}
    response = chain.invoke(
        {"task": state["task"], "preferences": pref_text},
        config=invoke_config
    )

    #content = response.content
    content = extract_text(response)
 
 
    # extract language from response (default to preferences or python)
    language = preferences.get("language", "python") 

    for line in content.splitlines():
        if line.startswith("LANGUAGE:"):
            language = line.split(":", 1)[1].strip().lower()
            break
    
    elapsed = round(time.time() - start, 2)
 
    state["plan"] = content
    state["language"] = language
    state["debug_attempts"] = 0
    state["user_approved"] = False
    state["is_fixed"] = False
 
    log("planner", "completed", {"language": language, "elapsed_s": elapsed})
    print(f"[Planner] Language: {language} ({elapsed}s)")

    return state
