// Rechner-UI — BEG-Einzelmaßnahmen (Hülle/Anlagentechnik/Heizungsoptimierung/
// Fachplanung). Heizungsförderung, systemische Sanierung, §35c und iSFP
// folgen als eigene Abschnitte in weiteren Phasen.

const $ = (id) => document.getElementById(id);

function toast(msg, kind = "info") {
  const t = $("toast");
  t.textContent = msg;
  t.className = `toast ${kind}`;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 4000);
}

const KATEGORIEN = [
  { value: "huelle", label: "Gebäudehülle (5.1) — Dämmung, Fenster, Türen, Sonnenschutz" },
  { value: "anlagentechnik", label: "Anlagentechnik (5.2) — Lüftung, MSR, Kälte" },
  { value: "heizungsopt_eff", label: "Heizungsoptimierung — Effizienz (5.4a)" },
  { value: "heizungsopt_em", label: "Heizungsoptimierung — Emissionsminderung (5.4b)" },
  { value: "fachplanung", label: "Fachplanung & Baubegleitung (5.5)" },
];

let massnahmeCounter = 0;

function addMassnahmeRow(prefill = {}) {
  const id = `mn-${massnahmeCounter++}`;
  const wrap = document.createElement("div");
  wrap.className = "massnahme-row";
  wrap.dataset.id = id;
  wrap.innerHTML = `
    <div class="row-3">
      <label>
        <span>Kategorie</span>
        <select class="mn-kategorie">
          ${KATEGORIEN.map(k => `<option value="${k.value}">${k.label}</option>`).join("")}
        </select>
      </label>
      <label>
        <span>Bezeichnung</span>
        <input class="mn-bezeichnung" type="text" placeholder="z. B. Dach dämmen" />
      </label>
      <label>
        <span>Förderfähige Kosten (€)</span>
        <input class="mn-kosten" type="number" min="0" step="0.01" />
      </label>
    </div>
    <div class="row mn-optionen">
      <label class="checkbox-label"><input type="checkbox" class="mn-isfp" /> iSFP vorhanden</label>
      <label class="checkbox-label mn-daemmung-wrap"><input type="checkbox" class="mn-daemmung" /> davon Dämmung (5.1a)</label>
      <label class="checkbox-label mn-daemmung-wrap"><input type="checkbox" class="mn-wpb" /> WPB-Gebäude nachgewiesen</label>
    </div>
    <div class="row mn-optionen">
      <label class="checkbox-label"><input type="checkbox" class="mn-steuerbonus" /> § 35c-Steuerbonus statt BEG-Zuschuss beantragen</label>
      <button class="secondary small danger mn-remove" type="button">Entfernen</button>
    </div>
  `;
  $("massnahmen-liste").appendChild(wrap);

  const kategoriaSelect = wrap.querySelector(".mn-kategorie");
  const daemmungWraps = wrap.querySelectorAll(".mn-daemmung-wrap");
  function updateVisibility() {
    const isHuelle = kategoriaSelect.value === "huelle";
    daemmungWraps.forEach(el => el.classList.toggle("hidden", !isHuelle));
  }
  kategoriaSelect.addEventListener("change", updateVisibility);
  updateVisibility();

  wrap.querySelector(".mn-remove").addEventListener("click", () => wrap.remove());

  if (prefill.kategorie) kategoriaSelect.value = prefill.kategorie;
  if (prefill.bezeichnung) wrap.querySelector(".mn-bezeichnung").value = prefill.bezeichnung;
  if (prefill.kosten) wrap.querySelector(".mn-kosten").value = prefill.kosten;
}

$("btn-add-massnahme").addEventListener("click", () => addMassnahmeRow());

const WAERMEQUELLEN = [
  { value: "sonstige_ee", label: "Sonstige EE-Heizung (Biomasse, Solarthermie, …)" },
  { value: "wp_eu", label: "Wärmepumpe — EU-Ursprung" },
  { value: "wp_nicht_eu", label: "Wärmepumpe — Nicht-EU-Ursprung" },
  { value: "biomasse", label: "Biomasse (ALT: Emissionsminderungszuschlag)" },
];

let heizungCounter = 0;

function addHeizungRow() {
  const id = `hz-${heizungCounter++}`;
  const wrap = document.createElement("div");
  wrap.className = "massnahme-row";
  wrap.dataset.id = id;
  wrap.innerHTML = `
    <div class="row-3">
      <label>
        <span>Bezeichnung</span>
        <input class="hz-bezeichnung" type="text" placeholder="z. B. Wärmepumpe Luft/Wasser" />
      </label>
      <label>
        <span>Förderfähige Kosten (€)</span>
        <input class="hz-kosten" type="number" min="0" step="0.01" />
      </label>
      <label>
        <span>Wärmequelle</span>
        <select class="hz-waermequelle">
          ${WAERMEQUELLEN.map(w => `<option value="${w.value}">${w.label}</option>`).join("")}
        </select>
      </label>
    </div>
    <div class="row mn-optionen">
      <label class="checkbox-label"><input type="checkbox" class="hz-kgb1" /> Ersatz funktionst. Öl/Kohle/Gasetagen/Nachtspeicher</label>
      <label class="checkbox-label"><input type="checkbox" class="hz-kgb2" /> Ersatz Gas-/Biomasseheizung ≥ 20 Jahre</label>
      <button class="secondary small danger hz-remove" type="button">Entfernen</button>
    </div>
    <div class="row mn-optionen">
      <label class="checkbox-label"><input type="checkbox" class="hz-ee-ab-2008" /> Gebäude hat bereits EE-Anlage ab Bj. 2008 (NEU, ab Q1/2027: Ausschluss)</label>
      <label class="checkbox-label"><input type="checkbox" class="hz-ee-vor-2008" /> Ersatz EE-Anlage vor 2008 (NEU, ab Q1/2027: nur 25% förderfähig)</label>
    </div>
    <div class="row mn-optionen">
      <label class="checkbox-label"><input type="checkbox" class="hz-steuerbonus" /> § 35c-Steuerbonus statt BEG-Zuschuss beantragen</label>
    </div>
  `;
  $("heizung-liste").appendChild(wrap);
  wrap.querySelector(".hz-remove").addEventListener("click", () => wrap.remove());
}

$("btn-add-heizung").addEventListener("click", () => addHeizungRow());

function sammleHeizungMassnahmen() {
  const rows = document.querySelectorAll("#heizung-liste .massnahme-row");
  const massnahmen = [];
  for (const row of rows) {
    const kosten = parseFloat(row.querySelector(".hz-kosten").value);
    if (!kosten || kosten <= 0) continue;
    massnahmen.push({
      bezeichnung: row.querySelector(".hz-bezeichnung").value || "",
      kosten,
      waermequelle: row.querySelector(".hz-waermequelle").value,
      ersatz_funktionstuechtige_oel_kohle_gasetagen_nachtspeicher: row.querySelector(".hz-kgb1").checked,
      ersatz_gas_biomasse_ab_20_jahre: row.querySelector(".hz-kgb2").checked,
      ersatz_ee_anlage_baujahr_ab_2008: row.querySelector(".hz-ee-ab-2008").checked,
      ersatz_ee_anlage_vor_2008: row.querySelector(".hz-ee-vor-2008").checked,
      steuerbonus_statt_zuschuss: row.querySelector(".hz-steuerbonus").checked,
    });
  }
  return massnahmen;
}

// Gebäudetyp-abhängige Felder
$("gebaeude-typ").addEventListener("change", () => {
  const isNwg = $("gebaeude-typ").value === "NWG";
  $("feld-anzahl-we").classList.toggle("hidden", isNwg);
  $("feld-nwg-flaeche").classList.toggle("hidden", !isNwg);
});

function heute() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function sammleMassnahmen() {
  const rows = document.querySelectorAll(".massnahme-row");
  const massnahmen = [];
  for (const row of rows) {
    const kosten = parseFloat(row.querySelector(".mn-kosten").value);
    if (!kosten || kosten <= 0) continue;
    massnahmen.push({
      kategorie: row.querySelector(".mn-kategorie").value,
      bezeichnung: row.querySelector(".mn-bezeichnung").value || "",
      kosten,
      isfp_vorhanden: row.querySelector(".mn-isfp").checked,
      ist_daemmung: row.querySelector(".mn-daemmung").checked,
      wpb_gebaeude: row.querySelector(".mn-wpb").checked,
      steuerbonus_statt_zuschuss: row.querySelector(".mn-steuerbonus").checked,
    });
  }
  return massnahmen;
}

function euro(n) {
  return n.toLocaleString("de-DE", { style: "currency", currency: "EUR" });
}

function renderMassnahmenBlock(titel, block) {
  if (!block.massnahmen.length) return "";
  const rows = block.massnahmen.map(m => `
    <div class="ergebnis-massnahme">
      <div class="ergebnis-massnahme-head">
        <strong>${m.bezeichnung || m.kategorie}</strong>
        <span>${euro(m.betrag)}</span>
      </div>
      <div class="muted small">Satz effektiv: ${(m.satz_effektiv * 100).toFixed(1)} % · Kosten: ${euro(m.kosten)}</div>
      <ul class="rechenweg">${m.rechenweg.map(r => `<li>${r}</li>`).join("")}</ul>
    </div>
  `).join("");

  return `
    <div class="ergebnis-block">
      <h3>${titel}</h3>
      ${rows}
      <div class="ergebnis-summe-zeile">
        <span>Förderfähige Kosten gesamt</span><span>${euro(block.foerderfaehige_kosten_summe)}</span>
      </div>
      <div class="ergebnis-summe-zeile muted small">
        <span>Höchstgrenze (${block.hoechstgrenze_erklaerung})</span><span>${euro(block.hoechstgrenze)}</span>
      </div>
      ${block.gedeckelt ? `<div class="badge">Gedeckelt</div>` : ""}
      <div class="ergebnis-summe-zeile total">
        <span>Zuschuss</span><span>${euro(block.zuschuss)}</span>
      </div>
    </div>
  `;
}

$("systemisch-aktiv").addEventListener("change", () => {
  $("systemisch-felder").classList.toggle("hidden", !$("systemisch-aktiv").checked);
});

function renderSteuerbonusBlock(erg) {
  if (!erg) return "";
  return `
    <div class="ergebnis-block">
      <h3>§ 35c-Steuerbonus (statt BEG-Zuschuss)</h3>
      <div class="ergebnis-massnahme">
        <div class="muted small">Kosten der umgeschalteten Maßnahmen: ${euro(erg.kosten_summe)}</div>
        <ul class="rechenweg">${erg.rechenweg.map(r => `<li>${r}</li>`).join("")}</ul>
        <table class="jahresstaffel">
          <thead><tr><th>Jahr</th><th>Satz</th><th>Betrag</th></tr></thead>
          <tbody>
            ${erg.jahresstaffelung.map(j => `<tr><td>${j.jahr}</td><td>${(j.satz * 100).toFixed(0)} %</td><td>${euro(j.betrag)}</td></tr>`).join("")}
          </tbody>
        </table>
      </div>
      ${erg.gedeckelt ? `<div class="badge">Gedeckelt (40.000 €/Objekt)</div>` : ""}
      <div class="ergebnis-summe-zeile total">
        <span>Steuerbonus gesamt (3 Jahre)</span><span>${euro(erg.betrag_gesamt)}</span>
      </div>
    </div>
  `;
}

function renderSystemischBlock(erg) {
  if (!erg) return "";
  return `
    <div class="ergebnis-block">
      <h3>Systemische Sanierung — ${erg.stufe}</h3>
      <div class="ergebnis-massnahme">
        <div class="muted small">Satz: ${(erg.satz_prozentual * 100).toFixed(1)} % · Förderfähige Kosten: ${euro(erg.foerderfaehige_kosten)}</div>
        <ul class="rechenweg">${erg.rechenweg.map(r => `<li>${r}</li>`).join("")}</ul>
      </div>
      <div class="ergebnis-summe-zeile muted small">
        <span>Höchstgrenze (${erg.hoechstgrenze_erklaerung})</span><span>${euro(erg.hoechstgrenze)}</span>
      </div>
      ${erg.gedeckelt ? `<div class="badge">Gedeckelt</div>` : ""}
      <div class="ergebnis-summe-zeile">
        <span>Zuschuss Sanierung</span><span>${euro(erg.betrag)}</span>
      </div>
      <div class="ergebnis-summe-zeile">
        <span>Zuschuss Fachplanung (${euro(erg.fachplanung.foerderfaehige_kosten)} × 50%)</span><span>${euro(erg.fachplanung.betrag)}</span>
      </div>
      <div class="ergebnis-summe-zeile total">
        <span>Zuschuss gesamt (systemisch)</span><span>${euro(erg.zuschuss_gesamt)}</span>
      </div>
    </div>
  `;
}

function renderHeizungBlock(block) {
  if (!block.massnahmen.length) return "";
  const rows = block.massnahmen.map(m => `
    <div class="ergebnis-massnahme">
      <div class="ergebnis-massnahme-head">
        <strong>${m.bezeichnung || "Heizung"}</strong>
        <span>${euro(m.betrag)}</span>
      </div>
      ${m.ausgeschlossen
        ? `<div class="muted small">Nicht förderfähig</div>`
        : `<div class="muted small">Satz: ${(m.satz_prozentual * 100).toFixed(1)} %
             ${m.zuschlag_pauschal ? ` + ${euro(m.zuschlag_pauschal)} Pauschale` : ""}
             · Förderfähige Kosten: ${euro(m.foerderfaehige_kosten)}</div>`}
      <ul class="rechenweg">${m.rechenweg.map(r => `<li>${r}</li>`).join("")}</ul>
    </div>
  `).join("");

  return `
    <div class="ergebnis-block">
      <h3>Heizungsförderung</h3>
      ${rows}
      <div class="ergebnis-summe-zeile">
        <span>Förderfähige Kosten gesamt</span><span>${euro(block.foerderfaehige_kosten_summe)}</span>
      </div>
      <div class="ergebnis-summe-zeile muted small">
        <span>Höchstgrenze (${block.hoechstgrenze_erklaerung})</span><span>${euro(block.hoechstgrenze)}</span>
      </div>
      ${block.gedeckelt ? `<div class="badge">Gedeckelt</div>` : ""}
      <div class="ergebnis-summe-zeile total">
        <span>Zuschuss</span><span>${euro(block.zuschuss)}</span>
      </div>
    </div>
  `;
}

$("beta-aktiv").addEventListener("change", () => {
  $("beta-felder").classList.toggle("hidden", !$("beta-aktiv").checked);
});

$("btn-beta-berechnen").addEventListener("click", async () => {
  const btn = $("btn-beta-berechnen");
  btn.disabled = true;
  btn.textContent = "Prüfe…";
  try {
    const res = await fetch("/api/beta/nebenprogramme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        anzahl_kinder: parseInt($("beta-kinder").value, 10) || 0,
        zve_haushalt: parseFloat($("beta-zve").value) || null,
        anzahl_we: parseInt($("anzahl-we").value, 10) || 1,
        isfp_kosten: parseFloat($("beta-isfp-kosten").value) || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data));

    const html = data.programme.map(p => `
      <div class="ergebnis-massnahme">
        <div class="ergebnis-massnahme-head">
          <strong>${p.programm}</strong>
          <span class="badge">Beta — ungeprüft</span>
        </div>
        <div class="muted small">${p.hinweis}</div>
        ${p.kredit_max ? `<div class="small">Kredit max.: ${euro(p.kredit_max)}</div>` : ""}
        ${p.einkommensgrenze ? `<div class="small">Einkommensgrenze: ${euro(p.einkommensgrenze)}${p.vermutlich_berechtigt === false ? " — vermutlich nicht erfüllt" : ""}</div>` : ""}
        ${p.betrag !== undefined ? `<div class="small">Zuschuss: ${euro(p.betrag)} (${(p.satz * 100).toFixed(0)}%, max. ${euro(p.hoechstbetrag)})</div>` : ""}
        <div class="hint" style="margin-top:8px;">${p.pruefhinweis}</div>
      </div>
    `).join("");
    $("beta-ergebnis").innerHTML = html;
  } catch (e) {
    toast(`Fehler: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Beta-Programme prüfen";
  }
});

let lastPayload = null;

async function exportPdf() {
  if (!lastPayload) return;
  const btn = $("btn-pdf-export");
  btn.disabled = true;
  btn.textContent = "PDF wird erstellt…";
  try {
    const res = await fetch("/api/pdf/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastPayload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "PDF-Export fehlgeschlagen");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  } catch (e) {
    toast(`Fehler: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "PDF exportieren";
  }
}

$("btn-berechnen").addEventListener("click", async () => {
  const zveVal = parseFloat($("zve").value);
  const payload = {
    regime: $("regime").value,
    antragsdatum: $("antragsdatum").value || heute(),
    gebaeude: {
      typ: $("gebaeude-typ").value,
      anzahl_we: parseInt($("anzahl-we").value, 10) || 1,
      nwg_flaeche_m2: parseFloat($("nwg-flaeche").value) || null,
    },
    antragsteller: {
      selbstnutzer: $("selbstnutzer").checked,
      zve: Number.isFinite(zveVal) ? zveVal : null,
      kind_minderjaehrig: $("kind-minderjaehrig").checked,
    },
    em_massnahmen: sammleMassnahmen(),
    heizung_massnahmen: sammleHeizungMassnahmen(),
    systemische_sanierung: null,
  };

  if ($("systemisch-aktiv").checked) {
    const sysKosten = parseFloat($("sys-kosten").value);
    if (sysKosten > 0) {
      payload.systemische_sanierung = {
        stufe: $("sys-stufe").value,
        kosten: sysKosten,
        kommunal: $("sys-kommunal").checked,
        wpb_bonus: $("sys-wpb").checked,
        sersan_bonus: $("sys-sersan").checked,
        nh_bonus: $("sys-nh").checked,
        fachplanung_kosten: parseFloat($("sys-fachplanung").value) || 0,
      };
    }
  }

  if (!payload.em_massnahmen.length && !payload.heizung_massnahmen.length && !payload.systemische_sanierung) {
    toast("Bitte mindestens eine Maßnahme mit Kosten eingeben.", "error");
    return;
  }

  lastPayload = payload;
  const btn = $("btn-berechnen");
  btn.disabled = true;
  btn.textContent = "Berechne…";
  try {
    const res = await fetch("/api/calc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data));

    const html = `
      <section class="card">
        <div class="row-header">
          <h2>Ergebnis</h2>
          <span class="badge regime-badge">Regime: ${data.regime}</span>
        </div>
        ${(data.warnungen || []).map(w => `<div class="hint">${w}</div>`).join("")}
        ${renderMassnahmenBlock("BEG-Einzelmaßnahmen", data.beg_em)}
        ${renderMassnahmenBlock("Fachplanung & Baubegleitung", data.fachplanung)}
        ${renderHeizungBlock(data.beg_heizung)}
        ${renderSteuerbonusBlock(data.steuerbonus_35c)}
        ${renderSystemischBlock(data.beg_systemisch)}
        <div class="ergebnis-summe-zeile total">
          <span>Zuschuss gesamt (BEG)</span><span>${euro(data.zuschuss_gesamt)}</span>
        </div>
        ${data.steuerbonus_35c ? `
          <div class="ergebnis-summe-zeile total gesamt">
            <span>Gesamtvorteil inkl. Steuerbonus</span><span>${euro(data.gesamtvorteil_inkl_steuerbonus)}</span>
          </div>
        ` : ""}
        <div class="row" style="margin-top:16px;">
          <button id="btn-pdf-export" class="secondary" type="button">PDF exportieren</button>
        </div>
      </section>
    `;
    $("ergebnis").innerHTML = html;
    $("ergebnis").scrollIntoView({ behavior: "smooth", block: "start" });
    $("btn-pdf-export").addEventListener("click", exportPdf);
  } catch (e) {
    toast(`Fehler: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Förderung berechnen";
  }
});

// Init: Antragsdatum auf heute, eine leere Maßnahmenzeile
$("antragsdatum").value = heute();
addMassnahmeRow();
