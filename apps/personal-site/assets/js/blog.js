const apiBaseUrl = window.PRJ008_CONFIG?.apiBaseUrl || 'http://localhost:8001';
const pageSize = 4;

let offset = 0;
let isLoading = false;
let adminPosts = [];

const postsGrid = document.getElementById('blog-posts');
const loadMoreButton = document.getElementById('load-more-posts');
const statusMessage = document.getElementById('blog-status');
const reader = document.getElementById('blog-reader');
const themeToggle = document.getElementById('theme-toggle');
const adminPanel = document.getElementById('blog-admin-panel');
const adminToggle = document.getElementById('blog-admin-toggle');
const adminTokenInput = document.getElementById('blog-admin-token');
const adminLoadButton = document.getElementById('blog-admin-load');
const adminStatus = document.getElementById('blog-admin-status');
const adminList = document.getElementById('blog-admin-list');
const editorForm = document.getElementById('blog-editor-form');
const deleteButton = document.getElementById('blog-delete-post');
const resetButton = document.getElementById('blog-editor-reset');

const fields = {
  id: document.getElementById('blog-post-id'),
  slug: document.getElementById('blog-slug'),
  title: document.getElementById('blog-title-field'),
  summary: document.getElementById('blog-summary'),
  category: document.getElementById('blog-category'),
  status: document.getElementById('blog-status-field'),
  publishedAt: document.getElementById('blog-published-at'),
  tags: document.getElementById('blog-tags'),
  content: document.getElementById('blog-content'),
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatDate(value) {
  if (!value) return 'Draft';
  return new Intl.DateTimeFormat('en-GB', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  }).format(new Date(value));
}

function setStatus(element, message, type = 'muted') {
  if (!element) return;
  element.textContent = message;
  element.dataset.type = type;
}

function tagsFromInput(value) {
  return value.split(',').map(tag => tag.trim()).filter(Boolean);
}

function renderContent(content) {
  return escapeHtml(content)
    .split(/\n{2,}/)
    .map(paragraph => `<p>${paragraph.replaceAll('\n', '<br>')}</p>`)
    .join('');
}

function adminToken() {
  return adminTokenInput.value.trim();
}

function authHeaders() {
  return {
    Authorization: `Bearer ${adminToken()}`,
    'Content-Type': 'application/json',
  };
}

async function adminRequest(path, options = {}) {
  if (!adminToken()) {
    throw new Error('Admin token is required.');
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let message = `API returned ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch (error) {
      // Keep the HTTP status message when the response is not JSON.
    }
    throw new Error(message);
  }

  return response.status === 204 ? null : response.json();
}

function renderPostCard(post) {
  const tags = (post.tags || [])
    .map(tag => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join('');

  return `
    <article class="blog-card reveal">
      <div class="blog-meta">
        <span>${escapeHtml(formatDate(post.published_at))}</span>
        <span>${escapeHtml(post.category)}</span>
      </div>
      <h3>${escapeHtml(post.title)}</h3>
      <p>${escapeHtml(post.summary)}</p>
      <div class="tags">${tags}</div>
      <button class="project-link blog-read-link" type="button" data-slug="${escapeHtml(post.slug)}">Read article <span aria-hidden="true">→</span></button>
    </article>
  `;
}

function renderReader(post) {
  const tags = (post.tags || [])
    .map(tag => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join('');

  reader.innerHTML = `
    <p class="mono-label">${escapeHtml(post.category)} / ${escapeHtml(formatDate(post.published_at))}</p>
    <h3>${escapeHtml(post.title)}</h3>
    <p class="blog-reader-summary">${escapeHtml(post.summary)}</p>
    <div class="tags">${tags}</div>
    <div class="blog-content">${renderContent(post.content)}</div>
  `;
}

async function loadPostDetail(slug) {
  reader.innerHTML = '<p class="mono-label">Reader</p><h3>Loading article...</h3>';
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/blog/posts/${encodeURIComponent(slug)}`);
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }
    const payload = await response.json();
    renderReader(payload.post);
  } catch (error) {
    reader.innerHTML = '<p class="mono-label">Reader</p><h3>Article unavailable</h3><p>The API could not return this post right now.</p>';
  }
}

async function loadPosts() {
  if (isLoading) return;
  isLoading = true;
  loadMoreButton.disabled = true;
  loadMoreButton.textContent = 'Loading...';

  try {
    const url = `${apiBaseUrl}/api/v1/blog/posts?limit=${pageSize}&offset=${offset}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const payload = await response.json();
    postsGrid.insertAdjacentHTML('beforeend', payload.posts.map(renderPostCard).join(''));
    offset += payload.posts.length;

    setStatus(statusMessage, `Loaded ${offset}/${payload.total} published posts.`);
    loadMoreButton.hidden = !payload.has_more;
    loadMoreButton.disabled = false;
    loadMoreButton.textContent = 'Load more';
    initReveal();

    if (offset > 0 && reader.dataset.loaded !== 'true') {
      reader.dataset.loaded = 'true';
      loadPostDetail(payload.posts[0].slug);
    }
  } catch (error) {
    setStatus(statusMessage, 'Could not connect to the FastAPI blog API.', 'error');
    loadMoreButton.hidden = true;
  } finally {
    isLoading = false;
  }
}

function renderAdminList() {
  if (!adminPosts.length) {
    adminList.innerHTML = '<p class="blog-muted">No posts in the database yet.</p>';
    return;
  }

  adminList.innerHTML = adminPosts.map(post => `
    <button class="admin-post-item" type="button" data-post-id="${post.id}">
      <span>${escapeHtml(post.title)}</span>
      <small>${escapeHtml(post.status)} / ${escapeHtml(post.slug)}</small>
    </button>
  `).join('');
}

function fillEditor(post) {
  fields.id.value = post?.id || '';
  fields.slug.value = post?.slug || '';
  fields.title.value = post?.title || '';
  fields.summary.value = post?.summary || '';
  fields.category.value = post?.category || 'build-log';
  fields.status.value = post?.status || 'draft';
  fields.publishedAt.value = post?.published_at || '';
  fields.tags.value = (post?.tags || []).join(', ');
  fields.content.value = post?.content || '';
  deleteButton.hidden = !post?.id;
}

function editorPayload() {
  return {
    slug: fields.slug.value,
    title: fields.title.value,
    summary: fields.summary.value,
    content: fields.content.value,
    category: fields.category.value,
    tags: tagsFromInput(fields.tags.value),
    status: fields.status.value,
    published_at: fields.publishedAt.value || null,
  };
}

async function loadAdminPosts() {
  try {
    setStatus(adminStatus, 'Loading admin posts...');
    sessionStorage.setItem('blogAdminToken', adminToken());
    const payload = await adminRequest('/api/v1/admin/blog/posts');
    adminPosts = payload.posts;
    renderAdminList();
    setStatus(adminStatus, `Loaded ${payload.total} database posts.`);
  } catch (error) {
    setStatus(adminStatus, error.message, 'error');
  }
}

async function saveEditorPost(event) {
  event.preventDefault();
  const postId = fields.id.value;
  const path = postId ? `/api/v1/admin/blog/posts/${postId}` : '/api/v1/admin/blog/posts';
  const method = postId ? 'PATCH' : 'POST';

  try {
    setStatus(adminStatus, 'Saving post...');
    const payload = await adminRequest(path, {
      method,
      body: JSON.stringify(editorPayload()),
    });
    fillEditor(payload.post);
    await loadAdminPosts();
    resetPublicPosts();
    setStatus(adminStatus, 'Post saved.');
  } catch (error) {
    setStatus(adminStatus, error.message, 'error');
  }
}

async function deleteEditorPost() {
  const postId = fields.id.value;
  if (!postId || !confirm('Delete this blog post from the database?')) return;

  try {
    setStatus(adminStatus, 'Deleting post...');
    await adminRequest(`/api/v1/admin/blog/posts/${postId}`, { method: 'DELETE' });
    fillEditor(null);
    await loadAdminPosts();
    resetPublicPosts();
    setStatus(adminStatus, 'Post deleted.');
  } catch (error) {
    setStatus(adminStatus, error.message, 'error');
  }
}

function resetPublicPosts() {
  offset = 0;
  postsGrid.innerHTML = '';
  reader.dataset.loaded = 'false';
  reader.innerHTML = '<p class="mono-label">Reader</p><h3>Select a post</h3><p>Choose a published note to read the full database-backed article here.</p>';
  loadMoreButton.hidden = false;
  loadPosts();
}

function initReveal() {
  document.querySelectorAll('.reveal').forEach(element => {
    const rect = element.getBoundingClientRect();
    if (rect.top < window.innerHeight) {
      element.classList.add('visible');
    }
  });
}

function updateThemeLabel() {
  const isDark = document.body.classList.contains('dark');
  themeToggle?.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
  themeToggle?.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode');
}

if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');
adminTokenInput.value = sessionStorage.getItem('blogAdminToken') || '';
updateThemeLabel();

themeToggle?.addEventListener('click', () => {
  document.body.classList.toggle('dark');
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  updateThemeLabel();
});

adminToggle?.addEventListener('click', () => {
  adminPanel.hidden = !adminPanel.hidden;
  if (!adminPanel.hidden) {
    adminTokenInput.focus();
  }
});

postsGrid?.addEventListener('click', event => {
  const button = event.target.closest('[data-slug]');
  if (button) loadPostDetail(button.dataset.slug);
});

adminList?.addEventListener('click', event => {
  const button = event.target.closest('[data-post-id]');
  if (!button) return;
  const post = adminPosts.find(item => String(item.id) === button.dataset.postId);
  fillEditor(post);
});

adminLoadButton?.addEventListener('click', loadAdminPosts);
editorForm?.addEventListener('submit', saveEditorPost);
deleteButton?.addEventListener('click', deleteEditorPost);
resetButton?.addEventListener('click', () => fillEditor(null));
loadMoreButton?.addEventListener('click', loadPosts);

fillEditor(null);
loadPosts();
