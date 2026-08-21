# Agentic Todo App

A production-ready, AI-powered todo application with a FastAPI backend, Streamlit frontend, and LangGraph agentic layer.

## Architecture

```
├── backend/
│   ├── main.py          # FastAPI REST API
│   ├── models.py        # SQLModel schemas
│   ├── database.py      # SQLite engine & session management
│   └── agent/
│       ├── graph.py     # LangGraph state machine
│       └── tools.py     # Agent tool implementations (with fuzzy matching)
├── frontend/
│   ├── app.py           # Streamlit UI
│   └── assets/
│       └── style.css    # Dark theme stylesheet
├── todos.db             # SQLite database (auto-created)
├── requirements.txt
└── README.md
```

## Prerequisites

- **Python:** 3.10+
- **Ollama:** Local LLM runtime (for natural language processing)

## Setup

### 1. Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Ollama Model

```bash
ollama pull qwen2.5:3b
```

## Running the Application

### Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
streamlit run app.py
```

The app will be available at `http://localhost:8501`. API docs at `http://localhost:8000/docs`.

## Features

- **CRUD Operations:** Create, read, update, delete todos via UI or API
- **AI Agent:** Natural language command processing via LangGraph + Ollama
- **Fuzzy Matching:** Smart text-based search for update/delete commands
- **Rich Schema:** Priority, due dates, categories
- **Filtering:** Filter todos by category and completion status
- **Dark Theme:** Sleek, minimal UI

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/todos` | List all todos |
| POST | `/todos` | Create a todo |
| GET | `/todos/{id}` | Get a specific todo |
| PUT | `/todos/{id}` | Update a todo |
| DELETE | `/todos/{id}` | Delete a todo |
| DELETE | `/todos` | Delete all todos |
| POST | `/todos/process-command` | Process natural language command |

## Natural Language Commands

- **Create:** `"add buy groceries"`, `"remind me to call the dentist tomorrow"`
- **Complete:** `"complete #1"`, `"mark todo 2 as done"`
- **Update:** `"edit #1 to read matching slides"`
- **Delete:** `"remove eggs"`, `"delete #3"`, `"delete all"`
- **Compound:** `"add X and delete Y"`
