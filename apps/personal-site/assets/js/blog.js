const apiBaseUrl = window.PRJ008_CONFIG?.apiBaseUrl || 'http://localhost:8001';
const pageSize = 4;

let offset = 0;
let isLoading = false;

const postsGrid = document.getElementById('blog-posts');
const loadMoreButton = document.getElementById('load-more-posts');
const statusMessage = document.getElementById('blog-status');

if (localStorage.getItem('theme') === 'light') {
  document.body.classList.add('light');
}

document.getElementById('theme-toggle')?.addEventListener('click', () => {
  document.body.classList.toggle('light');
  const isLight = document.body.classList.contains('light');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
  document.getElementById('theme-toggle').textContent = isLight ? '☀️' : '🌙';
});

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
  return new Intl.DateTimeFormat('vi-VN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value));
}

function renderPost(post) {
  const tags = (post.tags || [])
    .map(tag => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join('');

  return `
    <article class="card blog-card reveal">
      <div class="blog-meta">
        <span>${escapeHtml(formatDate(post.published_at))}</span>
        <span>${escapeHtml(post.category)}</span>
      </div>
      <h3>${escapeHtml(post.title)}</h3>
      <p>${escapeHtml(post.summary)}</p>
      <div class="tags">${tags}</div>
      <a href="${apiBaseUrl}/api/v1/blog/posts/${encodeURIComponent(post.slug)}" target="_blank">
        Xem JSON API →
      </a>
    </article>
  `;
}

function setStatus(message, type = 'muted') {
  if (!statusMessage) return;
  statusMessage.textContent = message;
  statusMessage.dataset.type = type;
}

function initReveal() {
  document.querySelectorAll('.reveal').forEach(element => {
    const rect = element.getBoundingClientRect();
    if (rect.top < window.innerHeight) {
      element.classList.add('visible');
    }
  });
}

async function loadPosts() {
  if (isLoading) return;
  isLoading = true;
  loadMoreButton.disabled = true;
  loadMoreButton.textContent = 'Đang tải...';

  try {
    const url = `${apiBaseUrl}/api/v1/blog/posts?limit=${pageSize}&offset=${offset}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const payload = await response.json();
    postsGrid.insertAdjacentHTML('beforeend', payload.posts.map(renderPost).join(''));
    offset += payload.posts.length;

    setStatus(`Đã tải ${offset}/${payload.total} bài.`);
    loadMoreButton.hidden = !payload.has_more;
    loadMoreButton.disabled = false;
    loadMoreButton.textContent = 'Load more';
    initReveal();
  } catch (error) {
    setStatus('Không kết nối được FastAPI. Hãy chạy backend tại localhost:8001.', 'error');
    loadMoreButton.hidden = true;
  } finally {
    isLoading = false;
  }
}

loadMoreButton?.addEventListener('click', loadPosts);
loadPosts();
