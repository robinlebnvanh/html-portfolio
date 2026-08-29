const apiBaseUrl = window.PRJ008_CONFIG?.apiBaseUrl || 'http://localhost:8001';
const pageSize = 4;

let offset = 0;
let isLoading = false;

const postsGrid = document.getElementById('blog-posts');
const loadMoreButton = document.getElementById('load-more-posts');
const statusMessage = document.getElementById('blog-status');
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

function safeImageUrl(value) {
  const url = String(value || '').trim();
  if (!url) return '';
  if (/^https?:\/\//i.test(url) || /^(\.?\.?\/|assets\/)/.test(url)) return url;
  return '';
}

function renderPostCard(post) {
  const tags = (post.tags || [])
    .map(tag => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join('');
  const postUrl = `note.html?slug=${encodeURIComponent(post.slug)}`;
  const coverUrl = safeImageUrl(post.cover_image_url);
  const cover = coverUrl
    ? `<span class="blog-card-cover"><img src="${escapeHtml(coverUrl)}" alt="${escapeHtml(post.cover_image_alt || post.title)}" loading="lazy"></span>`
    : `<span class="blog-card-cover blog-card-cover-empty" aria-hidden="true"><span>${escapeHtml(post.category || 'Robin Log')}</span></span>`;

  return `
    <a class="blog-card reveal" href="${escapeHtml(postUrl)}" data-slug="${escapeHtml(post.slug)}" aria-label="Read ${escapeHtml(post.title)}">
      <div class="blog-meta">
        <span>${escapeHtml(formatDate(post.published_at))}</span>
        <span>${escapeHtml(post.category)}</span>
      </div>
      ${cover}
      <h3>${escapeHtml(post.title)}</h3>
      <p>${escapeHtml(post.summary)}</p>
      <div class="tags">${tags}</div>
      <span class="project-link blog-read-link">Read article <span aria-hidden="true">→</span></span>
    </a>
  `;
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

loadMoreButton?.addEventListener('click', loadPosts);

loadPosts();
