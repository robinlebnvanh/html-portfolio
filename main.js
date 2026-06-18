// ===== 1. FETCH + RENDER PROJECTS =====
let allProjects = [];

fetch('../data/projects.json')
  .then(res => res.json())
  .then(projects => {
    allProjects = projects;
    renderProjects('all');
  })
  .catch(() => {
    document.getElementById('projects-grid').innerHTML =
      '<p style="color:var(--muted)">Chưa có dự án nào.</p>';
  });

function renderProjects(filter) {
  const filtered = filter === 'all'
    ? allProjects
    : allProjects.filter(p => p.category === filter);

  const grid = document.getElementById('projects-grid');
  if (filtered.length === 0) {
    grid.innerHTML = '<p style="color:var(--muted)">Không có dự án nào.</p>';
    return;
  }
  grid.innerHTML = filtered.map(p => `
    <div class="card">
      <h3>${p.name}</h3>
      <p>${p.desc}</p>
      <div class="tags">
        ${p.tech.map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
      <a href="${p.link || '#'}" target="_blank">Xem dự án →</a>
    </div>
  `).join('');
}


// ===== 2. FETCH + RENDER SKILLS =====
fetch('../data/about.json')
  .then(res => res.json())
  .then(about => {
    const skillsList = document.getElementById('skills-list');
    if (!skillsList) return;
    skillsList.innerHTML = about.skills.map(s => `
      <div class="skill-item">
        <div class="skill-label">
          <span>${s.name}</span>
          <span>${s.level}%</span>
        </div>
        <div class="skill-bar">
          <div class="skill-fill" style="width: ${s.level}%"></div>
        </div>
      </div>
    `).join('');
  })
  .catch(() => {});


// ===== 3. DARK MODE =====
if (localStorage.getItem('theme') === 'light') {
  document.body.classList.add('light');
}

document.getElementById('theme-toggle').addEventListener('click', () => {
  document.body.classList.toggle('light');
  const isLight = document.body.classList.contains('light');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
  document.getElementById('theme-toggle').textContent = isLight ? '☀️' : '🌙';
});


// ===== 4. FILTER =====
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderProjects(btn.dataset.filter);
  });
});
