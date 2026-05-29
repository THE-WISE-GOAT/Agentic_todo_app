# Todo App — Agentic AI Workshop Project

## Overview
This repository contains a lightweight, functional Todo application developed as a hands-on project during an **Agentic AI Workshop**. 

The application architecture cleanly decouples standard, deterministic CRUD features from an intelligent AI layer. It features a robust **FastAPI backend**, a modern and minimal **Streamlit frontend**, and an advanced **LangGraph-driven orchestrator** that uses a local Large Language Model (LLM) to convert unstructured natural language commands into structured database operations.

---

## Architectural Deep-Dive: How the Agentic AI Works
Instead of relying on rigid, regex-based parsing, this project implements a dynamic **ReAct (Reasoning and Action) Architecture** using `langgraph`.

```mermaid
flowchart TD
	U[User Command] --> LG[LangGraph State]
	LG --> LLM[LLM Agent Node (Qwen2.5)]
	LLM --> D{Decides next move}
	D -->|Direct Answer| End[End]
	D -->|Tool Call Triggered| T[ToolNode Execution\n(Create, Update, Complete, etc.)]
	T --> LLM
	T --> End
```

1. **State Engine (`TodoAgentState`):** The app builds a standard state track (`messages`) passed from node to node using LangGraph’s message reducers.
2. **Contextual Awareness:** Before the user's message reaches the LLM, a system message injects the current live state of the database (`todos.json`). This gives the model explicit context so it can map text commands (e.g., *"complete the shopping task"*) to numerical database identifiers (e.g., `ID 03`).
3. **The ReAct Loop (`should_continue`):** The LLM parses the command and determines whether it can reply directly or if it requires a tool invocation. If it determines a tool is needed, it dynamically calls one of our custom tool bindings (like `create_todo_tool` or `complete_todo_tool`).
4. **Reactive Execution Loop:** The execution jumps to `ToolNode`, runs the native Python code affecting the data store, and loops back into the agent node to evaluate success and reply cleanly to the frontend.

*Because of lazy-loading protocols implemented in the FastAPI routes, the core database engine remains fully decoupled from the AI layer. If Ollama or your LLM libraries are offline, the standard UI buttons and endpoints remain fully operational.*

---

## What This Repository Contains
* **`backend.py`**: A FastAPI application housing the RESTful CRUD endpoints and JSON file storage handling. It provides a dedicated `/todos/process-command` pipeline for the agentic layer.
* **`frontend.py`**: A dark-themed, sleek Streamlit user interface styling custom inline cards, dynamic metric graphs, and a natural language instruction command dock.
* **`todo_graph.py`**: The definitive Agent core. Configures tool definitions (`@tool`), ties them to a compiled LangGraph state diagram, handles memory checkpoints (`MemorySaver`), and orchestrates inference with the local LLM.
* **`todos.json`**: The lightweight, flat-file local database layout tracking active IDs, tasks, creation timestamps, and completion state metrics.
* **`requirements.txt`**: Complete workspace python library pinning.

---

## Prerequisites
* **Python Engine:** Version `3.10` or newer (Developed and tested using `Python 3.12`)
* **Local LLM Runtime:** [Ollama](https://ollama.com/) (Required exclusively for natural language processing functions)

---

## Environment & Model Setup

### 1. Initialize Virtual Environment
Navigate to your project root folder and establish a localized python environment:
```bash
python3 -m venv .venv
source .venv/bin/activate

```

### 2. Install Project Dependencies

Upgrade your package installer and load package configurations:

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

### 3. Initialize the Ollama Brain Model

Ensure your local Ollama background server instance is active. Pull the specific model utilized throughout our workshop exercises:

```bash
ollama pull qwen2.5:3b

```

> **Note:** If you run into an engine error claiming `listen tcp 127.0.0.1:11434: bind: address already in use`, it means the native desktop Ollama app is already serving connections in the background. You do **not** need to execute a manual terminal `ollama serve`. You are ready to launch the app directly.

---

## Running the Application

To run the application, you must launch both the backend processing engine and the frontend visual layer in separate concurrent terminal windows. Ensure your virtual environment (`.venv`) is active in both.

### Step A: Fire Up the FastAPI Backend

```bash
uvicorn backend:app --reload --port 8000

```

The application backend will spin up local servers at `http://localhost:8000`. You can inspect documentation and test endpoints directly at `http://localhost:8000/docs`.

### Step B: Launch the Streamlit Frontend UI

In a fresh window or terminal tab, start the user portal:

```bash
streamlit run frontend.py

```

The browser will automatically load the frontend dashboard interface at `http://localhost:8501`.

---

## Supported Natural Language Controls

You can type unstructured human statements directly into the input bar on the left panel of the UI. The LangGraph agent seamlessly maps inputs to deterministic behaviors:

* **Creation Operations:** `"add download latest workspace data"`, `"remind me to call the landlord tomorrow"`
* **State Updates:** `"complete #03"`, `"mark todo 4 as done"`
* **Text Modifications:** `"edit #5 to read review matching slides"`
* **Destructive Deletion:** `"remove #02"`, `"delete all"`

---

## Troubleshooting Guide

* **Streamlit throws Connection Errors:** Double-check that your `uvicorn` engine is actively executing on port `8000`. If you configure an alternate address or port, match the `API_URL` global address string on line `9` of `frontend.py`.
* **Ollama Connection/Model Errors:** Run `ollama list` in your shell terminal to verify that `qwen2.5:3b` is downloaded. If you want to drop or change models, update the instantiation inside `todo_graph.py` on line `107` (`llm = ChatOllama(model="YOUR_MODEL")`).
* **Stuck Port 11434 Issues:** If you need to forcefully restart your Ollama background daemon on macOS, quit the application using the top menu-bar icon, or issue a terminal shutdown sequence via AppleScript:
```bash
osascript -e 'quit app "Ollama"'

```
