import subprocess
import tempfile
import os
from state import AgentState
from dotenv import load_dotenv
 
load_dotenv()
 
 
def ask_user_permission(code: str, language: str) -> bool:
    """Show the code to the user and ask if they want to run it."""
    print("\n" + "=" * 60)
    print("AGENT WANTS TO EXECUTE CODE")
    print("=" * 60)
    print(f"Language: {language}")
    print("-" * 60)
    print(code)
    print("-" * 60)
    print("This will run on your local machine inside a temp file.")
    print("The file is deleted immediately after execution.")
    answer = input("\nAllow execution? (yes/no): ").strip().lower()
    return answer in ("yes", "y")
 
 
def run_code_locally(code: str, language: str) -> dict:
    """Write code to a temp file, run it, return stdout/stderr, delete the file."""
 
    if language not in ("python", "python3"):
        return {
            "stdout": "",
            "stderr": f"Local execution currently supports Python only. Got: {language}",
            "success": False
        }
 
    # write code to a temporary .py file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False
    ) as f:
        f.write(code)
        tmp_path = f.name
 
    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,   # captures stdout and stderr separately
            text=True,             # returns strings instead of bytes
            timeout=30             # kill the process if it runs more than 10s
        )
 
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "success": result.returncode == 0   # 0 = no error
        }
 
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Code timed out after 30 seconds.",
            "success": False
        }
 
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Unexpected error during execution: {str(e)}",
            "success": False
        }
 
    finally:
        # always delete the temp file, even if an exception occurred
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
 
 
def run_executor(state: AgentState) -> AgentState:
    print("\n[Executor] Requesting permission to run code...")
 
    approved = ask_user_permission(state["code"], state["language"])
 
    if not approved:
        print("[Executor] Execution denied by user.")
        state["user_approved"] = False
        state["execution_result"] = {
            "stdout": "",
            "stderr": "User denied execution.",
            "success": False
        }
        return state
 
    state["user_approved"] = True
    print("[Executor] Running code locally...")
 
    result = run_code_locally(state["code"], state["language"])
    state["execution_result"] = result
    state["error_message"] = result["stderr"] if not result["success"] else None
 
    if result["success"]:
        print("[Executor] Success.")
        if result["stdout"]:
            print(f"[Executor] Output:\n{result['stdout']}")
    else:
        print(f"[Executor] Error:\n{result['stderr']}")
 
    return state
 