from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from dotenv import load_dotenv
from utils import extract_text
 
load_dotenv()
 
MAX_DEBUG_ATTEMPTS = 3
 
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
 
PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert debugger. You receive broken code and an error message.
Fix the code and return ONLY the corrected code — no explanation, no markdown, no backticks.
Make minimal changes. Keep the original logic intact."""),
    ("human", """Original task: {task}
 
Broken code:
{code}
 
Error message:
{error}
 
Fixed code:""")
])
 
chain = PROMPT | llm
 
 
def run_debugger(state: AgentState) -> AgentState:
    attempts = state.get("debug_attempts", 0)
 
    if attempts >= MAX_DEBUG_ATTEMPTS:
        print(f"\n[Debugger] ❌ Reached max debug attempts ({MAX_DEBUG_ATTEMPTS}). Giving up.")
        state["is_fixed"] = False
        return state
 
    print(f"\n[Debugger] Attempt {attempts + 1}/{MAX_DEBUG_ATTEMPTS} — fixing error...")
    print(f"[Debugger] Error: {state['error_message']}")
 
    response = chain.invoke({
        "task": state["task"],
        "code": state["code"],
        "error": state["error_message"]
    })
 
    #fixed_code = response.content.strip()
    fixed_code = extract_text(response)
    if fixed_code.startswith("```"):
        lines = fixed_code.splitlines()
        fixed_code = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
 
    state["code"] = fixed_code
    state["debug_attempts"] = attempts + 1
    state["is_fixed"] = True
    state["user_approved"] = False  # require approval again after fix
 
    print("[Debugger] Code patched. Will re-run.")
    return state