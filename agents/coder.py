from curses import raw
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from observability.tracer import log, get_langfuse_handler
from dotenv import load_dotenv
from utils import extract_text

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert software engineer. Write clean, working code based on the plan.
 
Rules:
- Output ONLY the raw code, no markdown, no backticks, no explanation
- Include helpful inline comments
- Handle edge cases from the plan
- Make it runnable as a standalone script
- If Python, include a main() function and if __name__ == '__main__': main()
"""),
    ("human", """Task: {task}
     
     Plan: 
     {plan}

     Language: {language}

     Previous error to fix (if any):
     {error}

     Write the complete code:""")
    ])

chain = PROMPT | llm

def run_coder(state: AgentState) -> AgentState:
    log("coder", "started", {"language": state.get("language"), "is_retry": bool(state.get("error_message"))})
    print("\n[Coder] Writing code...")
 
    start = time.time()
 
    handler = get_langfuse_handler(
        session_id=state.get("session_id", "unknown"),
        task=state["task"]
    )
 
    invoke_config = {"callbacks": [handler]} if handler else {}
    response = chain.invoke(
        {
            "task":     state["task"],
            "plan":     state["plan"],
            "language": state["language"],
            "error":    state.get("error_message") or "None"
        },
        config=invoke_config
    )

    #code = response.content.strip()
    code = extract_text(response)

    if code.startswith("```"):
        lines = code.splitlines()
        code = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    elapsed = round(time.time() - start, 2)
    
    state["code"] = code
    state["user_approved"] = False


    log("coder", "completed", {"elapsed_s": elapsed, "code_lines": len(code.splitlines())})
    print(f"[Coder] Code ready ({elapsed}s, {len(code.splitlines())} lines)")
    
    return state