from curses import raw

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
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
    print("\n[Coder] Generating code...")
    response = chain.invoke({
        "task": state["task"],
        "plan": state["plan"],
        "language": state["language"],
        "error": state.get("error_message") or "None"
    })


    #code = response.content.strip()
    code = extract_text(response)

    if code.startswith("```"):
        lines = code.splitlines()
        code = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    state["code"] = code
    state["user_approved"] = False
    print("\n[Coder] Code generated successfully.")
    return state