import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from utils import run_dir


def pdf_exporter(state: dict) -> dict:
    run_id = state["run_id"]
    memo   = state.get("memo", "")

    pdf_path = os.path.join(run_dir(run_id), "memo.pdf")
    _render_pdf(memo, pdf_path)

    status = f"✓ PDF exported → {os.path.basename(pdf_path)}"
    return {"pdf_path": pdf_path, "status_log": [status]}


# --------------------------------------------------------------------------- #
# Markdown → ReportLab renderer
# --------------------------------------------------------------------------- #

BRAND_BLUE  = colors.HexColor("#1a3c5e")
BRAND_LIGHT = colors.HexColor("#e8f0f7")
ACCENT_RED  = colors.HexColor("#c0392b")


def _make_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "MemoH1", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=14,
        textColor=BRAND_BLUE, spaceBefore=14, spaceAfter=4,
        borderPad=4,
    ))
    styles.add(ParagraphStyle(
        "MemoH2", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=11,
        textColor=BRAND_BLUE, spaceBefore=10, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        "MemoH3", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9.5,
        textColor=colors.HexColor("#2c5f8a"), spaceBefore=6, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "MemoBody", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9,
        leading=13, spaceBefore=3, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        "MemoBullet", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9,
        leading=13, leftIndent=16, spaceBefore=1, spaceAfter=1,
        bulletIndent=6,
    ))
    styles.add(ParagraphStyle(
        "MemoFooter", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=7,
        textColor=colors.gray, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "MemoCoverTitle", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=20,
        textColor=colors.white, alignment=TA_CENTER, leading=24,
    ))
    styles.add(ParagraphStyle(
        "MemoCoverSub", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#c8d8ea"), alignment=TA_CENTER,
    ))
    return styles


def _inline(text: str) -> str:
    """Convert inline markdown (**bold**, *italic*, `code`) to ReportLab XML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`",       r"<font name='Courier'>\1</font>", text)
    # Severity badges [HIGH] [MEDIUM] [LOW]
    text = re.sub(r"\[HIGH\]",   "<b><font color='#c0392b'>[HIGH]</font></b>",   text)
    text = re.sub(r"\[MEDIUM\]", "<b><font color='#d68910'>[MEDIUM]</font></b>", text)
    text = re.sub(r"\[LOW\]",    "<b><font color='#1a8e2a'>[LOW]</font></b>",    text)
    # Citations [Source: ...]
    text = re.sub(
        r"\[Source:([^\]]+)\]",
        r"<font color='#666666' size='7'>[Source:\1]</font>",
        text,
    )
    return text


def _parse_md_table(lines: list) -> list | None:
    """Parse a markdown table block into list-of-lists."""
    rows = []
    for line in lines:
        line = line.strip()
        if re.match(r"^\|[-| :]+\|$", line):
            continue  # separator row
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line[1:-1].split("|")]
            rows.append(cells)
    return rows if len(rows) >= 2 else None


def _render_pdf(markdown_text: str, output_path: str):
    styles = _make_styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.9*inch, rightMargin=0.9*inch,
        topMargin=0.75*inch, bottomMargin=0.85*inch,
        title="Quality of Earnings Memorandum",
    )

    elems = []

    # ── Cover band ──────────────────────────────────────────────────────────
    cover_data = [["Quality of Earnings Memorandum"]]
    cover_tbl  = Table(cover_data, colWidths=[6.7*inch])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 16),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    elems.append(cover_tbl)
    elems.append(Spacer(1, 0.08*inch))
    elems.append(Paragraph(
        "CONFIDENTIAL — Prepared for Due Diligence Purposes Only",
        styles["MemoFooter"],
    ))
    elems.append(Spacer(1, 0.12*inch))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_BLUE))
    elems.append(Spacer(1, 0.08*inch))

    # ── Body parsing ────────────────────────────────────────────────────────
    lines = markdown_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # Table block
        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = _parse_md_table(table_lines)
            if rows:
                elems.append(_build_rl_table(rows))
            elems.append(Spacer(1, 0.06*inch))
            continue

        stripped = line.strip()

        if stripped.startswith("### "):
            elems.append(Paragraph(_inline(stripped[4:]), styles["MemoH3"]))
        elif stripped.startswith("## "):
            elems.append(Spacer(1, 0.06*inch))
            elems.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#c8d8ea")))
            elems.append(Paragraph(_inline(stripped[3:]), styles["MemoH2"]))
        elif stripped.startswith("# "):
            elems.append(Paragraph(_inline(stripped[2:]), styles["MemoH1"]))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = _inline(stripped[2:])
            elems.append(Paragraph(f"• {bullet_text}", styles["MemoBullet"]))
        elif re.match(r"^\d+\. ", stripped):
            num_text = _inline(re.sub(r"^\d+\. ", "", stripped))
            num = re.match(r"^(\d+)\.", stripped).group(1)
            elems.append(Paragraph(f"{num}. {num_text}", styles["MemoBullet"]))
        elif stripped == "" or stripped == "---":
            elems.append(Spacer(1, 0.06*inch))
        else:
            elems.append(Paragraph(_inline(stripped), styles["MemoBody"]))

        i += 1

    # ── Footer ──────────────────────────────────────────────────────────────
    elems.append(Spacer(1, 0.2*inch))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_BLUE))
    elems.append(Spacer(1, 0.04*inch))
    elems.append(Paragraph(
        "This memorandum is confidential and prepared solely for the use of the named recipient. "
        "Generated by Earnest &mdash; a Verity product.",
        styles["MemoFooter"],
    ))

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.gray)
        canvas.drawString(0.9*inch, 0.5*inch, "CONFIDENTIAL — Earnest by Verity")
        canvas.drawRightString(
            letter[0] - 0.9*inch, 0.5*inch,
            f"Page {doc.page}"
        )
        canvas.restoreState()

    doc.build(elems, onFirstPage=_footer, onLaterPages=_footer)


def _build_rl_table(rows: list) -> Table:
    n_cols  = max(len(r) for r in rows)
    col_w   = [6.7 * inch / n_cols] * n_cols
    # Auto-size first column wider if multi-column
    if n_cols >= 3:
        col_w = [2.5*inch] + [(6.7*inch - 2.5*inch) / (n_cols - 1)] * (n_cols - 1)

    styled_rows = []
    for r_idx, row in enumerate(rows):
        padded = (row + [""] * n_cols)[:n_cols]
        if r_idx == 0:
            styled_rows.append([Paragraph(f"<b>{_inline(c)}</b>",
                                          ParagraphStyle("TH", fontName="Helvetica-Bold",
                                                         fontSize=8.5, leading=11,
                                                         textColor=colors.white))
                                 for c in padded])
        else:
            styled_rows.append([Paragraph(_inline(c),
                                          ParagraphStyle("TD", fontName="Helvetica",
                                                         fontSize=8.5, leading=11))
                                 for c in padded])

    t = Table(styled_rows, colWidths=col_w)
    light = colors.HexColor("#e8f0f7")
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  BRAND_BLUE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, light]),
        ("BOX",           (0, 0), (-1, -1), 0.5, BRAND_BLUE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d8ea")),
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
    ]))
    return t
