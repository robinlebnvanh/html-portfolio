let allProjects = [];

const config = window.PRJ008_CONFIG || {};
const apiBaseUrl = config.apiBaseUrl || '';
const contactNotificationUrl = config.contactNotificationUrl || 'https://formspree.io/f/maqzgroj';
const projectGrid = document.getElementById('projects-grid');
const skillsList = document.getElementById('skills-list');
const themeToggle = document.getElementById('theme-toggle');

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[char]);
}

function renderProjects(filter) {
  const filtered = filter === 'all' ? allProjects : allProjects.filter(project => project.category === filter);

  if (!filtered.length) {
    projectGrid.innerHTML = '<p class="empty-state">No projects in this category yet.</p>';
    return;
  }

  projectGrid.innerHTML = filtered.map((project, index) => `
    <article class="project-card reveal" style="transition-delay: ${index * 90}ms">
      <div class="project-visual ${escapeHtml(project.visual || 'dashboard')}" aria-hidden="true"></div>
      <div class="card-meta"><span>${escapeHtml(project.number)}</span><span>${escapeHtml(project.date)}</span></div>
      <h3>${escapeHtml(project.name)}</h3>
      <p class="project-audience">${escapeHtml(project.audience || 'Product audience')}</p>
      <p>${escapeHtml(project.desc)}</p>
      <p class="project-outcome">${escapeHtml(project.outcome || 'Case study details are being prepared.')}</p>
      <div class="tags">${(project.tech || []).map(tech => `<span class="tag">${escapeHtml(tech)}</span>`).join('')}</div>
      <div class="project-actions">
        <a class="project-link" href="${escapeHtml(project.link || '#')}">${escapeHtml(project.linkLabel || 'View project')} <span aria-hidden="true">↗</span></a>
        ${project.demoLink ? `<a class="project-link project-link-secondary" href="${escapeHtml(project.demoLink)}">${escapeHtml(project.demoLabel || 'Open demo')} <span aria-hidden="true">↗</span></a>` : ''}
      </div>
    </article>
  `).join('');

  requestAnimationFrame(initReveal);
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element && value) element.textContent = value;
}

function renderSkills(skills = []) {
  skillsList.innerHTML = skills.map(skill => `
    <li class="skill-item"><span>${escapeHtml(skill.name)}</span><span class="skill-level">${escapeHtml(skill.level)}%</span></li>
  `).join('');
}

function renderOffers(offers = []) {
  const container = document.getElementById('studio-offers');
  if (!container || !offers.length) return;
  container.innerHTML = offers.map(offer => `
    <article class="studio-card reveal">
      <p class="mono-label">${escapeHtml(offer.kicker)}</p>
      <h3>${escapeHtml(offer.title)}</h3>
      <p>${escapeHtml(offer.description)}</p>
    </article>
  `).join('');
}

function applyPortfolioContent(content) {
  setText('hero-eyebrow', content.hero_eyebrow);
  setText('hero-title', content.hero_title);
  setText('hero-intro', content.hero_intro);
  setText('hero-location', content.hero_location);
  setText('hero-experience', content.hero_experience);
  setText('about-title', content.about_title);
  setText('studio-title', content.studio_title);
  setText('studio-intro', content.studio_intro);
  setText('contact-title', content.contact_title);
  setText('contact-intro', content.contact_intro);

  const aboutBody = document.getElementById('about-body');
  if (aboutBody && Array.isArray(content.about_body)) {
    aboutBody.innerHTML = content.about_body.map(paragraph => `<p>${escapeHtml(paragraph)}</p>`).join('');
  }

  const githubLink = document.getElementById('github-link');
  if (githubLink && content.github_url) githubLink.href = content.github_url;

  const contactLink = document.getElementById('contact-email-link');
  if (contactLink && content.contact_email) {
    contactLink.href = `mailto:${content.contact_email}`;
    contactLink.innerHTML = `${escapeHtml(content.contact_email)} <span aria-hidden="true">↗</span>`;
  }

  renderSkills(content.skills || []);
  renderOffers(content.offers || []);
  allProjects = content.projects || [];
  renderProjects('all');
}

async function loadManagedPortfolioContent() {
  if (!apiBaseUrl) throw new Error('API base URL is not configured.');
  const response = await fetch(`${apiBaseUrl}/api/v1/portfolio/content`);
  if (!response.ok) throw new Error('Managed portfolio content could not be loaded.');
  const payload = await response.json();
  applyPortfolioContent(payload.content);
}

async function loadContent() {
  try {
    await loadManagedPortfolioContent();
  } catch (error) {
    try {
      const [projectsResponse, aboutResponse] = await Promise.all([
        fetch('./data/projects.json'),
        fetch('./data/about.json')
      ]);

      if (!projectsResponse.ok || !aboutResponse.ok) throw new Error('Content could not be loaded.');

      allProjects = await projectsResponse.json();
      const about = await aboutResponse.json();
      renderSkills(about.skills);
      renderProjects('all');
    } catch (error) {
      projectGrid.innerHTML = '<p class="empty-state">Selected work is temporarily unavailable.</p>';
    }
  }
}

const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

function initReveal() {
  document.querySelectorAll('.reveal:not(.visible)').forEach(element => {
    if (element.getBoundingClientRect().top < window.innerHeight * .95) {
      element.classList.add('visible');
    } else {
      revealObserver.observe(element);
    }
  });
}

function updateThemeLabel() {
  const isDark = document.body.classList.contains('dark');
  themeToggle.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
  themeToggle.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode');
}

if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');
updateThemeLabel();
themeToggle.addEventListener('click', () => {
  document.body.classList.toggle('dark');
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  updateThemeLabel();
});

document.querySelectorAll('.filter-btn').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    renderProjects(button.dataset.filter);
  });
});

const contactForm = document.getElementById('contact-form');
async function sendContactNotification(formData) {
  if (!contactNotificationUrl) return false;
  const response = await fetch(contactNotificationUrl, {
    method: 'POST',
    body: formData,
    headers: { Accept: 'application/json' }
  });
  if (!response.ok) throw new Error('Email notification failed.');
  return true;
}

contactForm.addEventListener('submit', async event => {
  event.preventDefault();
  const status = document.getElementById('form-status');
  const button = contactForm.querySelector('button[type="submit"]');
  const formData = new FormData(contactForm);
  button.disabled = true;
  button.innerHTML = 'Sending <span aria-hidden="true">…</span>';
  status.removeAttribute('data-type');

  try {
    if (!apiBaseUrl) throw new Error('API base URL is not configured.');
    const response = await fetch(`${apiBaseUrl}/api/v1/leads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source: 'personal-site',
        business_name: 'Robin Le Portfolio',
        customer_name: String(formData.get('name') || '').trim(),
        email: String(formData.get('email') || '').trim(),
        preferred_date: new Date().toISOString().slice(0, 10),
        package_name: 'Portfolio contact',
        message: String(formData.get('message') || '').trim()
      })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `API returned ${response.status}`);
    status.dataset.type = 'success';
    try {
      await sendContactNotification(formData);
      status.textContent = `Thank you. Your inquiry was saved to the database as Lead #${payload.lead.id}, and an email notification was sent.`;
    } catch (notificationError) {
      status.textContent = `Thank you. Your inquiry was saved to the database as Lead #${payload.lead.id}, but the email notification failed.`;
    }
    contactForm.reset();
  } catch (error) {
    try {
      await sendContactNotification(formData);
      status.dataset.type = 'error';
      status.textContent = `This inquiry was not saved to the database: ${error.message}. An email notification was still sent.`;
      contactForm.reset();
    } catch (notificationError) {
      status.dataset.type = 'error';
      status.textContent = `This inquiry was not saved to the database: ${error.message}. Please email me directly instead.`;
    }
  } finally {
    button.disabled = false;
    button.innerHTML = 'Send enquiry <span aria-hidden="true">↗</span>';
  }
});

document.addEventListener('DOMContentLoaded', initReveal);
loadContent();
