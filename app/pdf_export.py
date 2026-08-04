"""PDF-Export der Förderberechnung mit Branding (Logo/Firmenname/Kontakt aus
den Settings). Reportlab-Platypus statt WeasyPrint — siehe README/Plan für
die Begründung (keine zusätzlichen Systemdependencies)."""

from __future__ import annotations

import io
from datetime import date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT_DEFAULT = "#0B6E7F"


def _euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _massnahmen_tabelle(titel: str, massnahmen: list[dict], styles, accent) -> list:
    if not massnahmen:
        return []
    elemente = [Paragraph(titel, styles["H2"])]
    rows = [["Maßnahme", "Kosten", "Satz", "Betrag"]]
    for m in massnahmen:
        satz = m.get("satz_effektiv", m.get("satz_prozentual", 0))
        rows.append([
            m.get("bezeichnung") or m.get("kategorie", ""),
            _euro(m.get("kosten", 0)),
            f"{satz * 100:.1f} %",
            _euro(m.get("betrag", 0)),
        ])
    tbl = Table(rows, colWidths=[70 * mm, 35 * mm, 25 * mm, 35 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(accent)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e3e6ec")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbfc")]),
    ]))
    elemente.append(tbl)
    elemente.append(Spacer(1, 8))
    return elemente


def generate_pdf(
    calc_result: dict[str, Any], settings: dict[str, Any], logo_bytes: bytes | None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )

    accent = settings.get("akzentfarbe") or ACCENT_DEFAULT
    base_styles = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "TitleCustom", parent=base_styles["Title"], textColor=colors.HexColor("#0E2A40"),
            fontSize=20, spaceAfter=4,
        ),
        "Sub": ParagraphStyle(
            "SubCustom", parent=base_styles["Normal"], textColor=colors.HexColor("#6b7382"),
            fontSize=10, spaceAfter=14,
        ),
        "H2": ParagraphStyle(
            "H2Custom", parent=base_styles["Heading2"], textColor=colors.HexColor(accent),
            fontSize=13, spaceBefore=10, spaceAfter=6,
        ),
        "Normal": base_styles["Normal"],
        "Footer": ParagraphStyle(
            "FooterCustom", parent=base_styles["Normal"], textColor=colors.HexColor("#6b7382"),
            fontSize=8,
        ),
    }

    story: list = []

    firmenname = settings.get("firmenname") or ""
    if logo_bytes:
        try:
            img = Image(io.BytesIO(logo_bytes))
            img.drawHeight = 16 * mm
            img.drawWidth = img.drawHeight * (img.imageWidth / img.imageHeight)
            story.append(img)
            story.append(Spacer(1, 6))
        except Exception:
            pass
    if firmenname:
        story.append(Paragraph(firmenname, styles["Sub"]))

    story.append(Paragraph("Förderberechnung", styles["Title"]))
    story.append(Paragraph(
        f"Erstellt am {date.today().strftime('%d.%m.%Y')} · Regime: {calc_result.get('regime')}",
        styles["Sub"],
    ))

    for warnung in calc_result.get("warnungen", []):
        story.append(Paragraph(f"⚠ {warnung}", styles["Sub"]))

    beg_em = calc_result.get("beg_em", {})
    story += _massnahmen_tabelle("BEG-Einzelmaßnahmen", beg_em.get("massnahmen", []), styles, accent)

    fachplanung = calc_result.get("fachplanung", {})
    story += _massnahmen_tabelle(
        "Fachplanung & Baubegleitung", fachplanung.get("massnahmen", []), styles, accent
    )

    heizung = calc_result.get("beg_heizung", {})
    heizung_massnahmen = [
        {**m, "satz_effektiv": m.get("satz_prozentual", 0)} for m in heizung.get("massnahmen", [])
    ]
    story += _massnahmen_tabelle("Heizungsförderung", heizung_massnahmen, styles, accent)

    steuerbonus = calc_result.get("steuerbonus_35c")
    if steuerbonus:
        story.append(Paragraph("§ 35c-Steuerbonus (statt BEG-Zuschuss)", styles["H2"]))
        story.append(Paragraph(
            f"Kosten: {_euro(steuerbonus['kosten_summe'])} · Steuerbonus gesamt "
            f"(3 Jahre): {_euro(steuerbonus['betrag_gesamt'])}",
            styles["Normal"],
        ))
        story.append(Spacer(1, 8))

    systemisch = calc_result.get("beg_systemisch")
    if systemisch:
        story.append(Paragraph(
            f"Systemische Sanierung — {systemisch['stufe']}", styles["H2"]
        ))
        story.append(Paragraph(
            f"Förderfähige Kosten: {_euro(systemisch['foerderfaehige_kosten'])} · "
            f"Satz: {systemisch['satz_prozentual'] * 100:.1f} % · "
            f"Zuschuss gesamt: {_euro(systemisch['zuschuss_gesamt'])}",
            styles["Normal"],
        ))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 10))
    gesamt_rows = [["Zuschuss gesamt (BEG)", _euro(calc_result.get("zuschuss_gesamt", 0))]]
    if steuerbonus:
        gesamt_rows.append([
            "Gesamtvorteil inkl. Steuerbonus",
            _euro(calc_result.get("gesamtvorteil_inkl_steuerbonus", 0)),
        ])
    gesamt_tbl = Table(gesamt_rows, colWidths=[120 * mm, 45 * mm])
    gesamt_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor(accent)),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(gesamt_tbl)

    kontakt_teile = [
        settings.get("kontakt_adresse"), settings.get("kontakt_telefon"),
        settings.get("kontakt_email"),
    ]
    kontakt = " · ".join(t for t in kontakt_teile if t)
    if kontakt:
        story.append(Spacer(1, 20))
        story.append(Paragraph(kontakt, styles["Footer"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Unverbindliche Beispielrechnung, vorbehaltlich Bescheid. Ersetzt keine "
        "Förderberatung im Einzelfall.",
        styles["Footer"],
    ))

    doc.build(story)
    return buf.getvalue()
