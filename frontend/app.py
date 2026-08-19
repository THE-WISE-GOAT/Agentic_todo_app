import streamlit as st
import requests
from typing import List, Dict, Optional
import time
from datetime import datetime
import os

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="things to do",
    page_icon="◉",
    layout="wide",
)

css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
with open(css_path, "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get(path: str):
    return requests.get(f"{API_URL}{path}", timeout=8)


def _post(path: str, **kwargs):
    return requests.post(f"{API_URL}{path}", timeout=30, **kwargs)


def _put(path: str, **kwargs):
    return requests.put(f"{API_URL}{path}", timeout=8, **kwargs)


def _delete(path: str):
    return requests.delete(f"{API_URL}{path}", timeout=8)


def get_todos() -> List[Dict]:
    try:
        r = _get("/todos")
        if r.status_code == 200:
            return r.json()
        st.error(f"Backend returned {r.status_code}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("⚠ Can't reach the backend. Start it with: `cd backend && uvicorn main:app --reload`")
        return []
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return []


def update_todo(
    todo_id: int,
    text: Optional[str] = None,
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    category: Optional[str] = None,
) -> bool:
    try:
        data: Dict = {}
        if text is not None:
            data["text"] = text
        if completed is not None:
            data["completed"] = completed
        if priority is not None:
            data["priority"] = priority
        if due_date is not None:
            data["due_date"] = due_date
        if category is not None:
            data["category"] = category
        r = _put(f"/todos/{todo_id}", json=data)
        return r.status_code == 200
    except Exception as e:
        st.error(str(e))
        return False


def delete_todo(todo_id: int) -> bool:
    try:
        return _delete(f"/todos/{todo_id}").status_code == 200
    except Exception as e:
        st.error(str(e))
        return False


def delete_all_todos() -> bool:
    try:
        return _delete("/todos").status_code == 200
    except Exception as e:
        st.error(str(e))
        return False


def process_command(command: str, thread_id: str = "default") -> Optional[Dict]:
    try:
        r = _post(
            "/todos/process-command",
            params={"command": command, "thread_id": thread_id},
        )
        if r.status_code == 200:
            return r.json()
        st.error(f"Command endpoint returned {r.status_code}: {r.text[:200]}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("⚠ Can't reach the backend.")
        return None
    except Exception as e:
        st.error(f"Command error: {e}")
        return None


def parse_command_response(resp: Optional[Dict]) -> tuple[bool, str]:
    if resp is None:
        return False, "No response from backend."
    top_msg: str = resp.get("message", "")
    inner: Dict = resp.get("result") or {}
    inner_ok: bool = bool(inner.get("success", False))
    inner_msg: str = inner.get("message", "")
    success = inner_ok
    message = (top_msg or inner_msg or "Done.").strip()
    return success, message


# ─────────────────────────────────────────────────────────────────────────────
# SMALL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def fmt_id(n: int) -> str:
    return f"#{n:02d}"


def day_greeting() -> str:
    h = datetime.now().hour
    if h < 12:
        return "morning"
    if h < 17:
        return "afternoon"
    return "evening"


def relative_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        diff = datetime.now() - dt
        s = int(diff.total_seconds())
        if s < 60:
            return "just now"
        if s < 3600:
            return f"{s // 60}m ago"
        if s < 86400:
            return f"{s // 3600}h ago"
        if s < 7 * 86400:
            return f"{s // 86400}d ago"
        return dt.strftime("%d %b")
    except Exception:
        return ""


def format_due_date(due_date: Optional[str]) -> str:
    if not due_date:
        return ""
    try:
        dt = datetime.fromisoformat(due_date)
        return dt.strftime("%d %b %Y")
    except Exception:
        return due_date


PRIORITY_BADGE_CLASS = {
    "High": "badge-priority-high",
    "Medium": "badge-priority-medium",
    "Low": "badge-priority-low",
}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    for key, val in [
        ("last_msg", None),
        ("last_ok", None),
        ("pending_rerun", False),
        ("filter_category", "All"),
        ("filter_status", "All"),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val

    now = datetime.now()
    today = now.strftime("%A, %d %b")
    time_str = now.strftime("%H:%M")

    todos = get_todos()
    total = len(todos)

    # Apply filters
    filtered = []
    cat_filter = st.session_state.get("filter_category", "All")
    status_filter = st.session_state.get("filter_status", "All")
    for t in todos:
        if cat_filter != "All" and t.get("category") != cat_filter:
            continue
        if status_filter == "Pending" and t.get("completed"):
            continue
        if status_filter == "Completed" and not t.get("completed"):
            continue
        filtered.append(t)

    done_count = sum(1 for t in todos if t.get("completed", False))
    pending = total - done_count
    filtered_total = len(filtered)

    # ── HEADER ─────────────────────────────────────────────────────────────
    st.markdown(f"""
        <div class="app-header">
            <div class="app-title">
                good {day_greeting()},<br><em>here's what's on.</em>
            </div>
            <div class="app-meta">
                <div class="app-date">{today}</div>
                <div class="app-date">{time_str}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── TWO-COLUMN LAYOUT ──────────────────────────────────────────────────
    left, right = st.columns([1, 1.7], gap="large")

    # ──────────────────────────────────────────────────────────────────────
    # LEFT — command + stats
    # ──────────────────────────────────────────────────────────────────────
    with left:
        if total > 0:
            pct = int(done_count / total * 100)
            st.markdown(f"""
                <div class="stats-grid">
                    <div class="stat-card">
                        <span class="stat-num all">{total}</span>
                        <span class="stat-label">total</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-num">{pending}</span>
                        <span class="stat-label">left</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-num">{done_count}</span>
                        <span class="stat-label">done</span>
                    </div>
                </div>
                <div class="progress-wrap">
                    <div class="progress-label">
                        <span>progress</span>
                        <span>{pct}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width:{pct}%"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Command bar
        st.markdown('<span class="cmd-label">tell it what to do</span>', unsafe_allow_html=True)

        c_input, c_btn = st.columns([5, 1])
        with c_input:
            prompt = st.text_input(
                "command",
                placeholder="add call the dentist",
                label_visibility="collapsed",
                key="cmd_input",
            )
        with c_btn:
            run = st.button("→", type="primary", use_container_width=True, key="cmd_run")

        st.markdown("""
            <div class="cmd-hint">
                <span>add …</span>
                <span>complete #</span>
                <span>edit # to …</span>
                <span>remove #</span>
                <span>delete all</span>
            </div>
        """, unsafe_allow_html=True)

        # ── Execute NL command with explicit loading state
        if run and prompt:
            with st.spinner("thinking…"):
                resp = process_command(prompt.strip())
            ok, msg = parse_command_response(resp)
            st.session_state["last_ok"] = ok
            st.session_state["last_msg"] = msg
            time.sleep(0.25)
            st.rerun()

        # ── Show last command result
        if st.session_state.get("last_msg"):
            if st.session_state.get("last_ok"):
                st.success(st.session_state["last_msg"])
            else:
                st.warning(st.session_state["last_msg"])

        # ── Danger zone
        if total > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("danger zone"):
                st.markdown(
                    '<span style="font-size:0.8rem;color:#4a4138;">'
                    'removes everything, permanently.</span>',
                    unsafe_allow_html=True,
                )
                if st.button("clear all todos", key="clear_all"):
                    delete_all_todos()
                    st.session_state["last_msg"] = "All todos cleared."
                    st.session_state["last_ok"] = True
                    time.sleep(0.25)
                    st.rerun()

    # ──────────────────────────────────────────────────────────────────────
    # RIGHT — todo list
    # ──────────────────────────────────────────────────────────────────────
    with right:
        # Filters
        categories = ["All"] + sorted({t.get("category", "General") for t in todos})
        statuses = ["All", "Pending", "Completed"]

        st.markdown('<span class="filter-label">filter</span>', unsafe_allow_html=True)
        f1, f2 = st.columns(2)
        with f1:
            st.markdown('<span style="font-size:0.65rem;color:#a09890;font-family:\'DM Mono\',monospace;">category</span>', unsafe_allow_html=True)
            cat_cols = st.columns(len(categories), gap="small")
            for idx, cat in enumerate(categories):
                with cat_cols[idx]:
                    if st.button(
                        cat,
                        key=f"cat_{cat}",
                        type="primary" if st.session_state.get("filter_category", "All") == cat else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state["filter_category"] = cat
                        time.sleep(0.1)
                        st.rerun()

        with f2:
            st.markdown('<span style="font-size:0.65rem;color:#a09890;font-family:\'DM Mono\',monospace;">status</span>', unsafe_allow_html=True)
            stat_cols = st.columns(len(statuses), gap="small")
            for idx, sts in enumerate(statuses):
                with stat_cols[idx]:
                    if st.button(
                        sts,
                        key=f"stat_{sts}",
                        type="primary" if st.session_state.get("filter_status", "All") == sts else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state["filter_status"] = sts
                        time.sleep(0.1)
                        st.rerun()

        st.markdown(f"""
            <div class="list-header">
                <span class="list-title">the list</span>
                <span class="list-count">{filtered_total} item{"s" if filtered_total != 1 else ""}</span>
            </div>
        """, unsafe_allow_html=True)

        if not filtered:
            st.markdown("""
                <div class="empty-state">
                    <span class="empty-icon">◎</span>
                    <span class="empty-text">nothing here yet — add something on the left</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            for todo in filtered:
                tid = todo["id"]
                text = todo.get("text", "")
                is_done = bool(todo.get("completed", False))
                created = relative_time(todo.get("created_at", ""))
                priority = todo.get("priority", "Medium")
                category = todo.get("category", "General")
                due_date = todo.get("due_date")

                card_cls = "todo-card done" if is_done else "todo-card"
                txt_cls = "todo-text done" if is_done else "todo-text"
                dot = "✓" if is_done else "·"

                prio_cls = PRIORITY_BADGE_CLASS.get(priority, "badge-priority-medium")
                due_str = format_due_date(due_date) if due_date else ""

                col_card, col_tog, col_ed, col_del = st.columns([6.5, 0.6, 0.6, 0.6])

                with col_card:
                    badges_html = ""
                    badges_html += f'<span class="todo-badge {prio_cls}">{priority}</span>'
                    badges_html += f'<span class="todo-badge badge-category">{category}</span>'
                    if due_str:
                        badges_html += f'<span class="todo-badge badge-due">due {due_str}</span>'

                    st.markdown(f"""
                        <div class="{card_cls}">
                            <div class="todo-meta">{fmt_id(tid)} &nbsp;{dot}&nbsp; {created}</div>
                            <div class="{txt_cls}">{text}</div>
                            <div class="todo-details">{badges_html}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with col_tog:
                    tog_lbl = "✓" if not is_done else "↩"
                    tog_tip = "mark done" if not is_done else "mark undone"
                    if st.button(tog_lbl, key=f"tog_{tid}", help=tog_tip):
                        if update_todo(tid, completed=not is_done):
                            st.session_state["last_msg"] = (
                                f"Marked '{text}' as {'done' if not is_done else 'pending'}."
                            )
                            st.session_state["last_ok"] = True
                        time.sleep(0.25)
                        st.rerun()

                with col_ed:
                    if st.button("✎", key=f"ed_{tid}", help="edit"):
                        currently = st.session_state.get(f"editing_{tid}", False)
                        for t in todos:
                            st.session_state[f"editing_{t['id']}"] = False
                        st.session_state[f"editing_{tid}"] = not currently
                        st.rerun()

                with col_del:
                    if st.button("✕", key=f"del_{tid}", help="delete"):
                        if delete_todo(tid):
                            st.session_state["last_msg"] = f"Deleted '{text}'."
                            st.session_state["last_ok"] = True
                        time.sleep(0.25)
                        st.rerun()

                if st.session_state.get(f"editing_{tid}", False):
                    with st.form(key=f"form_{tid}"):
                        new_text = st.text_input(
                            "new text", value=text, label_visibility="collapsed"
                        )
                        fc1, fc2, _ = st.columns([1, 1, 4])
                        with fc1:
                            do_save = st.form_submit_button("save")
                        with fc2:
                            do_cancel = st.form_submit_button("cancel")

                        if do_save and new_text.strip():
                            if update_todo(tid, text=new_text.strip()):
                                st.session_state[f"editing_{tid}"] = False
                                st.session_state["last_msg"] = f"Updated to '{new_text.strip()}'."
                                st.session_state["last_ok"] = True
                            time.sleep(0.25)
                            st.rerun()

                        if do_cancel:
                            st.session_state[f"editing_{tid}"] = False
                            st.rerun()

            if total > 0 and done_count == total:
                st.markdown(
                    '<div class="all-done">all done. not bad at all.</div>',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
