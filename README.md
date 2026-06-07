# NoCodeCode - Multi-agent AI Coding System

**Tell an AI to code for you.** Describe what you want, and the agent plans, builds, tests, and debugs it—automatically.

## What is NoCodeCode?

NoCodeCode is an AI-powered coding assistant that handles the entire development workflow. Instead of writing code yourself, you describe your requirements and the agent:

- **Plans** the implementation
- **Codes** the solution
- **Executes** it
- **Debugs** errors
- **Tests** the result

## Agents

| Agent | What it does |
|-------|-------------|
| **Planner** | Breaks down your task into steps |
| **Coder** | Writes clean, functional code |
| **Executor** | Runs the code and captures output |
| **Debugger** | Finds and fixes errors |
| **Tester** | Creates and runs tests |

## Memory & Sessions

- **Sessions**: Each conversation is saved. Resume where you left off anytime.
- **Short-term memory**: Current session checkpoints for context.
- **Long-term memory**: Preferences, past tasks, and chat history.

## Quick Start

### 1. Create and activate a virtual environment
```bash
python -m venv nocode
source nocode/bin/activate   # Windows: nocode\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
```

Then open `.env` and fill in your API keys (see [Environment Variables](#environment-variables) below).

### 4. Run the agent
```bash
python main.py
```

### 5. Describe what you want
```
You: "Create a function to calculate fibonacci numbers"

Agent will:
1. Plan the approach
2. Write the code
3. Test it
4. Show you the result
```

## Project Structure

```
├── main.py                # Entry point
├── agents/                # Planner, Coder, Executor, Debugger, Tester
├── graph/                 # LangGraph workflow orchestration
├── memory/                # Session and preference storage
├── observability/
│   └── tracer.py          # Structured logging + Langfuse tracing
├── logs/                  # JSON log files written at runtime
├── state.py               # Shared agent state definition
└── requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and update the values.

### LLM Provider

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes (or OpenAI) | Google Gemini API key — get one at [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `OPENAI_API_KEY` | Optional | OpenAI API key — used if Google key is absent or a GPT model is selected |
| `VERBOSE` | Optional | Set `true` for verbose per-agent terminal output (default: `false`) |
| `MODEL` | Optional | Override the default model (e.g. `gemini-1.5-flash`, `gpt-4o`) |

### Observability — Langfuse

Langfuse is optional. When configured, every LLM call is traced with token counts, latency, and full prompt/response history in the Langfuse dashboard.

| Variable | Description |
|----------|-------------|
| `LANGFUSE_PUBLIC_KEY` | Public key from your Langfuse project (starts with `pk-lf-`) |
| `LANGFUSE_SECRET_KEY` | Secret key from your Langfuse project (starts with `sk-lf-`) |
| `LANGFUSE_HOST` | Only needed for self-hosted Langfuse; leave unset for cloud |

**How to get Langfuse keys:**
1. Sign up (free) at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a project
3. Go to **Settings → API Keys**
4. Copy the **Public Key** and **Secret Key** into your `.env`

If the keys are missing, the app logs a `langfuse_disabled` event and continues normally — tracing is silently skipped.

## Observability

NoCodeCode has a two-layer observability system in `observability/tracer.py`:

### Structured JSON logging

Every agent event is written as a JSON line to both the terminal and `logs/agent.log`:

```json
{"time": "2025-06-07T10:00:00", "agent": "planner", "event": "completed", "data": {"language": "python"}}
```

You can grep and filter these logs to analyse agent behaviour over time.

### Langfuse tracing (optional)

When Langfuse keys are present, a `CallbackHandler` is attached to every LangChain call. This records:

- Full prompt and response text
- Token usage and cost
- Latency per agent
- Session grouping (so you can trace a full multi-turn conversation)

View traces at [cloud.langfuse.com](https://cloud.langfuse.com) under your project dashboard.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Start coding with AI. It's that simple.**
