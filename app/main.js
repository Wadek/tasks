// Simple client for the tasks / reminders UI
let allTasks = [];
let currentEditId = null;

// Token handling - same pattern as books
let urlToken = new URLSearchParams(location.search).get('token');
if (urlToken) {
  try { localStorage.setItem('tasks_token', urlToken); } catch(e) {}
} else {
  urlToken = localStorage.getItem('tasks_token');
}
if (new URLSearchParams(location.search).get('token')) {
  history.replaceState(null, '', location.pathname + location.hash);
}

function withToken(url) {
  if (!urlToken) return url;
  const sep = url.includes('?') ? '&' : '?';
  return url + sep + 'token=' + encodeURIComponent(urlToken);
}

const searchInput = document.getElementById('search');
const listEl = document.getElementById('list');
const emptyEl = document.getElementById('empty');
const statsEl = document.getElementById('stats');

async function loadTasks() {
  const url = withToken('/api/tasks');
  const res = await fetch(url, { credentials: 'same-origin' });
  const data = await res.json();
  allTasks = data.tasks || [];
  render();
}

function render() {
  const q = (searchInput.value || '').toLowerCase().trim();
  let filtered = allTasks;
  if (q) {
    filtered = allTasks.filter(t =>
      (t.title || '').toLowerCase().includes(q) ||
      (t.notes || '').toLowerCase().includes(q)
    );
  }

  listEl.innerHTML = '';
  emptyEl.style.display = filtered.length ? 'none' : 'block';

  const pending = allTasks.filter(t => !t.completed).length;
  statsEl.textContent = `${pending} pending`;

  filtered.forEach(task => {
    const el = document.createElement('div');
    el.className = 'task' + (task.completed ? ' completed' : '');

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = !!task.completed;
    cb.addEventListener('change', () => toggleTask(task.id));

    const main = document.createElement('div');
    main.className = 'task-main';

    const title = document.createElement('div');
    title.className = 'task-title';
    title.textContent = task.title || '(untitled)';

    const due = document.createElement('div');
    due.className = 'task-due';
    if (task.due) {
      due.textContent = 'Due ' + task.due;
      const today = new Date().toISOString().slice(0,10);
      if (!task.completed && task.due < today) {
        due.classList.add('overdue');
      }
    }

    main.appendChild(title);
    if (task.due) main.appendChild(due);

    if (task.notes) {
      const notes = document.createElement('div');
      notes.className = 'task-notes';
      notes.textContent = task.notes;
      main.appendChild(notes);
    }

    const actions = document.createElement('div');
    actions.className = 'task-actions';

    const editBtn = document.createElement('button');
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', (e) => {
      e.stopImmediatePropagation();
      openEdit(task);
    });

    actions.appendChild(editBtn);

    el.appendChild(cb);
    el.appendChild(main);
    el.appendChild(actions);

    // Click anywhere except checkbox to edit
    el.addEventListener('click', (e) => {
      if (e.target !== cb) openEdit(task);
    });

    listEl.appendChild(el);
  });
}

async function addTask() {
  const title = document.getElementById('new-title').value.trim();
  if (!title) return;
  const due = document.getElementById('new-due').value || null;
  const notes = document.getElementById('new-notes').value.trim() || null;

  const res = await fetch(withToken('/api/tasks'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, due, notes }),
    credentials: 'same-origin'
  });
  if (res.ok) {
    document.getElementById('new-title').value = '';
    document.getElementById('new-due').value = '';
    document.getElementById('new-notes').value = '';
    await loadTasks();
  }
}

async function toggleTask(id) {
  await fetch(withToken(`/api/tasks/${id}/toggle`), {
    method: 'POST',
    credentials: 'same-origin'
  });
  await loadTasks();
}

function openEdit(task) {
  currentEditId = task.id;
  document.getElementById('edit-title').value = task.title || '';
  document.getElementById('edit-due').value = task.due || '';
  document.getElementById('edit-notes').value = task.notes || '';
  document.getElementById('edit-modal').style.display = 'flex';
}

async function saveEdit() {
  if (!currentEditId) return;
  const title = document.getElementById('edit-title').value.trim();
  const due = document.getElementById('edit-due').value || null;
  const notes = document.getElementById('edit-notes').value.trim() || null;

  await fetch(withToken(`/api/tasks/${currentEditId}`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, due, notes }),
    credentials: 'same-origin'
  });
  closeEdit();
  await loadTasks();
}

async function deleteEdit() {
  if (!currentEditId) return;
  if (!confirm('Delete this task?')) return;
  await fetch(withToken(`/api/tasks/${currentEditId}`), {
    method: 'DELETE',
    credentials: 'same-origin'
  });
  closeEdit();
  await loadTasks();
}

function closeEdit() {
  document.getElementById('edit-modal').style.display = 'none';
  currentEditId = null;
}

// Event listeners
document.getElementById('add-btn').addEventListener('click', addTask);
searchInput.addEventListener('input', render);

document.getElementById('save-edit').addEventListener('click', saveEdit);
document.getElementById('cancel-edit').addEventListener('click', closeEdit);
document.getElementById('delete-edit').addEventListener('click', deleteEdit);

// Close modal on outside click
document.getElementById('edit-modal').addEventListener('click', (e) => {
  if (e.target.id === 'edit-modal') closeEdit();
});

// Keyboard: Enter in add form
['new-title', 'new-due', 'new-notes'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      addTask();
    }
  });
});

// Initial load
loadTasks();
