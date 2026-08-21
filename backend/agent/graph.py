"""
LangGraph workflow for processing natural language todo commands using reactive tool calling.
"""
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage

from backend.agent.tools import tools


class TodoAgentState(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOllama(model="qwen2.5:3b")


def get_todo_graph():
    memory = MemorySaver()

    def system_prompt(state: TodoAgentState) -> list:
        from backend.agent.tools import list_todos_tool
        todos_result = list_todos_tool.invoke({})
        todos_context = "\n".join(
            f"ID {t['id']}: {t['text']} ({'completed' if t.get('completed') else 'pending'}) "
            f"[priority: {t.get('priority', 'Medium')}, category: {t.get('category', 'General')}]"
            for t in todos_result.get("todos", [])
        )
        system_msg = (
            "You are a helpful todo assistant. You can execute multiple actions in sequence "
            "to handle compound commands (e.g. 'add X and delete Y').\n\n"
            "Current todos:\n"
            f"{todos_context}\n\n"
            "Rules:\n"
            "- When the user refers to a todo by description (not ID), find the closest matching ID from the list above.\n"
            "- Use fuzzy matching mentally: accept approximate text matches.\n"
            "- For creation, use create_todo_tool with optional priority, due_date, category.\n"
            "- For updates, use update_todo_tool with the identifier and the fields to change.\n"
            "- For deletion, use delete_todo_tool with an ID or text.\n"
            "- For completion, use complete_todo_tool with an ID or text.\n"
            "- Always use the appropriate tool. Never pretend to perform an action without calling a tool.\n"
            "- If a command is ambiguous, make your best guess and proceed."
        )
        return [("system", system_msg)]

    return create_react_agent(
        model=llm,
        tools=tools,
        state_schema=TodoAgentState,
        messages_modifier=system_prompt,
        checkpointer=memory,
    )


def process_command_with_graph(command: str, thread_id: str = "default") -> dict:
    graph = get_todo_graph()
    initial_state = {"messages": [("user", command)]}
    config = {"configurable": {"thread_id": thread_id}}
    final_state = graph.invoke(initial_state, config)

    results = []
    for msg in final_state.get("messages", []):
        if isinstance(msg, ToolMessage):
            content = msg.content
            if isinstance(content, dict):
                results.append(content)
            elif isinstance(content, str):
                try:
                    import json
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        results.append(parsed)
                    else:
                        results.append({"success": True, "message": content})
                except Exception:
                    results.append({"success": True, "message": str(content)})

    if results:
        success = all(r.get("success", False) for r in results)
        messages = [r.get("message", "") for r in results if r.get("message")]
        combined_message = " | ".join(messages) if messages else "Done."
        return {
            "success": success,
            "message": combined_message,
            "results": results,
            "todo": results[-1].get("todo") if results else None,
            "todos": results[-1].get("todos") if results else None,
            "count": results[-1].get("count") if results else None,
        }

    final_message = final_state.get("messages", [])[-1]
    if hasattr(final_message, "content"):
        content = final_message.content
        return {"success": True, "message": str(content)}

    return {"success": False, "message": "No result"}
