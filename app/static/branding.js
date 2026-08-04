// Shared branding bootstrap — applies Firmenname, Logo, Akzentfarbe from
// /api/settings to the current page. Loaded on both index.html and
// settings.html before the page-specific script.

async function applyBranding() {
  try {
    const res = await fetch("/api/settings");
    const s = await res.json();

    if (s.akzentfarbe) {
      document.documentElement.style.setProperty("--accent", s.akzentfarbe);
    }

    const titleEl = document.getElementById("brand-title");
    if (titleEl && s.firmenname) {
      titleEl.textContent = s.firmenname;
    }

    const logoEl = document.getElementById("brand-logo");
    if (logoEl) {
      const infoRes = await fetch("/api/settings/logo/info");
      const info = await infoRes.json();
      if (info.has_logo) {
        logoEl.src = "/api/settings/logo?t=" + Date.now();
        logoEl.classList.remove("hidden");
      }
    }
  } catch (e) {
    console.warn("Branding konnte nicht geladen werden:", e);
  }
}

applyBranding();
