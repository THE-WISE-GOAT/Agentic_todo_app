# Things to do

A small todo app. FastAPI and SQLite behind it, plain HTML/CSS/JS in front, and an optional
Ollama agent that understands sentences like "move the essay to Friday".

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open <http://localhost:8000>. The database and tables are created on first start.

Use the commands above to install dependencies and start the server.

## The Ask tab

The command bar needs [Ollama](https://ollama.com) running locally:

```bash
ollama serve
ollama pull qwen2.5:3b
```

Everything else in the app works without it. If Ollama is down, the Ask tab says so instead of
hanging, and you can add or edit tasks by hand.

Example commands:

- `add call the dentist tomorrow, high priority`
- `mark the essay as done`
- `move groceries to Personal`
- `delete everything under watchlist`
- `clear all`

## Configuration

Copy `.env.example` to `.env` if you want to change the database path or the model:

| Variable | Default | Used for |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./todos.db` | Database location |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Agent host |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Model name |
| `CORS_ORIGINS` | empty | Extra allowed origins, comma-separated |

## Layout

```
backend/
  main.py         app setup, static files
  config.py       environment settings
  database.py     engine and sessions
  models.py       Todo table and enums
  schemas.py      request/response models
  services.py     queries shared by the API and agent
  routes/         todos, agent and system endpoints
  agent/
    graph.py      LangGraph agent and Ollama check
    tools.py      tools the agent calls
frontend/
  index.html
  assets/         app.css, app.js, favicon
```

## API

All endpoints live under `/api`. Interactive docs at `/api/docs`.

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/todos` | `status`, `category`, `q`, `sort` params |
| POST | `/api/todos` | `text`, optional `priority`, `category`, `due_date` |
| GET | `/api/todos/{id}` | |
| PATCH | `/api/todos/{id}` | Send only the fields you change |
| DELETE | `/api/todos/{id}` | |
| DELETE | `/api/todos` | Clears everything; `?status=done` clears only finished tasks |
| POST | `/api/agent/command` | `{"command": "..."}` |
| GET | `/api/stats` | totals for the header |
| GET | `/api/meta` | priorities, categories, agent status |
| GET | `/api/health` | database and agent check |

`due_date` is a plain `YYYY-MM-DD` date. `created_at` is local time.

## Notes

- The SQLite file is `todos.db` in the repo root and is gitignored. Delete it to start over.
- Deleting a task from the UI shows an undo toast for five seconds.
- Keyboard: `n` for a new task, `/` to search, `Esc` to cancel an edit.
