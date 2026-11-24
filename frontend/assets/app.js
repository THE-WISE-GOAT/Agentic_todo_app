const $ = (selector, root = document) => root.querySelector(selector);

const els = {
  today: $("#today"),
  headline: $("#headline"),
  statOpen: $("#stat-open"),
  statDone: $("#stat-done"),
  statOverdue: $("#stat-overdue"),
  progressFill: $("#progress-fill"),
  progressLabel: $("#progress-label"),
  list: $("#list"),
  empty: $("#empty"),
  emptyTitle: $("#empty-title"),
  emptyBody: $("#empty-body"),
  countOpen: $("#count-open"),
  countDone: $("#count-done"),
  countAll: $("#count-all"),
  search: $("#search"),
  filterCategory: $("#filter-category"),
  sort: $("#sort"),
  addForm: $("#add-form"),
  newText: $("#new-text"),
  newPriority: $("#new-priority"),
  newCategory: $("#new-category"),
  newDue: $("#new-due"),
  commandForm: $("#command-form"),
  commandInput: $("#command-input"),
  commandSubmit: $("#command-submit"),
  commandResult: $("#command-result"),
  agentState: $("#agent-state"),
  modeAdd: $("#mode-add"),
  modeCommand: $("#mode-command"),
  paneAdd: $("#pane-add"),
  paneCommand: $("#pane-command"),
  clearDone: $("#clear-done"),
  toasts: $("#toasts"),
};

const FALLBACK_META = {
  priorities: ["Low", "Medium", "High"],
  categories: ["University", "Tech Projects", "Watchlist", "Personal", "Work", "General"],
};

const state = {
  mode: "add",
  status: "open",
  category: "",
  query: "",
  sort: "newest",
  todos: [],
  stats: { total: 0, open: 0, done: 0, overdue: 0 },
  meta: FALLBACK_META,
  editingId: null,
};

async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail) ? detail[0]?.msg : detail;
    throw new Error(message || `Request failed (${response.status})`);
  }
  return data;
}

/* ---------- formatting ---------- */

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);

const startOfDay = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate());

function dayDiff(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number);
  const target = new Date(year, month - 1, day);
  return Math.round((startOfDay(target) - startOfDay(new Date())) / 86400000);
}

function shortDate(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
  });
}

function dueInfo(isoDate, completed) {
  if (!isoDate) return null;
  const diff = dayDiff(isoDate);
  const overdue = diff < 0 && !completed;
  const soon = !overdue && !completed && diff <= 1;

  let label;
  if (diff === 0) label = "due today";
  else if (diff === 1) label = "due tomorrow";
  else if (diff === -1) label = "1d overdue";
  else if (diff < 0) label = `${Math.abs(diff)}d overdue`;
  else if (diff <= 7) {
    const weekday = new Date(isoDate + "T00:00:00").toLocaleDateString(undefined, {
      weekday: "short",
    });
    label = `due ${weekday}`;
  } else label = `due ${shortDate(isoDate)}`;

  return { label, overdue, soon };
}

function timeAgo(isoTimestamp) {
  const then = new Date(isoTimestamp);
  if (Number.isNaN(then.getTime())) return "";
  const seconds = Math.round((Date.now() - then.getTime()) / 1000);

  if (seconds < 60) return "just added";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  const days = Math.floor(seconds / 86400);
  if (days < 7) return `${days}d ago`;
  return shortDate(then.toISOString().slice(0, 10));
}

/* ---------- rendering ---------- */

function taskTemplate(todo) {
  const due = dueInfo(todo.due_date, todo.completed);
  const priorityClass = todo.priority.toLowerCase();
  const badges = [
    `<span class="badge prio-${priorityClass}">${escapeHtml(todo.priority)}</span>`,
    `<span class="badge category">${escapeHtml(todo.category)}</span>`,
  ];

  if (due) {
    const classes = ["badge", "due"];
    if (due.overdue) classes.push("is-overdue");
    else if (due.soon) classes.push("is-soon");
    badges.push(`<span class="${classes.join(" ")}">${escapeHtml(due.label)}</span>`);
  }

  return `
    <li class="task${todo.completed ? " is-done" : ""}" data-id="${todo.id}">
      <button class="task-check" type="button" data-action="toggle"
        aria-label="${todo.completed ? "Mark as open" : "Mark as done"}"
        aria-pressed="${todo.completed}">
        <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M3 8.5l3 3 7-7" stroke="currentColor" stroke-width="2.4"
            stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <div class="task-body">
        <p class="task-text">${escapeHtml(todo.text)}</p>
        <p class="task-meta">
          ${badges.join("")}
          <span class="task-age">${escapeHtml(timeAgo(todo.created_at))}</span>
        </p>
      </div>
      <div class="task-actions">
        <button class="icon-btn" type="button" data-action="edit" aria-label="Edit task">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M13.2 3.4l3.4 3.4M4 16l3.9-.8 8-8a1.7 1.7 0 0 0 0-2.4l-.7-.7a1.7 1.7 0 0 0-2.4 0l-8 8L4 16z"
              stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <button class="icon-btn is-danger" type="button" data-action="delete" aria-label="Delete task">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </li>
  `;
}

function editTemplate(todo) {
  const options = (values, selected) =>
    values
      .map(
        (value) =>
          `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(
            value,
          )}</option>`,
      )
      .join("");

  return `
    <li class="task is-editing" data-id="${todo.id}">
      <form class="edit-form" autocomplete="off">
        <label class="sr-only" for="edit-text-${todo.id}">Task text</label>
        <input class="text-input" id="edit-text-${todo.id}" name="text" type="text"
          maxlength="500" value="${escapeHtml(todo.text)}" required>
        <div class="edit-fields">
          <label class="sr-only" for="edit-priority-${todo.id}">Priority</label>
          <select id="edit-priority-${todo.id}" name="priority">
            ${options(state.meta.priorities, todo.priority)}
          </select>
          <label class="sr-only" for="edit-category-${todo.id}">Category</label>
          <select id="edit-category-${todo.id}" name="category">
            ${options(state.meta.categories, todo.category)}
          </select>
          <label class="sr-only" for="edit-due-${todo.id}">Due date</label>
          <input id="edit-due-${todo.id}" name="due_date" type="date" value="${todo.due_date || ""}">
          <div class="edit-actions">
            <button class="btn btn-primary btn-sm" type="submit">save</button>
            <button class="btn btn-ghost btn-sm" type="button" data-action="cancel">cancel</button>
          </div>
        </div>
      </form>
    </li>
  `;
}

function emptyCopy() {
  if (state.query) {
    return ["no matches", `nothing here matches “${state.query}”.`];
  }
  if (state.status === "done") {
    return ["nothing done yet", "finished tasks end up here."];
  }
  if (state.stats.total === 0) {
    return ["nothing on the list", "add your first task above to get started."];
  }
  if (state.status === "open") {
    return ["all clear", "everything is done. go do something else."];
  }
  return ["nothing here", "add a task above."];
}

function render() {
  const { total, open, done, overdue } = state.stats;

  els.statOpen.textContent = open;
  els.statDone.textContent = done;
  els.statOverdue.textContent = overdue;
  els.statOverdue.dataset.zero = String(overdue === 0);
  els.headline.textContent = open === 0 ? (total === 0 ? "no tasks" : "all clear") : `${open} open`;
  els.countOpen.textContent = open;
  els.countDone.textContent = done;
  els.countAll.textContent = total;

  const percent = total ? Math.round((done / total) * 100) : 0;
  els.progressFill.style.width = `${percent}%`;
  els.progressLabel.textContent = total
    ? `${done} of ${total} done${overdue ? ` · ${overdue} overdue` : ""}`
    : "nothing yet";

  document.title = open ? `(${open}) things to do` : "things to do";

  if (state.loaded) {
    els.list.innerHTML = state.todos
      .map((todo) => (todo.id === state.editingId ? editTemplate(todo) : taskTemplate(todo)))
      .join("");

    const isEmpty = state.todos.length === 0;
    els.empty.hidden = !isEmpty;
    if (isEmpty) {
      const [title, body] = emptyCopy();
      els.emptyTitle.textContent = title;
      els.emptyBody.textContent = body;
    }

    if (state.editingId !== null) {
      const input = els.list.querySelector(".edit-form input[name='text']");
      if (input && document.activeElement !== input) {
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
      }
    }
  }

  document.querySelectorAll(".tab").forEach((tab) => {
    const active = tab.dataset.status === state.status;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });
}

/* ---------- data ---------- */

async function load({ quiet = false } = {}) {
  if (!quiet) els.list.classList.add("is-loading");
  try {
    const params = new URLSearchParams({ status: state.status, sort: state.sort });
    if (state.category) params.set("category", state.category);
    if (state.query) params.set("q", state.query);

    const [todos, stats] = await Promise.all([
      api(`/todos?${params.toString()}`),
      api("/stats"),
    ]);

    state.todos = todos;
    state.stats = stats;
    state.loaded = true;
    render();
  } catch (error) {
    state.loaded = true;
    els.empty.hidden = false;
    els.emptyTitle.textContent = "can't reach the api";
    els.emptyBody.textContent = `${error.message}. is the server running?`;
    toast(error.message, { tone: "error" });
  } finally {
    els.list.classList.remove("is-loading");
  }
}

async function loadMeta() {
  try {
    const meta = await api("/meta");
    state.meta = meta;
    fillOptions(els.newPriority, meta.priorities, "Medium");
    fillOptions(els.newCategory, meta.categories, "General");
    fillOptions(els.filterCategory, meta.categories, "", "all categories");
    renderAgentState();
  } catch {
    fillOptions(els.newPriority, FALLBACK_META.priorities, "Medium");
    fillOptions(els.newCategory, FALLBACK_META.categories, "General");
    fillOptions(els.filterCategory, FALLBACK_META.categories, "", "all categories");
  }
}

function fillOptions(select, values, selected, placeholder) {
  const items = values.map(
    (value) =>
      `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(
        value,
      )}</option>`,
  );
  if (placeholder !== undefined) {
    items.unshift(`<option value="">${escapeHtml(placeholder)}</option>`);
  }
  select.innerHTML = items.join("");
}

/* ---------- actions ---------- */

async function toggleTodo(todo) {
  const next = !todo.completed;
  todo.completed = next;
  render();

  try {
    await api(`/todos/${todo.id}`, { method: "PATCH", body: { completed: next } });
    await load({ quiet: true });
  } catch (error) {
    todo.completed = !next;
    render();
    toast(error.message, { tone: "error" });
  }
}

async function removeTodo(todo) {
  try {
    await api(`/todos/${todo.id}`, { method: "DELETE" });
    if (state.editingId === todo.id) state.editingId = null;
    await load({ quiet: true });

    toast("Task deleted.", {
      actionLabel: "undo",
      onAction: async () => {
        try {
          const created = await api("/todos", {
            method: "POST",
            body: {
              text: todo.text,
              priority: todo.priority,
              category: todo.category,
              due_date: todo.due_date,
            },
          });
          if (todo.completed) {
            await api(`/todos/${created.id}`, { method: "PATCH", body: { completed: true } });
          }
          await load({ quiet: true });
        } catch (error) {
          toast(error.message, { tone: "error" });
        }
      },
    });
  } catch (error) {
    toast(error.message, { tone: "error" });
  }
}

function startEdit(todo) {
  state.editingId = todo.id;
  render();
}

async function saveEdit(todo, form) {
  const data = new FormData(form);
  const body = {
    text: String(data.get("text") || "").trim(),
    priority: data.get("priority"),
    category: data.get("category"),
    due_date: data.get("due_date") || null,
  };

  if (!body.text) {
    toast("A task needs some text.", { tone: "error" });
    return;
  }

  try {
    await api(`/todos/${todo.id}`, { method: "PATCH", body });
    state.editingId = null;
    await load({ quiet: true });
    toast("Saved.");
  } catch (error) {
    toast(error.message, { tone: "error" });
  }
}

async function clearDone() {
  if (!state.stats.done) {
    toast("Nothing completed yet.");
    return;
  }
  const label = `${state.stats.done} completed task${state.stats.done === 1 ? "" : "s"}`;
  if (!window.confirm(`Delete ${label}? This can't be undone.`)) return;

  try {
    const result = await api("/todos?status=done", { method: "DELETE" });
    await load({ quiet: true });
    toast(`Cleared ${result.deleted} task${result.deleted === 1 ? "" : "s"}.`);
  } catch (error) {
    toast(error.message, { tone: "error" });
  }
}

/* ---------- agent ---------- */

function renderAgentState() {
  const agent = state.meta.agent;
  if (!agent) return;
  els.agentState.hidden = state.mode !== "command";
  els.agentState.textContent = agent.available ? `${agent.model} · ready` : "ollama offline";
  els.agentState.classList.toggle("is-off", !agent.available);
}

function setMode(mode) {
  state.mode = mode;
  renderAgentState();
  const isAdd = mode === "add";
  els.modeAdd.classList.toggle("is-active", isAdd);
  els.modeCommand.classList.toggle("is-active", !isAdd);
  els.modeAdd.setAttribute("aria-selected", String(isAdd));
  els.modeCommand.setAttribute("aria-selected", String(!isAdd));
  els.paneAdd.hidden = !isAdd;
  els.paneCommand.hidden = isAdd;
}

function showCommandResult(message, isError) {
  els.commandResult.hidden = false;
  els.commandResult.textContent = message;
  els.commandResult.classList.toggle("is-error", Boolean(isError));
}

async function runCommand(command) {
  const original = els.commandSubmit.textContent;
  els.commandSubmit.disabled = true;
  els.commandSubmit.textContent = "running";

  try {
    const result = await api("/agent/command", { method: "POST", body: { command } });
    showCommandResult(result.message, !result.ok);
    await loadMeta();
    await load({ quiet: true });
    if (result.ok) els.commandInput.value = "";
  } catch (error) {
    showCommandResult(error.message, true);
    await loadMeta();
  } finally {
    els.commandSubmit.disabled = false;
    els.commandSubmit.textContent = original;
  }
}

/* ---------- toasts ---------- */

function toast(message, { tone = "info", actionLabel, onAction } = {}) {
  const node = document.createElement("div");
  node.className = `toast${tone === "error" ? " is-error" : ""}`;

  const text = document.createElement("span");
  text.textContent = message;
  node.append(text);

  if (actionLabel && onAction) {
    const action = document.createElement("button");
    action.type = "button";
    action.textContent = actionLabel;
    action.addEventListener("click", () => {
      node.remove();
      onAction();
    });
    node.append(action);
  }

  els.toasts.append(node);
  while (els.toasts.children.length > 3) els.toasts.firstElementChild.remove();
  setTimeout(() => node.remove(), 5000);
}

/* ---------- events ---------- */

els.addForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = els.newText.value.trim();
  if (!text) return;

  try {
    await api("/todos", {
      method: "POST",
      body: {
        text,
        priority: els.newPriority.value,
        category: els.newCategory.value,
        due_date: els.newDue.value || null,
      },
    });
    els.newText.value = "";
    els.newDue.value = "";
    await load({ quiet: true });
    els.newText.focus();
  } catch (error) {
    toast(error.message, { tone: "error" });
  }
});

els.commandForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const command = els.commandInput.value.trim();
  if (command) runCommand(command);
});

document.querySelectorAll(".hint-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    els.commandInput.value = chip.dataset.command || "";
    els.commandInput.focus();
  });
});

els.list.addEventListener("click", (event) => {
  const action = event.target.closest("[data-action]");
  if (!action) return;

  const row = action.closest("[data-id]");
  const todo = state.todos.find((item) => item.id === Number(row?.dataset.id));
  if (!todo) return;

  if (action.dataset.action === "toggle") toggleTodo(todo);
  if (action.dataset.action === "delete") removeTodo(todo);
  if (action.dataset.action === "edit") startEdit(todo);
  if (action.dataset.action === "cancel") {
    state.editingId = null;
    render();
  }
});

els.list.addEventListener("submit", (event) => {
  const form = event.target.closest(".edit-form");
  if (!form) return;
  event.preventDefault();

  const todo = state.todos.find((item) => item.id === Number(form.closest("[data-id]")?.dataset.id));
  if (todo) saveEdit(todo, form);
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    state.status = tab.dataset.status;
    state.editingId = null;
    render();
    load();
  });
});

els.filterCategory.addEventListener("change", () => {
  state.category = els.filterCategory.value;
  state.editingId = null;
  load();
});

els.sort.addEventListener("change", () => {
  state.sort = els.sort.value;
  load();
});

let searchTimer;
els.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.query = els.search.value.trim();
    load();
  }, 180);
});

els.modeAdd.addEventListener("click", () => {
  setMode("add");
  els.newText.focus();
});

els.modeCommand.addEventListener("click", () => {
  setMode("command");
  els.commandInput.focus();
});

els.clearDone.addEventListener("click", clearDone);

document.addEventListener("keydown", (event) => {
  const tag = (event.target.tagName || "").toLowerCase();
  const typing = ["input", "textarea", "select"].includes(tag) || event.target.isContentEditable;

  if (event.key === "/" && !typing) {
    event.preventDefault();
    els.search.focus();
  } else if (event.key.toLowerCase() === "n" && !typing && !event.metaKey && !event.ctrlKey) {
    event.preventDefault();
    setMode("add");
    els.newText.focus();
  } else if (event.key === "Escape") {
    if (document.activeElement === els.search) {
      els.search.value = "";
      state.query = "";
      els.search.blur();
      load();
    } else if (state.editingId !== null) {
      state.editingId = null;
      render();
    }
  }
});

/* ---------- boot ---------- */

els.today.textContent = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  day: "numeric",
  month: "long",
});

loadMeta().then(() => load());
