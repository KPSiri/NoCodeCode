import subprocess
import tempfile
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from dotenv import load_dotenv
 
load_dotenv()
 
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
 
PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a test engineer. Write test cases for the given code.
 
Rules:
- Output ONLY raw Python test code, no markdown, no backticks
- Copy the function(s) from the solution inline — do not use import
- Write 4-6 tests covering: happy path, edge cases, boundary values
- Each test is a function starting with test_
- Use only assert statements — no pytest, no unittest
- Tests must be completely standalone and runnable as a plain Python script
"""),
    ("human", """Task: {task}
 
Code to test:
{code}
 
Write the test file:""")
])
 
chain = PROMPT | llm
 
 
def ask_test_permission(test_code: str) -> bool:
    print("\n" + "=" * 60)
    print("AGENT WANTS TO RUN TESTS")
    print("=" * 60)
    print(test_code)
    print("-" * 60)
    print("This will run on your local machine inside a temp file.")
    print("The file is deleted immediately after execution.")
    answer = input("\nAllow test execution? (yes/no): ").strip().lower()
    return answer in ("yes", "y")
 
 
def run_tests_locally(test_code: str) -> dict:
    """Combine solution + tests + a simple runner, execute locally."""
 
    # append a simple manual test runner at the bottom
    # (no pytest needed — just calls each test_ function and tracks pass/fail)
    runner = """
# ── simple test runner ──────────────────────────────────────
import traceback
passed = 0
failed = 0
all_tests = [name for name in list(globals().keys()) if name.startswith("test_")]
for test_name in all_tests:
    try:
        globals()[test_name]()
        print(f"  PASS: {test_name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {test_name} — {e}")
        failed += 1
print(f"\\nResults: {passed} passed, {failed} failed")
"""
 
    full_code = test_code + runner
 
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False
    ) as f:
        f.write(full_code)
        tmp_path = f.name
 
    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=15
        )
 
        output = result.stdout.strip()
        stderr = result.stderr.strip()
 
        passed = output.count("PASS:")
        failed = output.count("FAIL:")
 
        return {
            "passed": passed,
            "failed": failed,
            "output": output,
            "stderr": stderr,
            "success": result.returncode == 0
        }
 
    except subprocess.TimeoutExpired:
        return {
            "passed": 0,
            "failed": 0,
            "output": "",
            "stderr": "Tests timed out after 15 seconds.",
            "success": False
        }
 
    except Exception as e:
        return {
            "passed": 0,
            "failed": 0,
            "output": "",
            "stderr": str(e),
            "success": False
        }
 
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
 
 
def run_tester(state: AgentState) -> AgentState:
    print("\n[Tester] Generating test cases...")
 
    response = chain.invoke({
        "task": state["task"],
        "code": state["code"]
    })
 
    raw = response.content
    test_code = raw[0]["text"] if isinstance(raw, list) else raw
    test_code = test_code.strip()
 
    # strip markdown fences if model adds them
    if test_code.startswith("```"):
        lines = test_code.splitlines()
        test_code = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
 
    state["test_code"] = test_code
 
    approved = ask_test_permission(test_code)
    if not approved:
        print("[Tester] Test execution denied by user.")
        state["test_result"] = {
            "passed": 0,
            "failed": 0,
            "output": "User denied test execution.",
            "success": False
        }
        return state
 
    print("[Tester] Running tests locally...")
 
    result = run_tests_locally(test_code)
    state["test_result"] = result
 
    if result["output"]:
        print(result["output"])
    if result["stderr"]:
        print(f"[Tester] Stderr:\n{result['stderr']}")
 
    print(f"[Tester] {result['passed']} passed, {result['failed']} failed")