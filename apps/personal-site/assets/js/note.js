const apiBaseUrl = window.PRJ008_CONFIG?.apiBaseUrl || 'http://localhost:8001';

const article = document.getElementById('note-article');
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

function safeImageUrl(value) {
  const url = String(value || '').trim();
  if (!url) return '';
  if (/^https?:\/\//i.test(url) || /^(\.?\.?\/|assets\/)/.test(url)) return url;
  return '';
}

function renderImage(url, alt, className = 'note-inline-image') {
  const safeUrl = safeImageUrl(url);
  if (!safeUrl) return '';
  return `
    <figure class="${className}">
      <img src="${escapeHtml(safeUrl)}" alt="${escapeHtml(alt || '')}" loading="lazy">
      ${alt ? `<figcaption>${escapeHtml(alt)}</figcaption>` : ''}
    </figure>
  `;
}

function renderTextParagraph(text) {
  const body = escapeHtml(text.trim()).replaceAll('\n', '<br>');
  return body ? `<p>${body}</p>` : '';
}

function renderContentBlock(block) {
  const imagePattern = /!\[([^\]]*)\]\(([^)\s]+)\)/g;
  let cursor = 0;
  let html = '';
  let match;

  while ((match = imagePattern.exec(block)) !== null) {
    html += renderTextParagraph(block.slice(cursor, match.index));
    html += renderImage(match[2], match[1]);
    cursor = match.index + match[0].length;
  }

  html += renderTextParagraph(block.slice(cursor));
  return html;
}

function renderContent(content) {
  return String(content || '')
    .split(/\n{2,}/)
    .map(renderContentBlock)
    .join('');
}

function renderArticle(post) {
  const tags = (post.tags || [])
    .map(tag => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join('');
  const cover = renderImage(
    post.cover_image_url,
    post.cover_image_alt || post.title,
    'note-cover-image',
  );

  document.title = `${post.title} | Robin Log`;
  article.innerHTML = `
    <a class="note-back-link" href="blog.html">Back to notes <span aria-hidden="true">↑</span></a>
    <header class="note-header">
      <p class="mono-label">${escapeHtml(post.category)} / ${escapeHtml(formatDate(post.published_at))}</p>
      <h1>${escapeHtml(post.title)}</h1>
      <p class="note-summary">${escapeHtml(post.summary)}</p>
      <div class="tags">${tags}</div>
    </header>
    ${cover}
    <div class="note-content">${renderContent(post.content)}</div>
  `;
}

function renderError(message) {
  article.innerHTML = `
    <a class="note-back-link" href="blog.html">Back to notes <span aria-hidden="true">↑</span></a>
    <p class="mono-label">Robin Log</p>
    <h1>Article unavailable</h1>
    <p class="note-summary">${escapeHtml(message)}</p>
  `;
}

async function loadArticle() {
  const slug = new URLSearchParams(window.location.search).get('slug');
  if (!slug) {
    renderError('Choose a note from the blog index.');
    return;
  }

  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/blog/posts/${encodeURIComponent(slug)}`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const payload = await response.json();
    renderArticle(payload.post);
  } catch (error) {
    renderError('The API could not return this post right now.');
  }
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

loadArticle();
