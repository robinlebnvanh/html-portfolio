const state = {
  data: null,
  leads: []
};

let storageKey = "service-business-kit-leads";
const serviceConfig = window.PRJ008_SERVICE_CONFIG || {};
const apiBaseUrl = serviceConfig.apiBaseUrl || "";

const qs = (selector, scope = document) => scope.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    "\"": "&quot;"
  })[char]);
}

function setText(id, value) {
  const element = qs(`#${id}`);
  if (element && value) {
    element.textContent = value;
  }
}

function renderProof(items) {
  const container = qs("#proof-strip");
  container.innerHTML = items.map((item) => `
    <div class="proof-item">
      <strong>${escapeHtml(item.value)}</strong>
      <span>${escapeHtml(item.label)}</span>
    </div>
  `).join("");
}

function renderAudiences(items) {
  const container = qs("#audience-list");
  container.innerHTML = items.map((item) => `<span class="audience-pill">${escapeHtml(item)}</span>`).join("");
}

function renderServices(items) {
  const container = qs("#services-grid");
  const select = qs("#package-select");

  container.innerHTML = items.map((service) => `
    <article class="service-card">
      <div>
        <p class="price">${escapeHtml(service.price)}</p>
        <h3>${escapeHtml(service.name)}</h3>
      </div>
      <p>${escapeHtml(service.summary)}</p>
      <ul class="feature-list">
        ${service.features.map((feature) => `<li>${escapeHtml(feature)}</li>`).join("")}
      </ul>
      <a class="button button-primary" href="#booking">Request this package</a>
    </article>
  `).join("");

  select.innerHTML = items.map((service) => `<option value="${escapeHtml(service.name)}">${escapeHtml(service.name)}</option>`).join("");
}

function renderProcess(items) {
  const container = qs("#process-list");
  container.innerHTML = items.map((item) => `
    <article class="process-item">
      <strong class="process-step">${escapeHtml(item.step)}</strong>
      <div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.body)}</p>
      </div>
    </article>
  `).join("");
}

function renderTestimonials(items) {
  const container = qs("#testimonials-grid");
  container.innerHTML = items.map((item) => `
    <article class="testimonial-card">
      <blockquote>${escapeHtml(item.quote)}</blockquote>
      <footer>${escapeHtml(item.name)} / ${escapeHtml(item.context)}</footer>
    </article>
  `).join("");
}

function renderGallery(items) {
  const container = qs("#gallery-grid");
  container.innerHTML = items.map((item) => `
    <figure class="gallery-item">
      <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" loading="lazy">
      <figcaption class="gallery-caption">${escapeHtml(item.title)}</figcaption>
    </figure>
  `).join("");
}

function renderFaq(items) {
  const container = qs("#faq-list");
  container.innerHTML = items.map((item) => `
    <article class="faq-item">
      <h3>${escapeHtml(item.question)}</h3>
      <p>${escapeHtml(item.answer)}</p>
    </article>
  `).join("");
}

function readLeads() {
  try {
    state.leads = JSON.parse(localStorage.getItem(storageKey)) || [];
  } catch (error) {
    state.leads = [];
  }
}

function writeLeads() {
  localStorage.setItem(storageKey, JSON.stringify(state.leads));
}

async function persistLeadToApi(lead) {
  if (!apiBaseUrl) {
    throw new Error("API base URL is not configured.");
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/leads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source: lead.source,
      business_name: lead.businessName,
      customer_name: lead.name,
      email: lead.email,
      preferred_date: lead.date,
      package_name: lead.package,
      message: lead.message
    })
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `API returned ${response.status}`);
  }
  return payload.lead;
}

function renderLeadSummary() {
  const container = qs("#lead-summary");
  const latest = state.leads.slice(-3).reverse();

  if (!latest.length) {
    container.innerHTML = `
      <div class="lead-summary-item">
        <span>Captured inquiries</span>
        <strong>0</strong>
      </div>
    `;
    return;
  }

  container.innerHTML = latest.map((lead) => `
    <div class="lead-summary-item">
      <span>${escapeHtml(lead.package)}</span>
      <strong>${escapeHtml(lead.date)}</strong>
    </div>
  `).join("");
}

async function handleBookingSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const business = state.data?.business || {
    name: "Service business",
    source: storageKey,
    successMessage: "Inquiry saved."
  };
  const lead = {
    source: business.source || storageKey,
    businessName: business.name,
    name: data.get("name").trim(),
    email: data.get("email").trim(),
    date: data.get("date"),
    package: data.get("package"),
    message: data.get("message").trim(),
    status: "New",
    createdAt: new Date().toISOString()
  };

  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;
  qs("#form-status").textContent = "Saving inquiry...";

  try {
    const savedLead = await persistLeadToApi(lead);
    state.leads.push({ ...lead, id: savedLead.id, status: savedLead.status });
    writeLeads();
    renderLeadSummary();
    form.reset();
    qs("#form-status").textContent = business.successMessage || "Inquiry saved.";
  } catch (error) {
    state.leads.push({ ...lead, status: "local_fallback" });
    writeLeads();
    renderLeadSummary();
    form.reset();
    qs("#form-status").textContent = "Inquiry captured locally. API lead sync is temporarily unavailable.";
  } finally {
    submitButton.disabled = false;
  }
}

function setupNavigation() {
  const toggle = qs("#menu-toggle");
  const links = qs("#nav-links");

  toggle.addEventListener("click", () => {
    const isOpen = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  links.addEventListener("click", (event) => {
    if (event.target.closest("a")) {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
}

async function loadSite() {
  const response = await fetch("data/site.json");
  if (!response.ok) {
    throw new Error("Site data could not be loaded");
  }
  return response.json();
}

function renderSite(data) {
  const { business } = data;
  state.data = data;
  storageKey = business.storageKey || `service-business-leads-${business.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  document.title = business.pageTitle || `${business.name} | Service Business Website Kit`;

  setText("brand-name", business.name);
  setText("brand-meta", business.meta);
  setText("hero-kicker", business.kicker);
  setText("hero-title", business.title);
  setText("hero-intro", business.intro);
  setText("intro-title", business.positioningTitle);
  setText("intro-copy", business.positioningCopy);
  setText("booking-copy", business.bookingCopy);
  setText("footer-name", business.name);

  const hero = qs("#hero-image");
  hero.style.backgroundImage = `url("${business.heroImage}")`;
  hero.setAttribute("aria-label", business.title);

  renderProof(data.proof);
  renderAudiences(data.audiences);
  renderServices(data.services);
  renderProcess(data.process);
  renderTestimonials(data.testimonials);
  renderGallery(data.gallery);
  renderFaq(data.faq);
}

document.addEventListener("DOMContentLoaded", async () => {
  setupNavigation();

  try {
    const data = await loadSite();
    renderSite(data);
  } catch (error) {
    qs("#form-status").textContent = "Template data failed to load.";
  }

  readLeads();
  renderLeadSummary();
  qs("#booking-form").addEventListener("submit", handleBookingSubmit);
});
