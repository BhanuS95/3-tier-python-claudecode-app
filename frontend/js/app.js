/**
 * Task Manager frontend.
 *
 * Talks to the backend exclusively through the REST API under /api.
 * In Docker Compose / production, the frontend's Nginx server proxies
 * /api/* and /health/* to the backend service, so relative URLs work
 * without any build-time configuration. For pure local (non-Docker)
 * development, set window.API_BASE_URL below or via a <script> tag.
 */
const API_BASE_URL = window.API_BASE_URL || "http://localhost:5000";

const els = {
  form: document.getElementById("task-form"),
  title: document.getElementById("task-title"),
  description: document.getElementById("task-description"),
  formError: document.getElementById("form-error"),
  list: document.getElementById("task-list"),
  loading: document.getElementById("loading-text"),
  empty: document.getElementById("empty-text"),
  listError: document.getElementById("list-error"),
  refreshBtn: document.getElementById("refresh-btn"),
  filters: document.getElementById("status-filters"),
  backendStatus: document.getElementById("backend-status"),
  modal: document.getElementById("task-modal"),
  editForm: document.getElementById("edit-form"),
  editId: document.getElementById("edit-id"),
  editTitle: document.getElementById("edit-title"),
  editDescription: document.getElementById("edit-description"),
  editStatus: document.getElementById("edit-status"),
  cancelEditBtn: document.getElementById("cancel-edit-btn"),
};

let currentStatusFilter = "";

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const message = body && body.error ? body.error.message : `Request failed (${response.status})`;
    throw new Error(message);
  }

  return body;
}

function statusLabel(status) {
  return { pending: "Pending", in_progress: "In Progress", completed: "Completed" }[status] || status;
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString();
}

function renderTasks(tasks) {
  els.list.innerHTML = "";

  if (!tasks.length) {
    els.empty.hidden = false;
    return;
  }
  els.empty.hidden = true;

  for (const task of tasks) {
    const li = document.createElement("li");
    li.className = "task-item";
    li.innerHTML = `
      <div class="task-item__main">
        <div class="task-item__title ${task.completed ? "completed" : ""}">${escapeHtml(task.title)}</div>
        ${task.description ? `<p class="task-item__description">${escapeHtml(task.description)}</p>` : ""}
        <div class="task-item__meta">
          <span class="badge badge--${task.status}">${statusLabel(task.status)}</span>
          &middot; updated ${formatDate(task.updated_at)}
        </div>
      </div>
      <div class="task-item__actions">
        ${task.completed ? "" : `<button class="icon-btn icon-btn--success" data-action="complete" data-id="${task.id}">Complete</button>`}
        <button class="icon-btn" data-action="edit" data-id="${task.id}">Edit</button>
        <button class="icon-btn icon-btn--danger" data-action="delete" data-id="${task.id}">Delete</button>
      </div>
    `;
    els.list.appendChild(li);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadTasks() {
  els.loading.hidden = false;
  els.listError.hidden = true;
  try {
    const query = currentStatusFilter ? `?status=${encodeURIComponent(currentStatusFilter)}` : "";
    const tasks = await apiRequest(`/api/tasks${query}`);
    renderTasks(tasks);
  } catch (err) {
    els.listError.textContent = `Could not load tasks: ${err.message}`;
    els.listError.hidden = false;
  } finally {
    els.loading.hidden = true;
  }
}

async function checkBackendHealth() {
  const pill = els.backendStatus;
  try {
    const health = await apiRequest("/health/ready");
    const up = health.status === "UP";
    pill.textContent = up ? "Backend + Database: UP" : "Backend UP, Database DOWN";
    pill.className = `status-pill ${up ? "status-pill--up" : "status-pill--down"}`;
  } catch (err) {
    pill.textContent = "Backend unreachable";
    pill.className = "status-pill status-pill--down";
  }
}

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  els.formError.hidden = true;

  const title = els.title.value.trim();
  const description = els.description.value.trim();

  if (!title) {
    els.formError.textContent = "Title is required.";
    els.formError.hidden = false;
    return;
  }

  try {
    await apiRequest("/api/tasks", {
      method: "POST",
      body: JSON.stringify({ title, description: description || null }),
    });
    els.form.reset();
    await loadTasks();
  } catch (err) {
    els.formError.textContent = err.message;
    els.formError.hidden = false;
  }
});

els.list.addEventListener("click", async (event) => {
  const btn = event.target.closest("button[data-action]");
  if (!btn) return;

  const { action, id } = btn.dataset;

  try {
    if (action === "delete") {
      if (!confirm("Delete this task?")) return;
      await apiRequest(`/api/tasks/${id}`, { method: "DELETE" });
      await loadTasks();
    } else if (action === "complete") {
      await apiRequest(`/api/tasks/${id}/complete`, { method: "PATCH" });
      await loadTasks();
    } else if (action === "edit") {
      const task = await apiRequest(`/api/tasks/${id}`);
      openEditModal(task);
    }
  } catch (err) {
    els.listError.textContent = err.message;
    els.listError.hidden = false;
  }
});

function openEditModal(task) {
  els.editId.value = task.id;
  els.editTitle.value = task.title;
  els.editDescription.value = task.description || "";
  els.editStatus.value = task.status;
  els.modal.showModal();
}

els.cancelEditBtn.addEventListener("click", () => els.modal.close());

els.editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = els.editId.value;

  try {
    await apiRequest(`/api/tasks/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        title: els.editTitle.value.trim(),
        description: els.editDescription.value.trim() || null,
        status: els.editStatus.value,
      }),
    });
    els.modal.close();
    await loadTasks();
  } catch (err) {
    alert(`Could not save changes: ${err.message}`);
  }
});

els.filters.addEventListener("click", (event) => {
  const btn = event.target.closest(".filter-btn");
  if (!btn) return;

  document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  currentStatusFilter = btn.dataset.status;
  loadTasks();
});

els.refreshBtn.addEventListener("click", () => {
  loadTasks();
  checkBackendHealth();
});

// Initial load
loadTasks();
checkBackendHealth();
setInterval(checkBackendHealth, 30000);
