// Rechner-UI — wird in den nächsten Phasen mit der BEG-EM-/Heizungs-/
// Steuerbonus-Logik gefüllt. Aktuell nur das branding-fähige Grundgerüst.

const $ = (id) => document.getElementById(id);

function toast(msg, kind = "info") {
  const t = $("toast");
  t.textContent = msg;
  t.className = `toast ${kind}`;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 4000);
}
