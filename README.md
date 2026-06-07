# 🚀 NoCodeCode - Multi-agent system

**Tell an AI to code for you.** Describe what you want, and the agent plans, builds, tests, and debugs it—automatically.

## 🎯 What is NoCodeCode?

NoCodeCode is an AI-powered coding assistant that handles the entire development workflow. Instead of writing code yourself, you describe your requirements and the agent:
- 📋 **Plans** the implementation
- 💻 **Codes** the solution
- ▶️ **Executes** it
- 🐛 **Debugs** errors
- ✅ **Tests** the result

## 🤖 Meet the Agents

| Agent | What it does |
|-------|-------------|
| **Planner** | Breaks down your task into steps |
| **Coder** | Writes clean, functional code |
| **Executor** | Runs the code and captures output |
| **Debugger** | Finds and fixes errors |
| **Tester** | Creates and runs tests |

Executor and Tester agents ask for human approval before running the code on their local terminal.

## 🧠 Memory & Sessions

- **Sessions**: Each conversation is saved. Resume where you left off anytime.
- **Short-term Memory**: Current session checkpoints for context.
- **Long-term Memory**: Preferences, past tasks, and chat history.

## 📝 Observability & Logging

This is optional step (The code is present in observability-logging branch)
- Every LLM call is logged and stored in logs/ folder 
- Every LLM call is traced with token counts, latency, and full prompt/response history in the Langfuse dashboard.

## 🏃 Quick Start

### 1. Create and Activate Virtual Environment
```bash
python -m venv nocode
source nocode/bin/activate
```

### 2. Set Up API Keys
```bash
cp .env.example .env
# Edit .env and add your Google GenAI or OpenAI API key
```

### 3. Run the Agent
```bash
python main.py
```

### 4. Describe What You Want
```
You: "Create a function to calculate fibonacci numbers"

Agent will:
1. Plan the approach
2. Write the code
3. Test it
4. Show you the result
```

## 📁 Project Structure

```
├── main.py              # Start here
├── agents/              # Planner, Coder, Executor, Debugger, Tester
├── graph/               # Workflow orchestration
├── memory/              # Session and preference storage
└── state.py             # Agent state management
```

## ⚙️ Environment Variables

Create `.env` from `.env.example`:
```env
GOOGLE_API_KEY=your_key_here
VERBOSE=false
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Start coding with AI. It's that simple.**
