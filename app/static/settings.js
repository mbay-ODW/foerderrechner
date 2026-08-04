// Settings page — Branding (Firma/Kontakt/Akzentfarbe/Logo), talks to /api/settings

const $ = (id) => document.getElementById(id);

function showLoading(text) {
  $("loading-text").textContent = text || "Lade…";
  $("loading").classList.remove("hidden");
}
function hideLoading() { $("loading").classList.add("hidden"); }

function toast(msg, kind = "info") {
  const t = $("toast");
  t.textContent = msg;
  t.className = `toast ${kind}`;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 4000);
}

// ---------- General ----------

async function loadGeneral() {
  showLoading("Lade Einstellungen…");
  try {
    const res = await fetch("/api/settings");
    const s = await res.json();
    $("firmenname").value = s.firmenname || "";
    $("kontakt-adresse").value = s.kontakt_adresse || "";
    $("kontakt-telefon").value = s.kontakt_telefon || "";
    $("kontakt-email").value = s.kontakt_email || "";
    $("akzentfarbe").value = s.akzentfarbe || "#0B6E7F";
    document.documentElement.style.setProperty("--accent", s.akzentfarbe || "#0B6E7F");
  } finally {
    hideLoading();
  }
}

$("btn-save-general").onclick = async () => {
  showLoading("Speichere…");
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        firmenname: $("firmenname").value,
        kontakt_adresse: $("kontakt-adresse").value,
        kontakt_telefon: $("kontakt-telefon").value,
        kontakt_email: $("kontakt-email").value,
        akzentfarbe: $("akzentfarbe").value,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    document.documentElement.style.setProperty("--accent", $("akzentfarbe").value);
    toast("Einstellungen gespeichert.", "success");
  } catch (e) {
    toast(`Fehler: ${e.message}`, "error");
  } finally {
    hideLoading();
  }
};

// ---------- Logo ----------

async function loadLogo() {
  const res = await fetch("/api/settings/logo/info");
  const info = await res.json();
  if (info.has_logo) {
    $("logo-preview").src = "/api/settings/logo?t=" + Date.now();
    $("logo-preview-wrap").classList.remove("hidden");
    $("logo-upload-zone").classList.add("hidden");
  } else {
    $("logo-preview-wrap").classList.add("hidden");
    $("logo-upload-zone").classList.remove("hidden");
  }
}

function setLogoStatus(msg, kind = "info") {
  const el = $("logo-status");
  el.textContent = msg;
  el.className = kind;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4000);
}

async function uploadLogo(file) {
  const fd = new FormData();
  fd.append("file", file);
  showLoading("Logo hochladen…");
  try {
    const res = await fetch("/api/settings/logo", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Fehler beim Hochladen");
    }
    toast("Logo gespeichert.", "success");
    await loadLogo();
  } catch (e) {
    setLogoStatus(`✗ ${e.message}`, "error");
  } finally {
    hideLoading();
  }
}

$("logo-file").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) uploadLogo(file);
  e.target.value = "";
});

const logoZone = $("logo-upload-zone");
logoZone.addEventListener("click", (e) => {
  if (e.target === $("logo-file")) return;
  $("logo-file").click();
});
logoZone.addEventListener("dragover", (e) => { e.preventDefault(); logoZone.classList.add("drag-over"); });
logoZone.addEventListener("dragleave", () => logoZone.classList.remove("drag-over"));
logoZone.addEventListener("drop", (e) => {
  e.preventDefault();
  logoZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) uploadLogo(file);
});

$("btn-delete-logo").addEventListener("click", async () => {
  if (!confirm("Logo wirklich entfernen?")) return;
  showLoading("Entferne Logo…");
  try {
    const res = await fetch("/api/settings/logo", { method: "DELETE" });
    if (!res.ok) throw new Error("Fehler beim Löschen");
    toast("Logo entfernt.", "success");
    await loadLogo();
  } catch (e) {
    toast(`Fehler: ${e.message}`, "error");
  } finally {
    hideLoading();
  }
});

// ---------- Init ----------

loadGeneral();
loadLogo();
