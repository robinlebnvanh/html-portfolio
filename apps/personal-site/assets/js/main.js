let allProjects = [];

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
      <div class="tags">${project.tech.map(tech => `<span class="tag">${escapeHtml(tech)}</span>`).join('')}</div>
      <a class="project-link" href="${escapeHtml(project.link || '#')}" target="_blank" rel="noreferrer">${escapeHtml(project.linkLabel || 'View project')} <span aria-hidden="true">↗</span></a>
    </article>
  `).join('');

  requestAnimationFrame(initReveal);
}

async function loadContent() {
  try {
    const [projectsResponse, aboutResponse] = await Promise.all([
      fetch('./data/projects.json'),
      fetch('./data/about.json')
    ]);

    if (!projectsResponse.ok || !aboutResponse.ok) throw new Error('Content could not be loaded.');

    allProjects = await projectsResponse.json();
    const about = await aboutResponse.json();
    skillsList.innerHTML = about.skills.map(skill => `
      <li class="skill-item"><span>${escapeHtml(skill.name)}</span><span class="skill-level">${escapeHtml(skill.level)}%</span></li>
    `).join('');
    renderProjects('all');
  } catch (error) {
    projectGrid.innerHTML = '<p class="empty-state">Selected work is temporarily unavailable.</p>';
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
contactForm.addEventListener('submit', async event => {
  event.preventDefault();
  const status = document.getElementById('form-status');
  const button = contactForm.querySelector('button[type="submit"]');
  button.disabled = true;
  button.innerHTML = 'Sending <span aria-hidden="true">…</span>';

  try {
    const response = await fetch('https://formspree.io/f/maqzgroj', {
      method: 'POST',
      body: new FormData(contactForm),
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) throw new Error('Form submission failed.');
    status.textContent = 'Thank you. I will get back to you shortly.';
    contactForm.reset();
  } catch (error) {
    status.textContent = 'Something went wrong. Please email me directly instead.';
  } finally {
    button.disabled = false;
    button.innerHTML = 'Send enquiry <span aria-hidden="true">↗</span>';
  }
});

document.addEventListener('DOMContentLoaded', initReveal);
loadContent();
