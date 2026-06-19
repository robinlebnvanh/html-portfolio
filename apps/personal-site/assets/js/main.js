// ===== 1. FETCH + RENDER PROJECTS =====
let allProjects = [];

fetch('./data/projects.json')
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
  grid.innerHTML = filtered.map((p, i) => `
    <div class="card reveal" style="transition-delay:${i * 0.1}s">
      <h3>${p.name}</h3>
      <p>${p.desc}</p>
      <div class="tags">
        ${p.tech.map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
      <a href="${p.link || '#'}" target="_blank">Xem dự án →</a>
    </div>
  `).join('');
  // Đợi 1 tick để DOM cập nhật xong rồi mới observe
  setTimeout(initReveal, 50);
}


// ===== 2. FETCH + RENDER SKILLS =====
fetch('./data/about.json')
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


// ===== SCROLL ANIMATIONS =====
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target); // Unobserve sau khi đã hiện
    }
  });
}, { threshold: 0.1 });

function initReveal() {
  document.querySelectorAll('.reveal').forEach(el => {
    // Nếu element đã trong viewport → hiện luôn, không cần observe
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight) {
      el.classList.add('visible');
    } else {
      revealObserver.observe(el);
    }
  });
}

// Gọi khi DOM load xong (cho h2 và các element tĩnh)
document.addEventListener('DOMContentLoaded', initReveal);

// ===== CONTACT FORM =====
const contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const status = document.getElementById('form-status');
    const btn = contactForm.querySelector('button[type=submit]');

    btn.textContent = 'Đang gửi...';
    btn.disabled = true;

    const res = await fetch('https://formspree.io/f/maqzgroj', {  // ← đổi endpoint
      method: 'POST',
      body: new FormData(contactForm),
      headers: { 'Accept': 'application/json' }
    });

    if (res.ok) {
      status.textContent = '✅ Gửi thành công! Mình sẽ reply sớm.';
      status.style.color = '#34d399';
      contactForm.reset();
    } else {
      status.textContent = '❌ Lỗi — thử lại sau nhé.';
      status.style.color = '#f87171';
    }

    status.style.display = 'block';
    btn.textContent = 'Gửi →';
    btn.disabled = false;
  });
}