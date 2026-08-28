const config = window.PRJ008_PHOTOSHOP_CONFIG || {};
const apiBaseUrl = config.apiBaseUrl || "";

function qs(selector, scope = document) {
  return scope.querySelector(selector);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    "\"": "&quot;"
  })[char]);
}

function getPageConfig() {
  const locale = document.documentElement.lang === "en-AU" ? "au" : "vi";
  return {
    locale,
    storageKey: `photoshop-retouching-${locale}-leads`,
    businessName: locale === "au" ? "Robin Retouch Studio Australia" : "Robin Retouch Studio Vietnam",
    source: locale === "au" ? "photoshop-retouching-au" : "photoshop-retouching-vi",
    saving: locale === "au" ? "Sending quote request..." : "Đang gửi yêu cầu báo giá...",
    saved: locale === "au"
      ? "Thanks. Your request was saved. I will confirm pricing and timeline before starting."
      : "Mình đã nhận yêu cầu. Mình sẽ báo giá và timeline rõ ràng trước khi bắt đầu.",
    fallback: locale === "au"
      ? "The API is unavailable, so this request was saved in this browser only. Please email if urgent."
      : "API đang không khả dụng nên yêu cầu chỉ được lưu trên trình duyệt này. Nếu gấp, vui lòng email trực tiếp.",
    latestTitle: locale === "au" ? "Latest local requests" : "Yêu cầu mới trên trình duyệt",
    empty: locale === "au" ? "No local requests yet" : "Chưa có yêu cầu local"
  };
}

function trackEvent(name, params = {}) {
  if (typeof window.gtag === "function") {
    window.gtag("event", name, params);
    return;
  }

  if (Array.isArray(window.dataLayer)) {
    window.dataLayer.push({ event: name, ...params });
  }
}

function setupNavigation() {
  const button = qs("#menu-toggle");
  const links = qs("#nav-links");
  if (!button || !links) return;

  button.addEventListener("click", () => {
    const isOpen = links.classList.toggle("open");
    button.setAttribute("aria-expanded", String(isOpen));
  });

  links.addEventListener("click", (event) => {
    const link = event.target.closest("a");
    if (link) {
      trackEvent("retouching_nav_click", {
        target: link.getAttribute("href"),
        locale: getPageConfig().locale
      });
      links.classList.remove("open");
      button.setAttribute("aria-expanded", "false");
    }
  });

  document.querySelectorAll(".language-link").forEach((link) => {
    link.addEventListener("click", () => {
      trackEvent("retouching_language_switch", {
        target: link.getAttribute("href"),
        locale: getPageConfig().locale
      });
    });
  });
}

function readLocalLeads(storageKey) {
  try {
    return JSON.parse(localStorage.getItem(storageKey)) || [];
  } catch (error) {
    return [];
  }
}

function writeLocalLead(storageKey, lead) {
  const leads = readLocalLeads(storageKey);
  leads.push(lead);
  localStorage.setItem(storageKey, JSON.stringify(leads.slice(-10)));
}

function renderLeadSummary() {
  const page = getPageConfig();
  const container = qs("#lead-summary");
  if (!container) return;

  const leads = readLocalLeads(page.storageKey).slice(-3).reverse();
  if (!leads.length) {
    container.innerHTML = `
      <div class="lead-summary-item">
        <span>${escapeHtml(page.latestTitle)}</span>
        <strong>${escapeHtml(page.empty)}</strong>
      </div>
    `;
    return;
  }

  container.innerHTML = leads.map((lead) => `
    <div class="lead-summary-item">
      <span>${escapeHtml(lead.packageName)}</span>
      <strong>${escapeHtml(lead.deadline || lead.market)}</strong>
    </div>
  `).join("");
}

async function persistLead(lead) {
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
      preferred_date: lead.deadline || new Date().toISOString().slice(0, 10),
      package_name: `${lead.packageName} / ${lead.market} / ${lead.currency}`,
      message: [
        `Market: ${lead.market}`,
        `Currency: ${lead.currency}`,
        `Phone/Zalo: ${lead.phone || "Not provided"}`,
        `Image count: ${lead.imageCount || "Not provided"}`,
        `Image link: ${lead.imageLink || "Not provided"}`,
        `Budget: ${lead.budget || "Not provided"}`,
        `Brief: ${lead.message}`
      ].join("\n")
    })
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `API returned ${response.status}`);
  }
  return payload.lead;
}

function setupQuoteForm() {
  const form = qs("#quote-form");
  const status = qs("#form-status");
  if (!form || !status) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const page = getPageConfig();
    const formData = new FormData(form);
    const button = form.querySelector("button[type='submit']");
    const lead = {
      source: page.source,
      businessName: page.businessName,
      market: form.dataset.market || (page.locale === "au" ? "Australia" : "Vietnam"),
      currency: form.dataset.currency || (page.locale === "au" ? "AUD" : "VND"),
      name: String(formData.get("name") || "").trim(),
      email: String(formData.get("email") || "").trim(),
      phone: String(formData.get("phone") || "").trim(),
      packageName: String(formData.get("package") || "").trim(),
      imageCount: String(formData.get("imageCount") || "").trim(),
      deadline: String(formData.get("deadline") || "").trim(),
      imageLink: String(formData.get("imageLink") || "").trim(),
      budget: String(formData.get("budget") || "").trim(),
      message: String(formData.get("message") || "").trim(),
      createdAt: new Date().toISOString()
    };

    button.disabled = true;
    status.dataset.type = "";
    status.textContent = page.saving;
    trackEvent("retouching_quote_submit", {
      locale: page.locale,
      market: lead.market,
      package_name: lead.packageName
    });

    try {
      const saved = await persistLead(lead);
      writeLocalLead(page.storageKey, { ...lead, id: saved.id, status: saved.status });
      status.dataset.type = "success";
      status.textContent = `${page.saved} Lead #${saved.id}.`;
      trackEvent("retouching_quote_success", {
        locale: page.locale,
        market: lead.market,
        lead_id: saved.id
      });
      form.reset();
    } catch (error) {
      writeLocalLead(page.storageKey, { ...lead, status: "local_fallback", error: error.message });
      status.dataset.type = "error";
      status.textContent = `${page.fallback} ${error.message}`;
      trackEvent("retouching_quote_fallback", {
        locale: page.locale,
        market: lead.market
      });
    } finally {
      button.disabled = false;
      renderLeadSummary();
    }
  });
}

setupNavigation();
setupQuoteForm();
renderLeadSummary();
