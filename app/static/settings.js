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

// ---------- Tab switching ----------

for (const btn of document.querySelectorAll(".tab")) {
  btn.addEventListener("click", () => {
    for (const b of document.querySelectorAll(".tab")) b.classList.remove("active");
    btn.classList.add("active");
    for (const p of document.querySelectorAll(".tab-pane")) p.classList.add("hidden");
    $(`tab-${btn.dataset.tab}`).classList.remove("hidden");
  });
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

// ---------- Konditionen ----------

let kondDefault = null;
let diffVisibleKond = false;

async function loadKonditionen() {
  showLoading("Lade Konditionen…");
  try {
    const res = await fetch("/api/konditionen");
    const data = await res.json();
    $("kond-editor").value = JSON.stringify(data.current, null, 2);
    kondDefault = data.default;
  } finally {
    hideLoading();
  }
}

function setKondError(msg) {
  const el = $("kond-error");
  if (!msg) {
    el.classList.add("hidden");
    return;
  }
  el.textContent = msg;
  el.classList.remove("hidden");
}

$("btn-save-kond").onclick = async () => {
  let parsed;
  try {
    parsed = JSON.parse($("kond-editor").value);
  } catch (e) {
    setKondError(`JSON ungültig: ${e.message}`);
    return;
  }
  setKondError(null);
  showLoading("Speichere Konditionen…");
  try {
    const res = await fetch("/api/konditionen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ konditionen: parsed }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Fehler beim Speichern");
    $("kond-editor").value = JSON.stringify(data.current, null, 2);
    toast("Konditionen gespeichert — wirkt sofort auf die nächste Berechnung.", "success");
  } catch (e) {
    setKondError(`Fehler: ${e.message}`);
  } finally {
    hideLoading();
  }
};

$("btn-reset-kond").onclick = async () => {
  if (!confirm("Konditionen wirklich auf die ausgelieferten Skill-Defaults zurücksetzen? Eigene Änderungen gehen verloren.")) return;
  showLoading("Setze zurück…");
  try {
    const res = await fetch("/api/konditionen/reset", { method: "POST" });
    const data = await res.json();
    $("kond-editor").value = JSON.stringify(data.current, null, 2);
    setKondError(null);
    toast("Konditionen auf Default zurückgesetzt.", "success");
  } catch (e) {
    toast(`Fehler: ${e.message}`, "error");
  } finally {
    hideLoading();
  }
};

$("btn-toggle-diff-kond").onclick = () => {
  diffVisibleKond = !diffVisibleKond;
  const pane = $("kond-diff");
  if (!diffVisibleKond) {
    pane.classList.add("hidden");
    $("btn-toggle-diff-kond").textContent = "Diff anzeigen";
    return;
  }
  let current;
  try {
    current = JSON.parse($("kond-editor").value);
  } catch (e) {
    setKondError(`JSON ungültig: ${e.message}`);
    diffVisibleKond = false;
    return;
  }
  pane.textContent = simpleDiff(
    JSON.stringify(kondDefault, null, 2),
    JSON.stringify(current, null, 2),
  );
  pane.classList.remove("hidden");
  $("btn-toggle-diff-kond").textContent = "Diff verstecken";
};

function simpleDiff(a, b) {
  const A = a.split("\n");
  const B = b.split("\n");
  const out = [];
  const max = Math.max(A.length, B.length);
  for (let i = 0; i < max; i++) {
    if (A[i] === B[i]) continue;
    if (A[i] !== undefined) out.push(`- ${A[i]}`);
    if (B[i] !== undefined) out.push(`+ ${B[i]}`);
  }
  return out.length ? out.join("\n") : "Keine Änderungen.";
}

// ---------- Init ----------

loadGeneral();
loadLogo();
loadKonditionen();
