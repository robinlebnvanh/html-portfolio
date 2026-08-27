const apiBaseUrl = window.PRJ008_CONFIG?.apiBaseUrl || 'http://localhost:8001';
const pageSize = 4;

let offset = 0;
let isLoading = false;

const postsGrid = document.getElementById('blog-posts');
const loadMoreButton = document.getElementById('load-more-posts');
const statusMessage = document.getElementById('blog-status');
const reader = document.getElementById('blog-reader');
const themeToggle = document.getElementById('theme-toggle');

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

function renderContent(content) {
  return escapeHtml(content)
    .split(/\n{2,}/)
    .map(paragraph => `<p>${paragraph.replaceAll('\n', '<br>')}</p>`)
    .join('');
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
updateThemeLabel();

themeToggle?.addEventListener('click', () => {
  document.body.classList.toggle('dark');
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  updateThemeLabel();
});

postsGrid?.addEventListener('click', event => {
  const button = event.target.closest('[data-slug]');
  if (button) loadPostDetail(button.dataset.slug);
});

loadMoreButton?.addEventListener('click', loadPosts);

loadPosts();
