const config = window.PRJ008_ADMIN_CONFIG || {};
const apiBaseUrl = config.apiBaseUrl || 'http://localhost:8001';
const tokenKey = 'prj008AdminToken';

const $ = id => document.getElementById(id);

const loginView = $('login-view');
const dashboardView = $('dashboard-view');
const loginForm = $('login-form');
const emailInput = $('admin-email');
const passwordInput = $('admin-password');
const loginStatus = $('login-status');
const logoutButton = $('logout-button');
const refreshStatusButton = $('refresh-status');
const apiStatusValue = $('api-status-value');
const apiStatusDetail = $('api-status-detail');
const blogCountValue = $('blog-count-value');
const blogCountDetail = $('blog-count-detail');
const leadCountValue = $('lead-count-value');
const leadCountDetail = $('lead-count-detail');
const siteCountValue = $('site-count-value');
const siteCountDetail = $('site-count-detail');
const apiBaseUrlValue = $('api-base-url');
const sections = [...document.querySelectorAll('[data-section]')];
const navItems = [...document.querySelectorAll('.nav-item')];
const stockTabs = [...document.querySelectorAll('[data-stock-tab]')];
const stockPanels = [...document.querySelectorAll('[data-stock-panel]')];
const portfolioTabs = [...document.querySelectorAll('[data-portfolio-tab]')];
const portfolioPanels = [...document.querySelectorAll('[data-portfolio-panel]')];
const projectList = $('portfolio-project-list');
const projectEditor = $('portfolio-project-editor');
const projectsJsonField = $('portfolio-projects-json-field');
const projectsJsonToggle = $('portfolio-toggle-json');
const portfolioDirtyStatus = $('portfolio-dirty-status');
const portfolioPreview = $('portfolio-preview');
const portfolioDraftKey = 'prj008PortfolioDraft';
const portfolioVersionsKey = 'prj008PortfolioVersions';

let blogPosts = [];
let stockState = { portfolio: null, journals: {}, auditLogs: [] };
let portfolioContent = null;
let portfolioProjects = [];
let selectedProjectIndex = 0;
let serviceLeads = [];
let leadActivities = {};
let selectedLeadId = null;
let siteChecks = {};

const leadStatuses = ['new', 'contacted', 'proposal_sent', 'booked', 'closed'];
const jobStages = ['awaiting_files', 'editing', 'review', 'revision', 'delivered', 'paid'];
const publicBaseUrl = new URL('../../', window.location.href);

const fallbackSiteRegistry = [
  {
    name: 'Root redirect',
    category: 'redirect',
    visibility: 'public',
    route: '/',
    owner: 'Portfolio',
    description: 'Redirects visitors to the personal portfolio home.',
    url: publicBaseUrl.href,
  },
  {
    name: 'Portfolio home',
    category: 'portfolio',
    visibility: 'public',
    route: '/apps/personal-site/',
    owner: 'Portfolio CMS',
    description: 'Main public profile, product studio positioning, and selected work.',
    url: publicUrl('/apps/personal-site/'),
  },
  {
    name: 'Notes',
    category: 'portfolio',
    visibility: 'public',
    route: '/apps/personal-site/blog.html',
    owner: 'Blog CMS',
    description: 'Public learning notes and database-backed posts.',
    url: publicUrl('/apps/personal-site/blog.html'),
  },
  {
    name: 'Investment Dashboard case study',
    category: 'case-study',
    visibility: 'public',
    route: '/apps/personal-site/case-studies/investment-dashboard.html',
    owner: 'Portfolio CMS',
    description: 'Case study for the stocks dashboard product demo.',
    url: publicUrl('/apps/personal-site/case-studies/investment-dashboard.html'),
  },
  {
    name: 'Fame Lux Nails case study',
    category: 'case-study',
    visibility: 'public',
    route: '/apps/personal-site/case-studies/fame-lux-nails.html',
    owner: 'Portfolio CMS',
    description: 'Case study for the service landing-page demo.',
    url: publicUrl('/apps/personal-site/case-studies/fame-lux-nails.html'),
  },
  {
    name: 'Personal AI Agent case study',
    category: 'case-study',
    visibility: 'public',
    route: '/apps/personal-site/case-studies/personal-ai-agent.html',
    owner: 'Portfolio CMS',
    description: 'Case study for the AI assistant workflow.',
    url: publicUrl('/apps/personal-site/case-studies/personal-ai-agent.html'),
  },
  {
    name: 'Service Business Kit case study',
    category: 'case-study',
    visibility: 'public',
    route: '/apps/personal-site/case-studies/service-business-kit.html',
    owner: 'Portfolio CMS',
    description: 'Case study for reusable booking-ready service websites.',
    url: publicUrl('/apps/personal-site/case-studies/service-business-kit.html'),
  },
  {
    name: 'Photography Studio case study',
    category: 'case-study',
    visibility: 'public',
    route: '/apps/personal-site/case-studies/photography-studio.html',
    owner: 'Portfolio CMS',
    description: 'Case study for wedding, baby, and maternity studio positioning.',
    url: publicUrl('/apps/personal-site/case-studies/photography-studio.html'),
  },
  {
    name: 'Wedding Planner case study',
    category: 'case-study',
    visibility: 'public',
    route: '/apps/personal-site/case-studies/wedding-planner.html',
    owner: 'Portfolio CMS',
    description: 'Case study for inquiry and proposal planning workflow.',
    url: publicUrl('/apps/personal-site/case-studies/wedding-planner.html'),
  },
  {
    name: 'Photoshop Retouching',
    category: 'redirect',
    visibility: 'public',
    route: '/apps/photoshop-retouching/',
    owner: 'Robin Retouch Studio',
    description: 'Market selector redirect for Photoshop service pages.',
    url: publicUrl('/apps/photoshop-retouching/'),
  },
  {
    name: 'Photoshop Vietnam',
    category: 'service',
    visibility: 'public',
    route: '/apps/photoshop-retouching/vi/',
    owner: 'Robin Retouch Studio',
    description: 'Vietnamese Photoshop quote page with VND pricing.',
    url: publicUrl('/apps/photoshop-retouching/vi/'),
  },
  {
    name: 'Photoshop Australia',
    category: 'service',
    visibility: 'public',
    route: '/apps/photoshop-retouching/au/',
    owner: 'Robin Retouch Studio',
    description: 'English Photoshop quote page with AUD pricing.',
    url: publicUrl('/apps/photoshop-retouching/au/'),
  },
  {
    name: 'Service Business Kit',
    category: 'service',
    visibility: 'public',
    route: '/apps/service-business-kit/',
    owner: 'Service demos',
    description: 'Reusable service-business landing page and inquiry pattern.',
    url: publicUrl('/apps/service-business-kit/'),
  },
  {
    name: 'Photography Studio Demo',
    category: 'service',
    visibility: 'public',
    route: '/apps/photography-studio-demo/',
    owner: 'Service demos',
    description: 'Photography studio demo for wedding, baby, and maternity clients.',
    url: publicUrl('/apps/photography-studio-demo/'),
  },
  {
    name: 'Wedding Planner Demo',
    category: 'service',
    visibility: 'public',
    route: '/apps/wedding-planner-demo/',
    owner: 'Service demos',
    description: 'Wedding planning inquiry and proposal demo.',
    url: publicUrl('/apps/wedding-planner-demo/'),
  },
  {
    name: 'Nail Landing Page',
    category: 'demo',
    visibility: 'public',
    route: '/apps/nail-landing-page/',
    owner: 'Service demos',
    description: 'Fame Lux Nails landing-page demo.',
    url: publicUrl('/apps/nail-landing-page/'),
  },
  {
    name: 'Stocks dashboard',
    category: 'demo',
    visibility: 'public',
    route: '/apps/stocks-app/',
    owner: 'Stocks operations',
    description: 'Public shell for investment dashboard views.',
    url: publicUrl('/apps/stocks-app/'),
  },
  {
    name: 'Stocks journal',
    category: 'demo',
    visibility: 'public',
    route: '/apps/stocks-app/journal.html',
    owner: 'Stocks operations',
    description: 'Stock thesis and journal reading surface.',
    url: publicUrl('/apps/stocks-app/journal.html'),
  },
  {
    name: 'Stocks portfolio',
    category: 'demo',
    visibility: 'public',
    route: '/apps/stocks-app/portfolio.html',
    owner: 'Stocks operations',
    description: 'Portfolio dashboard reading surface.',
    url: publicUrl('/apps/stocks-app/portfolio.html'),
  },
  {
    name: 'Admin Console',
    category: 'admin',
    visibility: 'private',
    route: '/apps/admin/',
    owner: 'Admin',
    description: 'Private operator surface for content, leads, stocks, and site structure.',
    url: publicUrl('/apps/admin/'),
  },
  {
    name: 'API health',
    category: 'api',
    visibility: 'system',
    route: '/health',
    owner: 'FastAPI',
    description: 'Render backend health endpoint.',
    url: `${apiBaseUrl}/health`,
    method: 'GET',
  },
  {
    name: 'OpenAPI schema',
    category: 'api',
    visibility: 'system',
    route: '/openapi.json',
    owner: 'FastAPI',
    description: 'Machine-readable API contract.',
    url: `${apiBaseUrl}/openapi.json`,
    method: 'GET',
  },
  {
    name: 'Lead intake API',
    category: 'api',
    visibility: 'system',
    route: '/api/v1/leads',
    owner: 'FastAPI',
    description: 'Public write endpoint used by service booking forms.',
    url: `${apiBaseUrl}/api/v1/leads`,
    checkMode: 'contract',
  },
  {
    name: 'Admin leads API',
    category: 'api',
    visibility: 'private',
    route: '/api/v1/admin/leads',
    owner: 'FastAPI',
    description: 'Authenticated lead management endpoint.',
    url: `${apiBaseUrl}/api/v1/admin/leads`,
    method: 'GET',
    requiresAuth: true,
  },
];
let siteRegistry = [...fallbackSiteRegistry];

const leadStatusLabels = {
  new: 'New',
  contacted: 'Contacted',
  proposal_sent: 'Proposal sent',
  booked: 'Booked',
  closed: 'Closed',
};

const jobStageLabels = {
  awaiting_files: 'Awaiting files',
  editing: 'Editing',
  review: 'Client review',
  revision: 'Revision',
  delivered: 'Delivered',
  paid: 'Paid',
};

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[char]));
}

function semanticClass(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-');
}

function formatDateLabel(value) {
  if (!value) return 'Not set';
  return String(value).slice(0, 10);
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function publicUrl(route) {
  return new URL(String(route || '').replace(/^\//, ''), publicBaseUrl).href;
}

function siteUrl(site) {
  if (site.url) return site.url;
  if (site.urlType === 'api') return `${apiBaseUrl}${site.route}`;
  return publicUrl(site.route);
}

function normalizeSite(site) {
  return {
    ...site,
    url: siteUrl(site),
  };
}

async function loadSiteRegistry() {
  try {
    const response = await fetch('data/site-registry.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Registry returned ${response.status}`);
    const payload = await response.json();
    if (!Array.isArray(payload.sites)) throw new Error('Registry has no sites array.');
    siteRegistry = payload.sites.map(normalizeSite);
    setStatus($('sites-status'), `Loaded ${siteRegistry.length} generated site entries.`, 'success');
  } catch (error) {
    siteRegistry = fallbackSiteRegistry.map(normalizeSite);
    setStatus($('sites-status'), `Using fallback site map: ${error.message}`, 'warning');
  }
  renderSites();
}

function moneyLabel(amount, currency) {
  if (amount === null || amount === undefined || amount === '') return 'No quote';
  return `${Number(amount).toLocaleString('en-US')} ${currency || ''}`.trim();
}

function normalizePhone(value) {
  return String(value || '').replace(/[^\d+]/g, '');
}

function setStatus(element, message, type = 'muted') {
  if (!element) return;
  element.textContent = message;
  element.dataset.type = type;
}

function setPortfolioDirty(isDirty) {
  setStatus(
    portfolioDirtyStatus,
    isDirty ? 'Unsaved changes' : 'No unsaved changes',
    isDirty ? 'warning' : 'success',
  );
}

function labelFromKey(value) {
  return String(value || '')
    .split('-')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function siteBadge(value, prefix = '') {
  const label = prefix ? `${prefix}${labelFromKey(value)}` : labelFromKey(value);
  return `<span class="site-badge ${semanticClass(value)}">${escapeHtml(label)}</span>`;
}

function siteStatusBadge(site) {
  const check = siteChecks[site.name];
  if (site.checkMode === 'contract') {
    return '<span class="site-badge system">OpenAPI contract</span>';
  }
  if (!check) {
    return '<span class="site-badge unchecked">Not checked</span>';
  }
  if (check.ok) {
    return `<span class="site-badge online">${escapeHtml(check.label)}</span>`;
  }
  return `<span class="site-badge offline">${escapeHtml(check.label)}</span>`;
}

function filteredSites() {
  const category = $('site-category-filter')?.value || 'all';
  const visibility = $('site-visibility-filter')?.value || 'all';
  return siteRegistry.filter(site => {
    const categoryMatches = category === 'all' || site.category === category;
    const visibilityMatches = visibility === 'all' || site.visibility === visibility;
    return categoryMatches && visibilityMatches;
  });
}

function renderSiteMetrics(sites = siteRegistry) {
  const metrics = $('site-metrics');
  if (!metrics) return;
  const publicCount = sites.filter(site => site.visibility === 'public').length;
  const privateCount = sites.filter(site => site.visibility === 'private').length;
  const apiCount = sites.filter(site => site.category === 'api').length;
  const checkedCount = sites.filter(site => siteChecks[site.name] || site.checkMode === 'contract').length;
  metrics.innerHTML = [
    ['Visible surfaces', sites.length],
    ['Public', publicCount],
    ['Private', privateCount],
    ['API', apiCount],
    ['Checked', checkedCount],
  ].map(([label, value]) => `
    <article class="site-metric-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </article>
  `).join('');
}

function renderSites() {
  const sites = filteredSites();
  const body = $('sites-body');
  const cards = $('sites-cards');
  if (siteCountValue) siteCountValue.textContent = String(siteRegistry.length);
  if (siteCountDetail) {
    const publicCount = siteRegistry.filter(site => site.visibility === 'public').length;
    const privateCount = siteRegistry.filter(site => site.visibility === 'private').length;
    siteCountDetail.textContent = `${publicCount} public, ${privateCount} private, ${siteRegistry.length} total tracked.`;
  }
  renderSiteMetrics(sites);
  if (!body || !cards) return;
  if (!sites.length) {
    body.innerHTML = '<tr><td colspan="7" class="empty-cell">No sites match this filter.</td></tr>';
    cards.innerHTML = '<p class="empty-note">No sites match this filter.</p>';
    return;
  }

  body.innerHTML = sites.map(site => `
    <tr>
      <td><strong>${escapeHtml(site.name)}</strong><br><span class="empty-note">${escapeHtml(site.description)}</span></td>
      <td>${siteBadge(site.category)}</td>
      <td>${siteBadge(site.visibility)}</td>
      <td><code class="route-code">${escapeHtml(site.route)}</code></td>
      <td>${escapeHtml(site.owner)}</td>
      <td>${siteStatusBadge(site)}</td>
      <td><a class="module-action compact-action" href="${escapeHtml(site.url)}" target="_blank" rel="noreferrer">Open</a></td>
    </tr>
  `).join('');

  cards.innerHTML = sites.map(site => `
    <article class="site-card">
      <div class="site-card-header">
        <div>
          <h4>${escapeHtml(site.name)}</h4>
          <p>${escapeHtml(site.owner)} / ${escapeHtml(site.route)}</p>
        </div>
        ${siteStatusBadge(site)}
      </div>
      <p>${escapeHtml(site.description)}</p>
      <div class="site-card-meta">
        ${siteBadge(site.category)}
        ${siteBadge(site.visibility)}
      </div>
      <a class="module-action compact-action" href="${escapeHtml(site.url)}" target="_blank" rel="noreferrer">Open</a>
    </article>
  `).join('');
}

function adminToken() {
  return sessionStorage.getItem(tokenKey) || '';
}

function authHeaders(withJson = false) {
  return {
    ...(withJson ? { 'Content-Type': 'application/json' } : {}),
    Authorization: `Bearer ${adminToken()}`,
  };
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${apiBaseUrl}${path}`, options);
  if (response.status === 204) return null;

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `API returned ${response.status}`);
  }
  return body;
}

async function checkSite(site) {
  if (site.checkMode === 'contract') {
    const contract = await fetch(`${apiBaseUrl}/openapi.json`).then(response => response.json());
    const exists = Boolean(contract.paths && contract.paths[site.route]);
    return {
      ok: exists,
      label: exists ? 'Contract OK' : 'Missing contract',
    };
  }

  const response = await fetch(site.url, {
    method: site.method || 'HEAD',
    headers: site.requiresAuth ? authHeaders() : {},
  });
  return {
    ok: response.ok,
    label: response.ok ? `HTTP ${response.status}` : `HTTP ${response.status}`,
  };
}

async function checkSitesStatus() {
  const button = $('sites-check');
  if (button) button.disabled = true;
  setStatus($('sites-status'), 'Checking site and API status...');
  const checks = await Promise.allSettled(siteRegistry.map(async site => {
    try {
      return [site.name, await checkSite(site)];
    } catch (error) {
      return [site.name, { ok: false, label: error.message || 'Check failed' }];
    }
  }));
  siteChecks = checks.reduce((nextChecks, result) => {
    if (result.status === 'fulfilled') {
      const [name, check] = result.value;
      nextChecks[name] = check;
    }
    return nextChecks;
  }, {});
  renderSites();
  const failed = Object.values(siteChecks).filter(check => !check.ok).length;
  setStatus(
    $('sites-status'),
    failed ? `${failed} surface checks need attention.` : 'All checked surfaces are reachable.',
    failed ? 'warning' : 'success',
  );
  if (button) button.disabled = false;
}

async function adminRequest(path, options = {}) {
  if (!adminToken()) {
    sessionStorage.removeItem(tokenKey);
    showLogin('Please sign in before loading admin data.');
    throw new Error('Admin session is missing.');
  }
  const hasBody = Boolean(options.body);
  try {
    return await requestJson(path, {
      ...options,
      headers: {
        ...authHeaders(hasBody),
        ...(options.headers || {}),
      },
    });
  } catch (error) {
    if (/401|403|Not authenticated|Invalid|expired/i.test(error.message)) {
      sessionStorage.removeItem(tokenKey);
      showLogin('Session expired. Sign in again.');
    }
    throw error;
  }
}

function showSection(name) {
  const target = sections.some(section => section.dataset.section === name) ? name : 'overview';
  sections.forEach(section => {
    section.hidden = section.dataset.section !== target;
    section.classList.toggle('is-active', section.dataset.section === target);
  });
  navItems.forEach(item => {
    const isActive = item.getAttribute('href') === `#${target}`;
    item.classList.toggle('active', isActive);
    if (isActive) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });
}

function showStockPanel(name) {
  const target = stockPanels.some(panel => panel.dataset.stockPanel === name) ? name : 'holdings';
  stockPanels.forEach(panel => {
    panel.hidden = panel.dataset.stockPanel !== target;
  });
  stockTabs.forEach(tab => {
    const isActive = tab.dataset.stockTab === target;
    tab.classList.toggle('active', isActive);
    tab.setAttribute('aria-selected', String(isActive));
  });
}

function showPortfolioPanel(name) {
  const target = portfolioPanels.some(panel => panel.dataset.portfolioPanel === name) ? name : 'hero';
  portfolioPanels.forEach(panel => {
    panel.hidden = panel.dataset.portfolioPanel !== target;
  });
  portfolioTabs.forEach(tab => {
    const isActive = tab.dataset.portfolioTab === target;
    tab.classList.toggle('active', isActive);
    tab.setAttribute('aria-selected', String(isActive));
  });
}

function currentHashSection() {
  return (window.location.hash || '#overview').replace('#', '') || 'overview';
}

function showDashboard() {
  loginView.hidden = true;
  dashboardView.hidden = false;
  showSection(currentHashSection());
  loadDashboard();
}

function showLogin(message = '') {
  dashboardView.hidden = true;
  loginView.hidden = false;
  passwordInput.value = '';
  setStatus(loginStatus, message);
  emailInput.focus();
}

async function checkHealth() {
  setStatus(apiStatusValue, 'Checking');
  setStatus(apiStatusDetail, 'Calling /health...');
  try {
    const payload = await requestJson('/health');
    setStatus(apiStatusValue, 'Online', 'success');
    setStatus(apiStatusDetail, `${payload.service || 'API'} returned ${payload.status || 'ok'}.`, 'success');
  } catch (error) {
    setStatus(apiStatusValue, 'Offline', 'error');
    setStatus(apiStatusDetail, error.message, 'error');
  }
}

async function loadBlogAdminSummary() {
  setStatus(blogCountValue, '-');
  setStatus(blogCountDetail, 'Loading authenticated blog summary...');
  try {
    const payload = await adminRequest('/api/v1/admin/blog/posts');
    setStatus(blogCountValue, String(payload.total ?? payload.posts?.length ?? 0), 'success');
    setStatus(blogCountDetail, 'Token accepted by the admin blog endpoint.', 'success');
  } catch (error) {
    setStatus(blogCountValue, 'Blocked', 'error');
    setStatus(blogCountDetail, error.message, 'error');
  }
}

async function loadLeadAdminSummary() {
  setStatus(leadCountValue, '-');
  setStatus(leadCountDetail, 'Loading authenticated lead summary...');
  try {
    const payload = await adminRequest('/api/v1/admin/leads');
    setStatus(leadCountValue, String(payload.total ?? payload.leads?.length ?? 0), 'success');
    setStatus(leadCountDetail, 'Token accepted by the admin lead endpoint.', 'success');
  } catch (error) {
    setStatus(leadCountValue, 'Blocked', 'error');
    setStatus(leadCountDetail, error.message, 'error');
  }
}

async function loginAdmin(email, password) {
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `API returned ${response.status}`);
  }
  return response.json();
}

async function validateSession() {
  await adminRequest('/api/v1/auth/me');
}

async function loadDashboard() {
  apiBaseUrlValue.textContent = apiBaseUrl;
  await Promise.all([checkHealth(), loadBlogAdminSummary(), loadLeadAdminSummary()]);
}

function tagsFromInput(value) {
  return value.split(',').map(tag => tag.trim()).filter(Boolean);
}

function linesFromTextarea(id) {
  return $(id).value.split('\n').map(line => line.trim()).filter(Boolean);
}

function splitRows(id, expectedParts) {
  return linesFromTextarea(id).map((line, index) => {
    const parts = line.split('|').map(part => part.trim());
    if (parts.length < expectedParts || parts.some(part => !part)) {
      throw new Error(`Line ${index + 1} in ${id} must use ${expectedParts} pipe-separated values.`);
    }
    return parts;
  });
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function renderBlogList() {
  const list = $('blog-list');
  if (!blogPosts.length) {
    list.innerHTML = '<p class="empty-note">No blog posts in the database.</p>';
    return;
  }
  list.innerHTML = blogPosts.map(post => `
    <button class="item-button" type="button" data-blog-id="${post.id}">
      <strong>${escapeHtml(post.title)}</strong>
      <span class="item-meta"><span class="content-status-badge ${semanticClass(post.status)}">${escapeHtml(post.status)}</span><span>${escapeHtml(post.slug)}</span></span>
    </button>
  `).join('');
}

function fillBlogForm(post = null) {
  $('blog-id').value = post?.id || '';
  $('blog-slug').value = post?.slug || '';
  $('blog-post-status').value = post?.status || 'draft';
  $('blog-title-field').value = post?.title || '';
  $('blog-summary').value = post?.summary || '';
  $('blog-category').value = post?.category || 'build-log';
  $('blog-published-at').value = post?.published_at || '';
  $('blog-tags').value = (post?.tags || []).join(', ');
  $('blog-content').value = post?.content || '';
  $('blog-delete').hidden = !post?.id;
}

function blogPayload() {
  return {
    slug: $('blog-slug').value,
    title: $('blog-title-field').value,
    summary: $('blog-summary').value,
    content: $('blog-content').value,
    category: $('blog-category').value,
    tags: tagsFromInput($('blog-tags').value),
    status: $('blog-post-status').value,
    published_at: $('blog-published-at').value || null,
  };
}

async function loadBlogPosts() {
  try {
    setStatus($('blog-status'), 'Loading blog posts...');
    const payload = await adminRequest('/api/v1/admin/blog/posts');
    blogPosts = payload.posts || [];
    renderBlogList();
    setStatus($('blog-status'), `Loaded ${payload.total ?? blogPosts.length} database posts.`, 'success');
    await loadBlogAdminSummary();
  } catch (error) {
    setStatus($('blog-status'), error.message, 'error');
  }
}

async function saveBlogPost(event) {
  event.preventDefault();
  const postId = $('blog-id').value;
  try {
    setStatus($('blog-status'), 'Saving post...');
    const payload = await adminRequest(
      postId ? `/api/v1/admin/blog/posts/${postId}` : '/api/v1/admin/blog/posts',
      {
        method: postId ? 'PATCH' : 'POST',
        body: JSON.stringify(blogPayload()),
      },
    );
    fillBlogForm(payload.post);
    await loadBlogPosts();
    setStatus($('blog-status'), 'Post saved.', 'success');
  } catch (error) {
    setStatus($('blog-status'), error.message, 'error');
  }
}

async function deleteBlogPost() {
  const postId = $('blog-id').value;
  if (!postId || !confirm('Delete this blog post from the database?')) return;
  try {
    setStatus($('blog-status'), 'Deleting post...');
    await adminRequest(`/api/v1/admin/blog/posts/${postId}`, { method: 'DELETE' });
    fillBlogForm(null);
    await loadBlogPosts();
    setStatus($('blog-status'), 'Post deleted.', 'success');
  } catch (error) {
    setStatus($('blog-status'), error.message, 'error');
  }
}

async function loadStockData() {
  try {
    setStatus($('stocks-status'), 'Loading stocks data...');
    const [portfolio, journals, audit] = await Promise.all([
      adminRequest('/api/v1/stocks/portfolio'),
      adminRequest('/api/v1/stocks/journals'),
      adminRequest('/api/v1/stocks/audit-logs'),
    ]);
    stockState = { portfolio, journals, auditLogs: audit.logs || [] };
    renderStockViews();
    setStatus($('stocks-status'), 'Loaded from FastAPI / Neon PostgreSQL.', 'success');
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

function stockFilterValues() {
  return {
    ticker: $('stock-filter-ticker').value.trim().toUpperCase(),
    type: $('stock-filter-type').value,
    from: $('stock-filter-from').value,
    to: $('stock-filter-to').value,
  };
}

function filteredTrades(journals) {
  const filter = stockFilterValues();
  return allTrades(journals).filter(trade => (
    (!filter.ticker || trade.ticker === filter.ticker)
    && (filter.type === 'all' || trade.type === filter.type)
    && (!filter.from || trade.date >= filter.from)
    && (!filter.to || trade.date <= filter.to)
  ));
}

function renderStockSummary() {
  const holdings = stockState.portfolio?.holdings || [];
  const active = holdings.filter(holding => holding.quantity > 0);
  const invested = active.reduce((total, holding) => total + (holding.quantity * holding.avg_cost), 0);
  const coveredByStop = active.filter(holding => holding.stop_loss !== null && holding.stop_loss !== undefined).length;
  const trades = allTrades(stockState.journals || {});
  $('stock-summary').innerHTML = [
    ['Invested cost', invested.toLocaleString()],
    ['Open positions', active.length],
    ['Open quantity', active.reduce((total, holding) => total + holding.quantity, 0).toLocaleString()],
    ['Stop-loss coverage', `${coveredByStop}/${active.length}`],
    ['Trade records', trades.length],
  ].map(([label, value]) => `<article class="stock-summary-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`).join('');
}

function renderStockViews() {
  const filter = stockFilterValues();
  const portfolio = stockState.portfolio || {};
  const holdings = (portfolio.holdings || []).filter(holding => !filter.ticker || holding.ticker === filter.ticker);
  const watchlist = (portfolio.watchlist || []).filter(ticker => !filter.ticker || ticker === filter.ticker);
  const journals = Object.fromEntries(Object.entries(stockState.journals || {}).filter(([ticker]) => !filter.ticker || ticker === filter.ticker));
  renderStockSummary();
  renderHoldings(holdings);
  renderWatchlist(watchlist);
  renderJournals(journals);
  renderTrades(filteredTrades(stockState.journals || {}));
  renderStockAudit(stockState.auditLogs || [], filter);
}

function renderHoldings(holdings) {
  const body = $('holdings-body');
  if (!holdings.length) {
    body.innerHTML = '<tr><td colspan="7" class="empty-cell">No holdings.</td></tr>';
    return;
  }
  body.innerHTML = holdings.map(holding => `
    <tr>
      <td><span class="ticker-badge">${escapeHtml(holding.ticker)}</span></td>
      <td>${Number(holding.quantity).toLocaleString()}</td>
      <td>${Number(holding.avg_cost).toLocaleString()}</td>
      <td>${escapeHtml(holding.entry_date)}</td>
      <td><span class="holding-status-badge ${semanticClass(holding.status)}">${escapeHtml(holding.status)}</span></td>
      <td>${(holding.targets || []).map(Number).map(value => value.toLocaleString()).join(', ') || '-'}</td>
      <td class="row-actions">
        <button type="button" data-holding-edit="${holding.id}">Edit</button>
        <button type="button" data-holding-delete="${holding.id}" class="danger-link">Close</button>
      </td>
    </tr>
  `).join('');
}

function holdingPayload() {
  const targets = $('holding-targets').value.split(',').map(value => value.trim()).filter(Boolean).map(Number);
  if (targets.some(value => !Number.isInteger(value) || value < 0)) {
    throw new Error('Targets must be non-negative integers separated by commas.');
  }
  return {
    ticker: $('holding-ticker').value.trim().toUpperCase(),
    quantity: Number($('holding-quantity').value),
    avg_cost: Number($('holding-avg-cost').value),
    entry_date: $('holding-entry-date').value,
    stop_loss: $('holding-stop-loss').value ? Number($('holding-stop-loss').value) : null,
    status: $('holding-status').value,
    note: $('holding-note').value.trim() || null,
    targets,
  };
}

function editHolding(holding) {
  $('holding-id').value = holding.id;
  $('holding-ticker').value = holding.ticker;
  $('holding-ticker').disabled = true;
  $('holding-quantity').value = holding.quantity;
  $('holding-avg-cost').value = holding.avg_cost;
  $('holding-entry-date').value = holding.entry_date;
  $('holding-stop-loss').value = holding.stop_loss ?? '';
  $('holding-status').value = holding.status;
  $('holding-targets').value = (holding.targets || []).join(', ');
  $('holding-note').value = holding.note || '';
  $('holding-submit').textContent = 'Save adjustment';
  $('holding-cancel').hidden = false;
}

function resetHoldingForm() {
  $('holding-form').reset();
  $('holding-id').value = '';
  $('holding-ticker').disabled = false;
  $('holding-status').value = 'HOLDING';
  $('holding-submit').textContent = 'Add holding';
  $('holding-cancel').hidden = true;
}

async function saveHolding(event) {
  event.preventDefault();
  try {
    const id = $('holding-id').value;
    const payload = holdingPayload();
    if (!payload.ticker || !payload.entry_date) throw new Error('Ticker and entry date are required.');
    await adminRequest(id ? `/api/v1/stocks/holdings/${id}` : '/api/v1/stocks/holdings', {
      method: id ? 'PATCH' : 'POST',
      body: JSON.stringify(id ? Object.fromEntries(Object.entries(payload).filter(([key]) => key !== 'ticker')) : payload),
    });
    resetHoldingForm();
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

async function deleteHolding(id) {
  const holding = (stockState.portfolio?.holdings || []).find(item => item.id === id);
  if (!holding || !confirm(`Close ${holding.ticker}: this creates a zero-quantity adjustment and keeps all trade history.`)) return;
  try {
    await adminRequest(`/api/v1/stocks/holdings/${id}`, { method: 'DELETE' });
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

function renderWatchlist(watchlist) {
  const list = $('watchlist-list');
  if (!watchlist.length) {
    list.innerHTML = '<span class="empty-note">No watchlist tickers.</span>';
    return;
  }
  list.innerHTML = watchlist.map(ticker => `
    <span class="chip"><strong>${escapeHtml(ticker)}</strong><button type="button" data-watch-delete="${escapeHtml(ticker)}">Delete</button></span>
  `).join('');
}

async function saveWatchlistItem(event) {
  event.preventDefault();
  const ticker = $('watchlist-ticker').value.trim().toUpperCase();
  if (!ticker) {
    setStatus($('stocks-status'), 'Watchlist ticker is required.', 'error');
    return;
  }
  try {
    await adminRequest('/api/v1/stocks/watchlist', {
      method: 'POST',
      body: JSON.stringify({ ticker }),
    });
    $('watchlist-ticker').value = '';
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

async function deleteWatchlistItem(ticker) {
  if (!confirm(`Delete ${ticker} from watchlist?`)) return;
  try {
    await adminRequest(`/api/v1/stocks/watchlist/${encodeURIComponent(ticker)}`, { method: 'DELETE' });
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

function renderJournals(journals) {
  const rows = Object.values(journals);
  const body = $('journals-body');
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="5" class="empty-cell">No journals.</td></tr>';
    return;
  }
  body.innerHTML = rows.map(journal => `
    <tr>
      <td><span class="ticker-badge">${escapeHtml(journal.ticker)}</span></td>
      <td>${escapeHtml(journal.buffett || '-').slice(0, 90)}</td>
      <td>${(journal.bull || []).length}</td>
      <td>${(journal.bear || []).length}</td>
      <td class="row-actions">
        <button type="button" data-journal-edit="${escapeHtml(journal.ticker)}">Edit</button>
        <button type="button" data-journal-delete="${escapeHtml(journal.ticker)}" class="danger-link">Delete</button>
      </td>
    </tr>
  `).join('');
}

function editJournal(ticker) {
  const journal = stockState.journals[ticker];
  if (!journal) return;
  $('journal-ticker').value = journal.ticker;
  $('journal-buffett').value = journal.buffett || '';
  $('journal-bull').value = (journal.bull || []).join('\n');
  $('journal-bear').value = (journal.bear || []).join('\n');
}

async function saveJournal(event) {
  event.preventDefault();
  const ticker = $('journal-ticker').value.trim().toUpperCase();
  if (!ticker) {
    setStatus($('stocks-status'), 'Journal ticker is required.', 'error');
    return;
  }
  const exists = Boolean(stockState.journals[ticker]);
  const payload = {
    ticker,
    buffett: $('journal-buffett').value.trim(),
    bull: linesFromTextarea('journal-bull'),
    bear: linesFromTextarea('journal-bear'),
  };
  try {
    await adminRequest(exists ? `/api/v1/stocks/journals/${encodeURIComponent(ticker)}` : '/api/v1/stocks/journals', {
      method: exists ? 'PATCH' : 'POST',
      body: JSON.stringify(exists ? { buffett: payload.buffett, bull: payload.bull, bear: payload.bear } : payload),
    });
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

async function deleteJournal(ticker = '') {
  const target = ticker || $('journal-ticker').value.trim().toUpperCase();
  if (!target) {
    setStatus($('stocks-status'), 'Choose a journal ticker to delete.', 'error');
    return;
  }
  if (!confirm(`Delete journal ${target} and related trades?`)) return;
  try {
    await adminRequest(`/api/v1/stocks/journals/${encodeURIComponent(target)}`, { method: 'DELETE' });
    $('journal-form').reset();
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

function allTrades(journals) {
  return Object.values(journals).flatMap(journal => (journal.trades || []).map(trade => ({ ...trade, ticker: trade.ticker || journal.ticker })));
}

function renderTrades(rows) {
  const body = $('trades-body');
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="9" class="empty-cell">No trades.</td></tr>';
    return;
  }
  body.innerHTML = rows.map(trade => `
    <tr>
      <td><span class="ticker-badge">${escapeHtml(trade.ticker)}</span></td>
      <td>${escapeHtml(trade.date)}</td>
      <td><span class="trade-type-badge ${semanticClass(trade.type)}">${escapeHtml(trade.type)}</span></td>
      <td>${Number(trade.quantity || 0).toLocaleString()}</td>
      <td>${Number(trade.price).toLocaleString()}</td>
      <td>${trade.stop_loss == null ? '-' : Number(trade.stop_loss).toLocaleString()}</td>
      <td>${escapeHtml(trade.pnl || '-')}</td>
      <td>${escapeHtml(trade.note || '-')}</td>
      <td class="row-actions">
        <button type="button" data-trade-edit="${trade.id}">Edit</button>
        <button type="button" data-trade-delete="${trade.id}" class="danger-link">Delete</button>
      </td>
    </tr>
  `).join('');
}

function renderStockAudit(logs, filter) {
  const rows = logs.filter(log => !filter.ticker || log.ticker === filter.ticker);
  const body = $('stock-audit-body');
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="6" class="empty-cell">No matching admin changes.</td></tr>';
    return;
  }
  body.innerHTML = rows.map(log => {
    const before = log.before_json ? JSON.parse(log.before_json) : null;
    const after = log.after_json ? JSON.parse(log.after_json) : null;
    const change = after || before || {};
    return `<tr>
      <td>${escapeHtml(formatDateLabel(log.created_at))}</td>
      <td>${escapeHtml(log.actor)}</td>
      <td>${escapeHtml(log.action)}</td>
      <td>${escapeHtml(log.entity_type)} #${escapeHtml(log.entity_id || '-')}</td>
      <td>${log.ticker ? `<span class="ticker-badge">${escapeHtml(log.ticker)}</span>` : '-'}</td>
      <td class="audit-change">${escapeHtml(JSON.stringify(change))}</td>
    </tr>`;
  }).join('');
}

function editTrade(id) {
  const trade = allTrades(stockState.journals).find(item => item.id === id);
  if (!trade) return;
  $('trade-id').value = trade.id;
  $('trade-ticker').value = trade.ticker;
  $('trade-ticker').disabled = true;
  $('trade-date').value = trade.date;
  $('trade-type').value = trade.type;
  $('trade-quantity').value = trade.quantity || 0;
  $('trade-price').value = trade.price;
  $('trade-stop-loss').value = trade.stop_loss ?? '';
  $('trade-pnl').value = trade.pnl || '';
  $('trade-note').value = trade.note || '';
  $('trade-submit').textContent = 'Save trade';
  $('trade-cancel').hidden = false;
}

function resetTradeForm() {
  $('trade-form').reset();
  $('trade-id').value = '';
  $('trade-ticker').disabled = false;
  $('trade-date').value = today();
  $('trade-submit').textContent = 'Add trade';
  $('trade-cancel').hidden = true;
}

async function saveTrade(event) {
  event.preventDefault();
  const id = $('trade-id').value;
  const payload = {
    ticker: $('trade-ticker').value.trim().toUpperCase(),
    date: $('trade-date').value,
    type: $('trade-type').value,
    quantity: Number($('trade-quantity').value),
    price: Number($('trade-price').value),
    stop_loss: $('trade-stop-loss').value ? Number($('trade-stop-loss').value) : null,
    pnl: $('trade-pnl').value.trim() || null,
    note: $('trade-note').value.trim() || null,
  };
  if (!payload.ticker || !payload.date || payload.quantity <= 0) {
    setStatus($('stocks-status'), 'Ticker, trade date, and positive quantity are required.', 'error');
    return;
  }
  try {
    await adminRequest(id ? `/api/v1/stocks/trades/${id}` : '/api/v1/stocks/trades', {
      method: id ? 'PATCH' : 'POST',
      body: JSON.stringify(id ? Object.fromEntries(Object.entries(payload).filter(([key]) => key !== 'ticker')) : payload),
    });
    resetTradeForm();
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

async function deleteTrade(id) {
  if (!confirm('Delete this trade?')) return;
  try {
    await adminRequest(`/api/v1/stocks/trades/${id}`, { method: 'DELETE' });
    await loadStockData();
  } catch (error) {
    setStatus($('stocks-status'), error.message, 'error');
  }
}

function skillsToText(skills = []) {
  return skills.map(skill => `${skill.name} | ${skill.level}`).join('\n');
}

function offersToText(offers = []) {
  return offers.map(offer => `${offer.kicker} | ${offer.title} | ${offer.description}`).join('\n');
}

function parseSkills() {
  return splitRows('portfolio-skills', 2).map(([name, levelText]) => {
    const level = Number(levelText);
    if (!Number.isInteger(level) || level < 0 || level > 100) {
      throw new Error('Skill levels must be whole numbers from 0 to 100.');
    }
    return { name, level };
  });
}

function parseOffers() {
  return splitRows('portfolio-offers', 3).map(([kicker, title, ...descriptionParts]) => ({
    kicker,
    title,
    description: descriptionParts.join(' | '),
  }));
}

function defaultProject(nextId) {
  const number = String(nextId).padStart(2, '0');
  return {
    id: nextId,
    number,
    name: 'New project',
    audience: 'Target audience',
    desc: 'Short project description',
    outcome: 'What this project proves.',
    tech: [],
    category: 'frontend',
    link: 'case-studies/new-project.html',
    demoLink: '../new-project/',
    github: 'https://github.com/robinlebnvanh/html-portfolio',
    date: 'Draft',
    visual: 'dashboard',
    linkLabel: 'Read case study',
    demoLabel: 'Open demo',
  };
}

function projectField(project, index, field, label, options = {}) {
  const value = project[field] ?? '';
  if (options.textarea) {
    return `
      <label class="field">
        <span>${label}</span>
        <textarea data-project-index="${index}" data-project-field="${field}" rows="${options.rows || 3}" ${options.required ? 'required' : ''}>${escapeHtml(value)}</textarea>
      </label>
    `;
  }
  if (options.select) {
    return `
      <label class="field">
        <span>${label}</span>
        <select data-project-index="${index}" data-project-field="${field}">
          ${options.select.map(option => `<option value="${escapeHtml(option)}" ${option === value ? 'selected' : ''}>${escapeHtml(option)}</option>`).join('')}
        </select>
      </label>
    `;
  }
  return `
    <label class="field">
      <span>${label}</span>
      <input data-project-index="${index}" data-project-field="${field}" value="${escapeHtml(value)}" ${options.type ? `type="${options.type}"` : ''} ${options.required ? 'required' : ''}>
    </label>
  `;
}

function renderPortfolioProjectList() {
  $('portfolio-project-count').textContent = `${portfolioProjects.length} selected project${portfolioProjects.length === 1 ? '' : 's'}.`;
  if (!portfolioProjects.length) {
    projectList.innerHTML = '<p class="empty-note">No projects. Add one project before saving.</p>';
    return;
  }
  projectList.innerHTML = portfolioProjects.map((project, index) => `
    <button class="project-list-button ${index === selectedProjectIndex ? 'active' : ''}" type="button" data-project-select="${index}">
      <strong>${escapeHtml(project.number || String(index + 1).padStart(2, '0'))} / ${escapeHtml(project.name || 'Untitled project')}</strong>
      <span>${escapeHtml(project.category || 'uncategorized')} / ${escapeHtml(project.date || 'No label')}</span>
    </button>
  `).join('');
}

function renderPortfolioProjectEditor() {
  if (!portfolioProjects.length) {
    projectEditor.innerHTML = '<p class="empty-note">Select or add a project to edit its content.</p>';
    renderPortfolioProjectList();
    return;
  }
  const index = Math.min(selectedProjectIndex, portfolioProjects.length - 1);
  const project = portfolioProjects[index];
  selectedProjectIndex = index;
  projectEditor.innerHTML = `
    <article class="project-editor-card" data-project-card="${index}">
      <div class="project-editor-header">
        <div class="project-editor-title">
          <strong>${escapeHtml(project.number || String(index + 1).padStart(2, '0'))} / ${escapeHtml(project.name || 'Untitled project')}</strong>
          <span>${escapeHtml(project.audience || 'No audience set')}</span>
        </div>
        <div class="project-editor-controls">
          <button type="button" data-project-move="up" data-project-index="${index}" ${index === 0 ? 'disabled' : ''}>Up</button>
          <button type="button" data-project-move="down" data-project-index="${index}" ${index === portfolioProjects.length - 1 ? 'disabled' : ''}>Down</button>
          <button class="danger-link" type="button" data-project-delete="${index}">Delete</button>
        </div>
      </div>
      <div class="form-grid three">
        ${projectField(project, index, 'id', 'ID', { type: 'number', required: true })}
        ${projectField(project, index, 'number', 'Number', { required: true })}
        ${projectField(project, index, 'date', 'Label', { required: true })}
        ${projectField(project, index, 'name', 'Name', { required: true })}
        ${projectField(project, index, 'category', 'Category', { select: ['tool', 'frontend', 'backend', 'full-stack', 'automation'] })}
        ${projectField(project, index, 'visual', 'Visual key')}
      </div>
      ${projectField(project, index, 'audience', 'Audience', { required: true })}
      ${projectField(project, index, 'desc', 'Description', { textarea: true, rows: 3, required: true })}
      ${projectField(project, index, 'outcome', 'Outcome', { textarea: true, rows: 3, required: true })}
      <div class="form-grid">
        ${projectField({ ...project, tech: (project.tech || []).join(', ') }, index, 'tech', 'Tech tags')}
        ${projectField(project, index, 'github', 'GitHub URL')}
        ${projectField(project, index, 'link', 'Case study link', { required: true })}
        ${projectField(project, index, 'demoLink', 'Demo link')}
        ${projectField(project, index, 'linkLabel', 'Case study label')}
        ${projectField(project, index, 'demoLabel', 'Demo label')}
      </div>
    </article>
  `;
  renderPortfolioProjectList();
}

function syncSelectedProjectFromEditor() {
  const card = projectEditor.querySelector('[data-project-card]');
  if (!card) return;
  const project = {};
  card.querySelectorAll('[data-project-field]').forEach(input => {
    const field = input.dataset.projectField;
    project[field] = input.value.trim();
  });
  project.id = Number(project.id);
  project.tech = tagsFromInput(project.tech || '');
  portfolioProjects[selectedProjectIndex] = project;
}

function projectsFromEditor() {
  syncSelectedProjectFromEditor();
  return portfolioProjects;
}

function syncProjectsJsonFromEditor() {
  $('portfolio-projects').value = JSON.stringify(projectsFromEditor(), null, 2);
}

function replaceProjects(projects, nextSelectedIndex = selectedProjectIndex) {
  portfolioProjects = projects;
  selectedProjectIndex = Math.max(0, Math.min(nextSelectedIndex, Math.max(0, portfolioProjects.length - 1)));
  $('portfolio-projects').value = JSON.stringify(projects, null, 2);
  renderPortfolioProjectEditor();
}

function parseProjects() {
  try {
    const projects = JSON.parse($('portfolio-projects').value);
    if (!Array.isArray(projects) || !projects.length) {
      throw new Error('Projects JSON must be a non-empty array.');
    }
    return projects.map(project => ({
      ...project,
      tech: Array.isArray(project.tech) ? project.tech : [],
    }));
  } catch (error) {
    throw new Error(`Projects JSON is invalid: ${error.message}`);
  }
}

function fillPortfolioForm(content) {
  portfolioContent = content;
  $('portfolio-hero-eyebrow').value = content.hero_eyebrow || '';
  $('portfolio-hero-title').value = content.hero_title || '';
  $('portfolio-hero-intro').value = content.hero_intro || '';
  $('portfolio-hero-location').value = content.hero_location || '';
  $('portfolio-hero-experience').value = content.hero_experience || '';
  $('portfolio-about-title').value = content.about_title || '';
  $('portfolio-about-body').value = (content.about_body || []).join('\n');
  $('portfolio-github-url').value = content.github_url || '';
  $('portfolio-skills').value = skillsToText(content.skills || []);
  $('portfolio-studio-title').value = content.studio_title || '';
  $('portfolio-studio-intro').value = content.studio_intro || '';
  $('portfolio-offers').value = offersToText(content.offers || []);
  replaceProjects(content.projects || []);
  $('portfolio-contact-title').value = content.contact_title || '';
  $('portfolio-contact-intro').value = content.contact_intro || '';
  $('portfolio-contact-email').value = content.contact_email || '';
  setPortfolioDirty(false);
  renderPortfolioPreview(content);
}

function portfolioPayload() {
  syncProjectsJsonFromEditor();
  return {
    hero_eyebrow: $('portfolio-hero-eyebrow').value.trim(),
    hero_title: $('portfolio-hero-title').value.trim(),
    hero_intro: $('portfolio-hero-intro').value.trim(),
    hero_location: $('portfolio-hero-location').value.trim(),
    hero_experience: $('portfolio-hero-experience').value.trim(),
    about_title: $('portfolio-about-title').value.trim(),
    about_body: linesFromTextarea('portfolio-about-body'),
    github_url: $('portfolio-github-url').value.trim(),
    studio_title: $('portfolio-studio-title').value.trim(),
    studio_intro: $('portfolio-studio-intro').value.trim(),
    offers: parseOffers(),
    contact_title: $('portfolio-contact-title').value.trim(),
    contact_intro: $('portfolio-contact-intro').value.trim(),
    contact_email: $('portfolio-contact-email').value.trim(),
    skills: parseSkills(),
    projects: parseProjects(),
  };
}

function isValidUrlOrRelative(value) {
  if (!value) return true;
  try {
    new URL(value, window.location.href);
    return true;
  } catch {
    return false;
  }
}

function validatePortfolioPayload(payload) {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.contact_email)) {
    throw new Error('Portfolio contact email is invalid.');
  }
  payload.projects.forEach(project => {
    ['link', 'demoLink', 'github'].forEach(field => {
      if (!isValidUrlOrRelative(project[field])) {
        throw new Error(`${project.name || 'Project'} has an invalid ${field}.`);
      }
    });
  });
}

function savePortfolioDraft() {
  try {
    localStorage.setItem(portfolioDraftKey, JSON.stringify(portfolioPayload()));
  } catch (error) {
    setStatus($('portfolio-status'), `Draft autosave skipped: ${error.message}`, 'error');
  }
}

function portfolioVersions() {
  try {
    return JSON.parse(localStorage.getItem(portfolioVersionsKey) || '[]');
  } catch {
    return [];
  }
}

function savePortfolioVersion(content) {
  if (!content) return;
  const versions = portfolioVersions();
  versions.unshift({
    saved_at: new Date().toISOString(),
    content,
  });
  localStorage.setItem(portfolioVersionsKey, JSON.stringify(versions.slice(0, 5)));
}

function restorePortfolioDraft() {
  const draft = localStorage.getItem(portfolioDraftKey);
  if (!draft) {
    setStatus($('portfolio-status'), 'No local draft found.', 'warning');
    return;
  }
  try {
    fillPortfolioForm(JSON.parse(draft));
    setPortfolioDirty(true);
    setStatus($('portfolio-status'), 'Local draft restored. Review before saving.', 'success');
  } catch (error) {
    setStatus($('portfolio-status'), `Draft restore failed: ${error.message}`, 'error');
  }
}

function restoreLastPortfolioVersion() {
  const [lastVersion] = portfolioVersions();
  if (!lastVersion?.content) {
    setStatus($('portfolio-status'), 'No local version found.', 'warning');
    return;
  }
  fillPortfolioForm(lastVersion.content);
  setPortfolioDirty(true);
  setStatus($('portfolio-status'), `Restored version from ${formatDateLabel(lastVersion.saved_at)}.`, 'success');
}

function renderPortfolioPreview(content = null) {
  if (!portfolioPreview) return;
  const payload = content || portfolioPayload();
  const projects = payload.projects || [];
  const offers = payload.offers || [];
  portfolioPreview.innerHTML = `
    <div class="preview-header">
      <span class="module-kicker">Preview</span>
      <strong>${escapeHtml(payload.hero_title || 'Untitled portfolio')}</strong>
      <p>${escapeHtml(payload.hero_intro || '')}</p>
    </div>
    <div class="preview-grid">
      <section>
        <h4>Offers</h4>
        ${offers.slice(0, 4).map(offer => `
          <p><strong>${escapeHtml(offer.title)}</strong><br><span>${escapeHtml(offer.description)}</span></p>
        `).join('') || '<p class="empty-note">No offers.</p>'}
      </section>
      <section>
        <h4>Selected work</h4>
        ${projects.slice(0, 6).map(project => `
          <p><strong>${escapeHtml(project.number)} / ${escapeHtml(project.name)}</strong><br><span>${escapeHtml(project.category)} / ${escapeHtml(project.date)}</span></p>
        `).join('') || '<p class="empty-note">No projects.</p>'}
      </section>
    </div>
  `;
}

async function loadPortfolioContent() {
  try {
    setStatus($('portfolio-status'), 'Loading portfolio content...');
    const payload = await adminRequest('/api/v1/admin/portfolio/content');
    fillPortfolioForm(payload.content);
    setStatus($('portfolio-status'), 'Loaded managed portfolio content.', 'success');
  } catch (error) {
    setStatus($('portfolio-status'), error.message, 'error');
  }
}

async function savePortfolioContent(event) {
  event.preventDefault();
  try {
    setStatus($('portfolio-status'), 'Saving portfolio content...');
    const payloadToSave = portfolioPayload();
    validatePortfolioPayload(payloadToSave);
    savePortfolioVersion(portfolioContent);
    const payload = await adminRequest('/api/v1/admin/portfolio/content', {
      method: 'PATCH',
      body: JSON.stringify(payloadToSave),
    });
    fillPortfolioForm(payload.content);
    localStorage.removeItem(portfolioDraftKey);
    setStatus($('portfolio-status'), 'Portfolio content saved.', 'success');
    setPortfolioDirty(false);
  } catch (error) {
    setStatus($('portfolio-status'), error.message, 'error');
  }
}

function leadStatusOptions(current) {
  return leadStatuses.map(statusValue => `
    <option value="${statusValue}" ${statusValue === current ? 'selected' : ''}>${leadStatusLabels[statusValue]}</option>
  `).join('');
}

function jobStageOptions(current) {
  return [''].concat(jobStages).map(stage => `
    <option value="${stage}" ${stage === (current || '') ? 'selected' : ''}>${stage ? jobStageLabels[stage] : 'Not a job yet'}</option>
  `).join('');
}

function leadStatusBadge(status) {
  const label = leadStatusLabels[status] || String(status || 'new').replace('_', ' ');
  return `<span class="lead-status-badge ${escapeHtml(status || 'new')}">${escapeHtml(label)}</span>`;
}

function jobStageBadge(stage) {
  if (!stage) return '<span class="lead-status-badge">Lead only</span>';
  return `<span class="lead-status-badge job-${escapeHtml(stage)}">${escapeHtml(jobStageLabels[stage] || stage)}</span>`;
}

function leadContactLine(lead) {
  return [lead.email, lead.phone].filter(Boolean).map(escapeHtml).join('<br>') || '<span class="empty-note">No contact method</span>';
}

function filteredLeads() {
  const channel = $('lead-channel-filter').value;
  return serviceLeads.filter(lead => channel === 'all' || lead.channel === channel);
}

function renderLeadMetrics(leads) {
  const metrics = $('lead-metrics');
  const today = todayIso();
  const overdue = leads.filter(lead => lead.follow_up_at && lead.follow_up_at < today && lead.status !== 'closed').length;
  const booked = leads.filter(lead => lead.status === 'booked').length;
  const activeJobs = leads.filter(lead => lead.job_stage && !['delivered', 'paid'].includes(lead.job_stage)).length;
  const dueSoon = leads.filter(lead => lead.deadline_at && lead.deadline_at <= today && lead.job_stage && !['delivered', 'paid'].includes(lead.job_stage)).length;
  metrics.innerHTML = [
    ['Visible leads', leads.length],
    ['Booked', booked],
    ['Active jobs', activeJobs],
    ['Follow-up overdue', overdue],
    ['Job due today', dueSoon],
  ].map(([label, value]) => `
    <article class="lead-metric-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </article>
  `).join('');
}

function renderLeadPipeline(leads) {
  const board = $('lead-pipeline');
  board.innerHTML = leadStatuses.map(status => {
    const items = leads.filter(lead => lead.status === status);
    return `
      <section class="pipeline-column">
        <div class="pipeline-heading">
          <strong>${leadStatusLabels[status]}</strong>
          <span>${items.length}</span>
        </div>
        ${items.slice(0, 6).map(lead => `
          <button class="pipeline-card" type="button" data-lead-open="${lead.id}">
            <strong>${escapeHtml(lead.customer_name)}</strong>
            <span>${escapeHtml(lead.package_name)} / ${formatDateLabel(lead.follow_up_at)}</span>
          </button>
        `).join('') || '<p class="empty-note">No leads.</p>'}
      </section>
    `;
  }).join('');
}

function quickActionLinks(lead) {
  const links = [];
  if (lead.email) {
    links.push(`<a class="module-action" href="mailto:${encodeURIComponent(lead.email)}?subject=${encodeURIComponent(`Re: ${lead.package_name}`)}">Email</a>`);
  }
  if (lead.phone) {
    const phone = normalizePhone(lead.phone);
    links.push(`<a class="module-action" href="tel:${escapeHtml(phone)}">Call</a>`);
    links.push(`<a class="module-action" href="https://zalo.me/${escapeHtml(phone.replace(/^\\+?84/, '0'))}" target="_blank" rel="noreferrer">Zalo</a>`);
    links.push(`<a class="module-action" href="https://wa.me/${escapeHtml(phone.replace(/^\\+/, ''))}" target="_blank" rel="noreferrer">WhatsApp</a>`);
  }
  links.push(`<button class="module-action" type="button" data-copy-quote="${lead.id}">Copy quote</button>`);
  return links.join('');
}

function renderLeadTimeline(leadId) {
  const activities = leadActivities[leadId] || [];
  if (!activities.length) return '<p class="empty-note">No timeline activity yet.</p>';
  return activities.map(activity => `
    <article class="timeline-item">
      <span>${escapeHtml(activity.activity_type)} / ${formatDateLabel(activity.created_at)}</span>
      <p>${escapeHtml(activity.note)}</p>
    </article>
  `).join('');
}

function renderLeadDetail(lead = null) {
  const panel = $('lead-detail-panel');
  if (!lead) {
    panel.innerHTML = '<p class="empty-note">Select a lead to review timeline and job details.</p>';
    return;
  }
  selectedLeadId = lead.id;
  panel.innerHTML = `
    <div class="detail-header">
      <div>
        <p class="eyebrow">Lead detail</p>
        <h4>${escapeHtml(lead.customer_name)}</h4>
        <p>${escapeHtml(lead.business_name)} / ${escapeHtml(lead.package_name)}</p>
      </div>
      <div class="detail-badges">
        ${leadStatusBadge(lead.status)}
        ${jobStageBadge(lead.job_stage)}
      </div>
    </div>
    <div class="quick-actions">${quickActionLinks(lead)}</div>
    <form class="job-editor" data-job-form="${lead.id}">
      <div class="form-grid three">
        <label class="field"><span>Job stage</span><select data-job-stage="${lead.id}">${jobStageOptions(lead.job_stage)}</select></label>
        <label class="field"><span>Quote</span><input data-job-quote="${lead.id}" type="number" min="0" step="1" value="${escapeHtml(lead.quoted_amount ?? '')}" placeholder="150000"></label>
        <label class="field"><span>Currency</span><select data-job-currency="${lead.id}"><option value="">-</option><option value="VND" ${lead.quote_currency === 'VND' ? 'selected' : ''}>VND</option><option value="AUD" ${lead.quote_currency === 'AUD' ? 'selected' : ''}>AUD</option><option value="USD" ${lead.quote_currency === 'USD' ? 'selected' : ''}>USD</option></select></label>
        <label class="field"><span>Deadline</span><input data-job-deadline="${lead.id}" type="date" value="${escapeHtml(lead.deadline_at || '')}"></label>
        <label class="field"><span>Revisions</span><input data-job-revisions="${lead.id}" type="number" min="0" step="1" value="${escapeHtml(lead.revision_count ?? 0)}"></label>
        <label class="field"><span>Paid date</span><input data-job-paid="${lead.id}" type="date" value="${escapeHtml(lead.paid_at || '')}"></label>
      </div>
      <label class="field"><span>Client files</span><input data-job-files="${lead.id}" value="${escapeHtml(lead.file_url || '')}" placeholder="Google Drive / Dropbox / WeTransfer link"></label>
      <label class="field"><span>Delivery link</span><input data-job-delivery="${lead.id}" value="${escapeHtml(lead.delivery_url || '')}" placeholder="Final delivery link"></label>
      <div class="form-actions">
        <button class="primary-button" type="button" data-job-save="${lead.id}">Save job</button>
      </div>
    </form>
    <div class="timeline-block">
      <div class="block-heading">
        <h4>Timeline</h4>
        <button class="module-action" type="button" data-activity-load="${lead.id}">Refresh timeline</button>
      </div>
      <div class="timeline-list">${renderLeadTimeline(lead.id)}</div>
    </div>
  `;
}

function renderLeads(leads) {
  const body = $('leads-body');
  const cards = $('leads-cards');
  const visibleLeads = leads;
  renderLeadMetrics(visibleLeads);
  renderLeadPipeline(visibleLeads);
  if (!leads.length) {
    body.innerHTML = '<tr><td colspan="9" class="empty-cell">No service leads for this filter.</td></tr>';
    cards.innerHTML = '<p class="empty-note">No service leads for this filter.</p>';
    renderLeadDetail(null);
    return;
  }

  body.innerHTML = leads.map(lead => `
    <tr data-lead-row="${lead.id}">
      <td>${escapeHtml(lead.channel || 'form')}<br><span class="empty-note">${escapeHtml(lead.source)} / ${escapeHtml(lead.business_name)}</span></td>
      <td><strong>${escapeHtml(lead.customer_name)}</strong><br><span class="empty-note">${leadContactLine(lead)}</span></td>
      <td><input class="lead-date-input" type="date" data-lead-follow-up="${lead.id}" value="${escapeHtml(lead.follow_up_at || '')}"><br><span class="empty-note">${escapeHtml(lead.preferred_date || 'No preferred date')}</span></td>
      <td>${escapeHtml(lead.package_name)}<br>${jobStageBadge(lead.job_stage)}<br><span class="empty-note">${moneyLabel(lead.quoted_amount, lead.quote_currency)}</span></td>
      <td>${escapeHtml(lead.message).slice(0, 180)}</td>
      <td>
        ${leadStatusBadge(lead.status)}
        <select class="lead-status-select" data-lead-status="${lead.id}">
          ${leadStatusOptions(lead.status)}
        </select>
      </td>
      <td><textarea class="lead-note-input" data-lead-note="${lead.id}" placeholder="Next action">${escapeHtml(lead.admin_note || '')}</textarea></td>
      <td><textarea class="lead-note-input" data-lead-activity="${lead.id}" placeholder="Add call/email note"></textarea></td>
      <td class="row-actions">
        <button type="button" data-lead-open="${lead.id}">Open</button>
        <button type="button" data-lead-save="${lead.id}">Save</button>
      </td>
    </tr>
  `).join('');

  cards.innerHTML = leads.map(lead => `
    <article class="lead-card" data-lead-row="${lead.id}">
      <div class="lead-card-header">
        <div>
          <h4>${escapeHtml(lead.customer_name)}</h4>
          <p class="lead-card-meta">${escapeHtml(lead.channel || 'form')} / ${escapeHtml(lead.email || lead.phone || 'No contact method')}</p>
        </div>
        ${leadStatusBadge(lead.status)}
      </div>
      <p class="lead-card-meta">${escapeHtml(lead.source)} / ${escapeHtml(lead.business_name)} / ${escapeHtml(lead.package_name)}</p>
      <p class="lead-card-meta">${jobStageBadge(lead.job_stage)} / ${moneyLabel(lead.quoted_amount, lead.quote_currency)} / Deadline: ${formatDateLabel(lead.deadline_at)}</p>
      <p class="lead-card-meta">Follow-up: ${escapeHtml(lead.follow_up_at || 'Not set')} / Preferred: ${escapeHtml(lead.preferred_date || 'Not set')}</p>
      <p class="lead-card-message">${escapeHtml(lead.message).slice(0, 220)}</p>
      <div class="lead-card-controls">
        <label class="field">
          <span>Status</span>
          <select class="lead-status-select" data-lead-status="${lead.id}">
            ${leadStatusOptions(lead.status)}
          </select>
        </label>
        <label class="field">
          <span>Follow-up date</span>
          <input class="lead-date-input" type="date" data-lead-follow-up="${lead.id}" value="${escapeHtml(lead.follow_up_at || '')}">
        </label>
        <label class="field">
          <span>Admin note</span>
          <textarea class="lead-note-input" data-lead-note="${lead.id}" placeholder="Next action">${escapeHtml(lead.admin_note || '')}</textarea>
        </label>
        <label class="field">
          <span>Activity note</span>
          <textarea class="lead-note-input" data-lead-activity="${lead.id}" placeholder="Add call/email note"></textarea>
        </label>
        <div class="form-actions">
          <button class="module-action" type="button" data-lead-open="${lead.id}">Open detail</button>
          <button class="module-action" type="button" data-lead-save="${lead.id}">Save lead</button>
        </div>
      </div>
    </article>
  `).join('');

  const selected = serviceLeads.find(lead => lead.id === selectedLeadId) || leads[0];
  renderLeadDetail(selected);
}

function manualLeadPayload() {
  const email = $('manual-lead-email').value.trim();
  const phone = $('manual-lead-phone').value.trim();
  if (!email && !phone) {
    throw new Error('Email or phone is required.');
  }
  return {
    source: 'admin-manual',
    channel: $('manual-lead-channel').value,
    business_name: 'Robin Le Portfolio',
    customer_name: $('manual-lead-name').value.trim(),
    email: email || null,
    phone: phone || null,
    preferred_date: null,
    follow_up_at: $('manual-lead-follow-up').value || null,
    package_name: $('manual-lead-package').value.trim(),
    message: $('manual-lead-message').value.trim(),
  };
}

async function createManualLead(event) {
  event.preventDefault();
  try {
    setStatus($('leads-status'), 'Creating manual lead...');
    await adminRequest('/api/v1/admin/leads', {
      method: 'POST',
      body: JSON.stringify(manualLeadPayload()),
    });
    $('manual-lead-form').reset();
    $('manual-lead-package').value = 'Portfolio contact';
    await loadLeads();
    setStatus($('leads-status'), 'Manual lead created.', 'success');
  } catch (error) {
    setStatus($('leads-status'), error.message, 'error');
  }
}

async function loadLeads() {
  try {
    const filter = $('lead-status-filter').value;
    const query = $('lead-search').value.trim();
    const params = new URLSearchParams({ status_filter: filter });
    if (query) params.set('q', query);
    setStatus($('leads-status'), 'Loading service leads...');
    const payload = await adminRequest(`/api/v1/admin/leads?${params.toString()}`);
    serviceLeads = payload.leads || [];
    renderLeads(filteredLeads());
    setStatus($('leads-status'), `Loaded ${payload.total ?? serviceLeads.length} service leads.`, 'success');
    await loadLeadAdminSummary();
  } catch (error) {
    setStatus($('leads-status'), error.message, 'error');
  }
}

async function openLeadDetail(leadId) {
  const lead = serviceLeads.find(item => item.id === Number(leadId));
  if (!lead) return;
  selectedLeadId = lead.id;
  renderLeadDetail(lead);
  await loadLeadActivities(lead.id);
}

async function loadLeadActivities(leadId) {
  try {
    const payload = await adminRequest(`/api/v1/admin/leads/${leadId}/activities`);
    leadActivities[leadId] = payload.activities || [];
    const lead = serviceLeads.find(item => item.id === Number(leadId));
    renderLeadDetail(lead);
  } catch (error) {
    setStatus($('leads-status'), error.message, 'error');
  }
}

async function saveLead(leadId, trigger = null) {
  const leadRow = trigger?.closest(`[data-lead-row="${leadId}"]`) || document;
  const statusSelect = leadRow.querySelector(`[data-lead-status="${leadId}"]`);
  const noteInput = leadRow.querySelector(`[data-lead-note="${leadId}"]`);
  const followUpInput = leadRow.querySelector(`[data-lead-follow-up="${leadId}"]`);
  const activityInput = leadRow.querySelector(`[data-lead-activity="${leadId}"]`);
  try {
    setStatus($('leads-status'), 'Saving lead...');
    await adminRequest(`/api/v1/admin/leads/${leadId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        status: statusSelect?.value,
        admin_note: noteInput?.value || null,
        follow_up_at: followUpInput?.value || null,
      }),
    });
    if (activityInput?.value.trim()) {
      await adminRequest(`/api/v1/admin/leads/${leadId}/activities`, {
        method: 'POST',
        body: JSON.stringify({
          activity_type: 'note',
          note: activityInput.value.trim(),
        }),
      });
    }
    await loadLeads();
    setStatus($('leads-status'), 'Lead updated.', 'success');
  } catch (error) {
    setStatus($('leads-status'), error.message, 'error');
  }
}

async function saveLeadJob(leadId, trigger = null) {
  const panel = trigger?.closest(`[data-job-form="${leadId}"]`) || document;
  const jobStage = panel.querySelector(`[data-job-stage="${leadId}"]`)?.value || null;
  const quoteValue = panel.querySelector(`[data-job-quote="${leadId}"]`)?.value;
  const revisionsValue = panel.querySelector(`[data-job-revisions="${leadId}"]`)?.value;
  try {
    setStatus($('leads-status'), 'Saving job details...');
    await adminRequest(`/api/v1/admin/leads/${leadId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        status: jobStage && jobStage !== 'paid' ? 'booked' : undefined,
        job_stage: jobStage,
        quoted_amount: quoteValue === '' ? null : Number(quoteValue),
        quote_currency: panel.querySelector(`[data-job-currency="${leadId}"]`)?.value || null,
        deadline_at: panel.querySelector(`[data-job-deadline="${leadId}"]`)?.value || null,
        file_url: panel.querySelector(`[data-job-files="${leadId}"]`)?.value || null,
        delivery_url: panel.querySelector(`[data-job-delivery="${leadId}"]`)?.value || null,
        revision_count: revisionsValue === '' ? 0 : Number(revisionsValue),
        paid_at: panel.querySelector(`[data-job-paid="${leadId}"]`)?.value || null,
      }),
    });
    await adminRequest(`/api/v1/admin/leads/${leadId}/activities`, {
      method: 'POST',
      body: JSON.stringify({
        activity_type: 'job_update',
        note: `Job updated: ${jobStage ? jobStageLabels[jobStage] : 'Lead only'}.`,
      }),
    });
    await loadLeads();
    await loadLeadActivities(leadId);
    setStatus($('leads-status'), 'Job details saved.', 'success');
  } catch (error) {
    setStatus($('leads-status'), error.message, 'error');
  }
}

async function copyLeadQuote(leadId) {
  const lead = serviceLeads.find(item => item.id === Number(leadId));
  if (!lead) return;
  const text = [
    `Hi ${lead.customer_name},`,
    '',
    `Thanks for your Photoshop editing request: ${lead.package_name}.`,
    `Quote: ${moneyLabel(lead.quoted_amount, lead.quote_currency)}.`,
    `Estimated deadline: ${formatDateLabel(lead.deadline_at)}.`,
    '',
    'Please send the original files and any reference/example images before I start.',
  ].join('\n');
  try {
    await navigator.clipboard.writeText(text);
    setStatus($('leads-status'), 'Quote summary copied.', 'success');
  } catch (error) {
    setStatus($('leads-status'), `Copy failed: ${error.message}`, 'error');
  }
}

loginForm.addEventListener('submit', async event => {
  event.preventDefault();
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  if (!email || !password) {
    setStatus(loginStatus, 'Email and password are required.', 'error');
    return;
  }
  setStatus(loginStatus, 'Signing in...');
  try {
    const payload = await loginAdmin(email, password);
    sessionStorage.setItem(tokenKey, payload.access_token);
    passwordInput.value = '';
    showDashboard();
  } catch (error) {
    sessionStorage.removeItem(tokenKey);
    setStatus(loginStatus, error.message, 'error');
  }
});

logoutButton.addEventListener('click', async () => {
  if (adminToken()) {
    await fetch(`${apiBaseUrl}/api/v1/auth/logout`, {
      method: 'POST',
      headers: authHeaders(),
    }).catch(() => {});
  }
  sessionStorage.removeItem(tokenKey);
  showLogin('Signed out for this browser session.');
});

window.addEventListener('hashchange', () => showSection(currentHashSection()));
refreshStatusButton.addEventListener('click', loadDashboard);
stockTabs.forEach(tab => {
  tab.addEventListener('click', () => showStockPanel(tab.dataset.stockTab));
});

$('blog-load').addEventListener('click', loadBlogPosts);
$('blog-form').addEventListener('submit', saveBlogPost);
$('blog-new').addEventListener('click', () => fillBlogForm(null));
$('blog-delete').addEventListener('click', deleteBlogPost);
$('blog-list').addEventListener('click', event => {
  const button = event.target.closest('[data-blog-id]');
  if (!button) return;
  const post = blogPosts.find(item => String(item.id) === button.dataset.blogId);
  fillBlogForm(post);
});

$('stocks-load').addEventListener('click', loadStockData);
['stock-filter-ticker', 'stock-filter-type', 'stock-filter-from', 'stock-filter-to'].forEach(id => {
  $(id).addEventListener(id === 'stock-filter-ticker' ? 'input' : 'change', renderStockViews);
});
$('stock-clear-filters').addEventListener('click', () => {
  $('stock-filter-ticker').value = '';
  $('stock-filter-type').value = 'all';
  $('stock-filter-from').value = '';
  $('stock-filter-to').value = '';
  renderStockViews();
});
$('holding-form').addEventListener('submit', saveHolding);
$('holding-cancel').addEventListener('click', resetHoldingForm);
$('holdings-body').addEventListener('click', event => {
  const editButton = event.target.closest('[data-holding-edit]');
  const deleteButton = event.target.closest('[data-holding-delete]');
  if (editButton) {
    const holding = (stockState.portfolio?.holdings || []).find(item => item.id === Number(editButton.dataset.holdingEdit));
    if (holding) editHolding(holding);
  }
  if (deleteButton) deleteHolding(Number(deleteButton.dataset.holdingDelete));
});

$('watchlist-form').addEventListener('submit', saveWatchlistItem);
$('watchlist-list').addEventListener('click', event => {
  const button = event.target.closest('[data-watch-delete]');
  if (button) deleteWatchlistItem(button.dataset.watchDelete);
});

$('journal-form').addEventListener('submit', saveJournal);
$('journal-delete').addEventListener('click', () => deleteJournal());
$('journals-body').addEventListener('click', event => {
  const editButton = event.target.closest('[data-journal-edit]');
  const deleteButton = event.target.closest('[data-journal-delete]');
  if (editButton) editJournal(editButton.dataset.journalEdit);
  if (deleteButton) deleteJournal(deleteButton.dataset.journalDelete);
});

$('trade-form').addEventListener('submit', saveTrade);
$('trade-cancel').addEventListener('click', resetTradeForm);
$('trades-body').addEventListener('click', event => {
  const editButton = event.target.closest('[data-trade-edit]');
  const deleteButton = event.target.closest('[data-trade-delete]');
  if (editButton) editTrade(Number(editButton.dataset.tradeEdit));
  if (deleteButton) deleteTrade(Number(deleteButton.dataset.tradeDelete));
});

$('portfolio-load').addEventListener('click', loadPortfolioContent);
$('portfolio-form').addEventListener('submit', savePortfolioContent);
$('portfolio-form').addEventListener('input', () => {
  setPortfolioDirty(true);
  savePortfolioDraft();
});
$('portfolio-reset').addEventListener('click', () => {
  if (portfolioContent) fillPortfolioForm(portfolioContent);
});
$('portfolio-preview-button').addEventListener('click', () => renderPortfolioPreview());
$('portfolio-restore-draft').addEventListener('click', restorePortfolioDraft);
$('portfolio-restore-version').addEventListener('click', restoreLastPortfolioVersion);
portfolioTabs.forEach(tab => {
  tab.addEventListener('click', () => showPortfolioPanel(tab.dataset.portfolioTab));
});
$('portfolio-add-project').addEventListener('click', () => {
  const projects = projectsFromEditor();
  const nextId = Math.max(0, ...projects.map(project => Number(project.id) || 0)) + 1;
  replaceProjects([...projects, defaultProject(nextId)], projects.length);
  showPortfolioPanel('projects');
  setPortfolioDirty(true);
});
projectsJsonToggle.addEventListener('click', () => {
  syncProjectsJsonFromEditor();
  const shouldShow = projectsJsonField.hidden;
  projectsJsonField.hidden = !shouldShow;
  projectsJsonToggle.setAttribute('aria-expanded', String(shouldShow));
});
projectList.addEventListener('click', event => {
  const button = event.target.closest('[data-project-select]');
  if (!button) return;
  syncProjectsJsonFromEditor();
  selectedProjectIndex = Number(button.dataset.projectSelect);
  renderPortfolioProjectEditor();
});
projectEditor.addEventListener('input', () => {
  syncProjectsJsonFromEditor();
  renderPortfolioProjectList();
});
projectEditor.addEventListener('click', event => {
  const deleteButton = event.target.closest('[data-project-delete]');
  const moveButton = event.target.closest('[data-project-move]');
  if (deleteButton) {
    const index = Number(deleteButton.dataset.projectDelete);
    const projects = projectsFromEditor();
    if (projects.length <= 1) {
      setStatus($('portfolio-status'), 'Portfolio needs at least one project.', 'error');
      return;
    }
    replaceProjects(projects.filter((_, projectIndex) => projectIndex !== index), Math.max(0, index - 1));
    setPortfolioDirty(true);
  }
  if (moveButton) {
    const index = Number(moveButton.dataset.projectIndex);
    const direction = moveButton.dataset.projectMove;
    const nextIndex = direction === 'up' ? index - 1 : index + 1;
    const projects = projectsFromEditor();
    if (nextIndex < 0 || nextIndex >= projects.length) return;
    [projects[index], projects[nextIndex]] = [projects[nextIndex], projects[index]];
    replaceProjects(projects, nextIndex);
    setPortfolioDirty(true);
  }
});
$('portfolio-projects').addEventListener('change', () => {
  try {
    replaceProjects(parseProjects(), 0);
    setPortfolioDirty(true);
  } catch (error) {
    setStatus($('portfolio-status'), error.message, 'error');
  }
});

$('sites-check').addEventListener('click', checkSitesStatus);
$('site-category-filter').addEventListener('change', renderSites);
$('site-visibility-filter').addEventListener('change', renderSites);

$('leads-load').addEventListener('click', loadLeads);
$('manual-lead-form').addEventListener('submit', createManualLead);
$('lead-status-filter').addEventListener('change', loadLeads);
$('lead-channel-filter').addEventListener('change', () => renderLeads(filteredLeads()));
$('lead-search').addEventListener('input', () => {
  clearTimeout(window.leadSearchTimer);
  window.leadSearchTimer = setTimeout(loadLeads, 280);
});
$('leads-body').addEventListener('click', event => {
  const openButton = event.target.closest('[data-lead-open]');
  const saveButton = event.target.closest('[data-lead-save]');
  if (openButton) openLeadDetail(Number(openButton.dataset.leadOpen));
  if (saveButton) saveLead(Number(saveButton.dataset.leadSave), saveButton);
});
$('leads-cards').addEventListener('click', event => {
  const openButton = event.target.closest('[data-lead-open]');
  const saveButton = event.target.closest('[data-lead-save]');
  if (openButton) openLeadDetail(Number(openButton.dataset.leadOpen));
  if (saveButton) saveLead(Number(saveButton.dataset.leadSave), saveButton);
});
$('lead-pipeline').addEventListener('click', event => {
  const openButton = event.target.closest('[data-lead-open]');
  if (openButton) openLeadDetail(Number(openButton.dataset.leadOpen));
});
$('lead-detail-panel').addEventListener('click', event => {
  const activityButton = event.target.closest('[data-activity-load]');
  const jobButton = event.target.closest('[data-job-save]');
  const quoteButton = event.target.closest('[data-copy-quote]');
  if (activityButton) loadLeadActivities(Number(activityButton.dataset.activityLoad));
  if (jobButton) saveLeadJob(Number(jobButton.dataset.jobSave), jobButton);
  if (quoteButton) copyLeadQuote(Number(quoteButton.dataset.copyQuote));
});

fillBlogForm(null);
resetHoldingForm();
resetTradeForm();
showStockPanel('holdings');
showPortfolioPanel('hero');
apiBaseUrlValue.textContent = apiBaseUrl;
loadSiteRegistry();

if (adminToken()) {
  validateSession().then(showDashboard).catch(() => {
    sessionStorage.removeItem(tokenKey);
    showLogin('Session expired. Sign in again.');
  });
} else {
  showLogin();
}
