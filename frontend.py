import streamlit as st
import requests
from typing import List, Dict, Optional
import time
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="things to do",
    page_icon="◉",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background-color: #181614 !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #ffffff !important;
}

/* ── Layout ──────────────────────────────── */
.block-container {
    max-width: 1100px !important;
    padding: 3rem 2.5rem 5rem !important;
    background: transparent !important;
    margin: 0 auto !important;
}

/* ── Header ──────────────────────────────── */
.app-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 2.8rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid #252118;
}
.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3.2rem;
    color: #ffffff;
    line-height: 1.05;
    letter-spacing: -0.025em;
}
.app-title em {
    font-style: italic;
    color: #c49a6c;
}
.app-meta {
    text-align: right;
}
.app-date {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 300;
    color: #d6cdb8;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    line-height: 1.9;
}

/* ── Stats ───────────────────────────────── */
.stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.75rem;
    margin-bottom: 1.8rem;
}
.stat-card {
    background: #1f1c18;
    border: 1px solid #2a2520;
    border-radius: 12px;
    padding: 1.1rem 1rem;
    text-align: center;
}
.stat-num {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: #c49a6c;
    line-height: 1;
    display: block;
}
.stat-num.all { color: #7a6a5a; }
.stat-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: #d0c6b8;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.3rem;
    display: block;
}

/* ── Progress ────────────────────────────── */
.progress-wrap { margin-bottom: 2rem; }
.progress-label {
    display: flex;
    justify-content: space-between;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #d0c6b8;
    font-weight: 300;
    letter-spacing: 0.07em;
    margin-bottom: 0.45rem;
}
.progress-track {
    height: 3px;
    background: #252118;
    border-radius: 99px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #7a4e28 0%, #c49a6c 100%);
    border-radius: 99px;
}

/* ── Command bar ─────────────────────────── */
.cmd-section { margin-bottom: 0.6rem; }
.cmd-label {
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #d0c6b8;
    margin-bottom: 0.6rem;
    display: block;
}
.cmd-hint {
    margin-top: 0.7rem;
    line-height: 2;
}
.cmd-hint span {
    display: inline-block;
    background: #252118;
    border: 1px solid #2e2920;
    border-radius: 4px;
    padding: 1px 7px;
    margin: 2px 2px;
    color: #e6dfcf;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 300;
}

/* ── Streamlit input overrides ───────────── */
.stTextInput > div > div > input {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    color: #ffffff !important;
    background: #252118 !important;
    border: 1.5px solid #322c24 !important;
    border-radius: 9px !important;
    padding: 0.78rem 1rem !important;
    box-shadow: none !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #c49a6c !important;
    box-shadow: 0 0 0 3px rgba(196,154,108,0.09) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #3e3528 !important; }

/* ── Buttons ─────────────────────────────── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 9px !important;
    transition: all 0.13s ease !important;
    cursor: pointer !important;
}
/* Primary — run command */
.stButton > button[kind="primary"] {
    background: #c49a6c !important;
    color: #181614 !important;
    border: none !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    padding: 0.78rem 1rem !important;
    letter-spacing: 0.01em !important;
}
.stButton > button[kind="primary"]:hover {
    background: #d4aa7c !important;
    box-shadow: 0 4px 16px rgba(196,154,108,0.22) !important;
    transform: translateY(-1px) !important;
}
/* Secondary / icon buttons */
.stButton > button:not([kind]),
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #e6dfcf !important;
    border: 1px solid #252118 !important;
    font-size: 1rem !important;
    padding: 0.38rem 0.58rem !important;
    min-height: unset !important;
}
.stButton > button:not([kind]):hover,
.stButton > button[kind="secondary"]:hover {
    background: #252118 !important;
    color: #f5efe4 !important;
    border-color: #322c24 !important;
}

/* ── Divider ─────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #252118 !important;
    margin: 1.6rem 0 !important;
}

/* ── Section header ──────────────────────── */
.list-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 1.2rem;
}
.list-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    color: #ffffff;
    font-weight: 400;
    letter-spacing: -0.01em;
}
.list-count {
    font-family: 'DM Mono', monospace;
    font-size: 0.67rem;
    color: #d0c6b8;
    font-weight: 300;
    letter-spacing: 0.08em;
}

/* ── Todo cards ──────────────────────────── */
.todo-card {
    background: #1f1c18;
    border: 1px solid #2a2520;
    border-radius: 11px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.12s, background 0.12s;
}
.todo-card:hover { border-color: #38322a; background: #222019; }
.todo-card.done {
    background: #1b1915;
    border-color: #232019;
    opacity: 0.55;
}
.todo-meta {
    font-family: 'DM Mono', monospace;
    font-size: 0.63rem;
    font-weight: 300;
    color: #d0c6b8;
    letter-spacing: 0.1em;
    margin-bottom: 0.28rem;
}
.todo-text {
    font-size: 1.02rem;
    font-weight: 400;
    color: #ffffff;
    line-height: 1.5;
}
.todo-text.done {
    text-decoration: line-through;
    color: #bfb6a6;
}

/* ── Empty state ─────────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 1rem;
}
.empty-icon { font-size: 2rem; display: block; margin-bottom: 0.9rem; opacity: 0.25; }
.empty-text { font-size: 0.9rem; font-style: italic; color: #d0c6b8; }

/* ── All-done message ────────────────────── */
.all-done {
    text-align: center;
    padding: 1.8rem 0 0;
    font-style: italic;
    font-size: 0.88rem;
    color: #d0c6b8;
}

/* ── Alerts ──────────────────────────────── */
div[data-testid="stAlert"] {
    border-radius: 9px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
}

/* ── Forms ───────────────────────────────── */
div[data-testid="stForm"] {
    background: #1b1915 !important;
    border: 1px solid #252118 !important;
    border-radius: 11px !important;
    padding: 1.1rem !important;
}
.stFormSubmitButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.87rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
}

/* ── Expander ────────────────────────────── */
div[data-testid="stExpander"] {
    border: 1px solid #252118 !important;
    border-radius: 9px !important;
    background: transparent !important;
}
div[data-testid="stExpander"] summary {
    color: #d0c6b8 !important;
    font-size: 0.8rem !important;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 0.05em !important;
}

/* ── Column padding ──────────────────────── */
[data-testid="column"] { padding: 0 0.2rem !important; }

/* ── Hide Streamlit chrome ───────────────── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# API HELPERS  (frontend only — backend untouched)
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
        st.error("⚠ Can't reach the backend. Start it with: `uvicorn backend:app --reload`")
        return []
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return []


def update_todo(todo_id: int, text: Optional[str] = None, completed: Optional[bool] = None) -> bool:
    try:
        data: Dict = {}
        if text is not None:      data["text"] = text
        if completed is not None: data["completed"] = completed
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
    """
    POST /todos/process-command
    Backend returns:
      { action, todo_id, todo_text, message,
        result: { success, message, [todo|todos|count] } }
    """
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
    """
    Safely unpack whatever the backend returns and give back (success, message).
    Handles both flat and nested shapes defensively.
    """
    if resp is None:
        return False, "No response from backend."

    # Top-level message is most human-readable
    top_msg: str = resp.get("message", "")

    # Nested result block
    inner: Dict = resp.get("result") or {}
    inner_ok:  bool = bool(inner.get("success", False))
    inner_msg: str  = inner.get("message", "")

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
    if h < 12: return "morning"
    if h < 17: return "afternoon"
    return "evening"


def relative_time(iso: str) -> str:
    """Turn ISO timestamp into a human-friendly relative string."""
    try:
        dt = datetime.fromisoformat(iso)
        diff = datetime.now() - dt
        s = int(diff.total_seconds())
        if s < 60:        return "just now"
        if s < 3600:      return f"{s // 60}m ago"
        if s < 86400:     return f"{s // 3600}h ago"
        if s < 7 * 86400: return f"{s // 86400}d ago"
        return dt.strftime("%d %b")
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Session state defaults
    for key, val in [("last_msg", None), ("last_ok", None), ("pending_rerun", False)]:
        if key not in st.session_state:
            st.session_state[key] = val

    now      = datetime.now()
    today    = now.strftime("%A, %d %b")
    time_str = now.strftime("%H:%M")

    # ── Fetch todos early (needed for stats + list)
    todos      = get_todos()
    total      = len(todos)
    done_count = sum(1 for t in todos if t.get("completed", False))
    pending    = total - done_count

    # ══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════════════════════
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

    # ══════════════════════════════════════════════════════════════════════════
    # TWO-COLUMN LAYOUT
    # ══════════════════════════════════════════════════════════════════════════
    left, right = st.columns([1, 1.7], gap="large")

    # ──────────────────────────────────────────────────────────────────────────
    # LEFT — command + stats
    # ──────────────────────────────────────────────────────────────────────────
    with left:

        # Stats cards (only when there are todos)
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

        # ── Execute NL command
        if run and prompt:
            with st.spinner("thinking…"):
                resp = process_command(prompt.strip())
            ok, msg = parse_command_response(resp)
            st.session_state.last_ok  = ok
            st.session_state.last_msg = msg
            time.sleep(0.25)
            st.rerun()

        # ── Show last command result
        if st.session_state.last_msg:
            if st.session_state.last_ok:
                st.success(st.session_state.last_msg)
            else:
                st.warning(st.session_state.last_msg)

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
                    st.session_state.last_msg = "All todos cleared."
                    st.session_state.last_ok  = True
                    time.sleep(0.25)
                    st.rerun()

    # ──────────────────────────────────────────────────────────────────────────
    # RIGHT — todo list
    # ──────────────────────────────────────────────────────────────────────────
    with right:
        st.markdown(f"""
            <div class="list-header">
                <span class="list-title">the list</span>
                <span class="list-count">{total} item{"s" if total != 1 else ""}</span>
            </div>
        """, unsafe_allow_html=True)

        if not todos:
            st.markdown("""
                <div class="empty-state">
                    <span class="empty-icon">◎</span>
                    <span class="empty-text">nothing here yet — add something on the left</span>
                </div>
            """, unsafe_allow_html=True)

        else:
            for todo in todos:
                tid      = todo["id"]
                text     = todo["text"]
                is_done  = bool(todo.get("completed", False))
                created  = relative_time(todo.get("created_at", ""))

                card_cls = "todo-card done" if is_done else "todo-card"
                txt_cls  = "todo-text done" if is_done else "todo-text"
                dot      = "✓" if is_done else "·"

                col_card, col_tog, col_ed, col_del = st.columns([6.5, 0.6, 0.6, 0.6])

                with col_card:
                    st.markdown(f"""
                        <div class="{card_cls}">
                            <div class="todo-meta">{fmt_id(tid)} &nbsp;{dot}&nbsp; {created}</div>
                            <div class="{txt_cls}">{text}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with col_tog:
                    tog_lbl = "✓" if not is_done else "↩"
                    tog_tip = "mark done" if not is_done else "mark undone"
                    if st.button(tog_lbl, key=f"tog_{tid}", help=tog_tip):
                        if update_todo(tid, completed=not is_done):
                            st.session_state.last_msg = (
                                f"Marked '{text}' as {'done' if not is_done else 'pending'}."
                            )
                            st.session_state.last_ok = True
                        time.sleep(0.25)
                        st.rerun()

                with col_ed:
                    if st.button("✎", key=f"ed_{tid}", help="edit"):
                        # Toggle edit mode; close others
                        currently = st.session_state.get(f"editing_{tid}", False)
                        for t in todos:
                            st.session_state[f"editing_{t['id']}"] = False
                        st.session_state[f"editing_{tid}"] = not currently
                        st.rerun()

                with col_del:
                    if st.button("✕", key=f"del_{tid}", help="delete"):
                        if delete_todo(tid):
                            st.session_state.last_msg = f"Deleted '{text}'."
                            st.session_state.last_ok  = True
                        time.sleep(0.25)
                        st.rerun()

                # Inline edit form
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
                                st.session_state.last_msg = f"Updated to '{new_text.strip()}'."
                                st.session_state.last_ok  = True
                            time.sleep(0.25)
                            st.rerun()

                        if do_cancel:
                            st.session_state[f"editing_{tid}"] = False
                            st.rerun()

            # All-done message
            if total > 0 and done_count == total:
                st.markdown(
                    '<div class="all-done">all done. not bad at all.</div>',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()