"""
Generates synthetic demo data for Acme HVAC Services, LLC.
Produces three PDFs in demo_data/acme_hvac/:
  - acme_hvac_pl_2021_2023.pdf   (3-year income statement)
  - acme_hvac_bank_2023.pdf      (12-month bank statement)
  - acme_hvac_customers_2023.pdf (47-customer revenue table)
"""

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "demo_data", "acme_hvac"
)

# --------------------------------------------------------------------------- #
# Shared styles
# --------------------------------------------------------------------------- #

def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CompanyName",
        fontSize=14, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="DocTitle",
        fontSize=11, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="SubTitle",
        fontSize=9, fontName="Helvetica",
        alignment=TA_CENTER, spaceAfter=8, textColor=colors.gray
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        fontSize=7, fontName="Helvetica",
        alignment=TA_CENTER, textColor=colors.gray
    ))
    return styles


def _fmt(n: int | float, prefix="$") -> str:
    if n < 0:
        return f"({prefix}{abs(n):,.0f})"
    return f"{prefix}{n:,.0f}"


def _pct(n: float) -> str:
    return f"{n:.1f}%"


# --------------------------------------------------------------------------- #
# P&L PDF
# --------------------------------------------------------------------------- #

PL_DATA = {
    "periods": ["FY2021", "FY2022", "FY2023"],
    "revenue": [3_100_000, 3_800_000, 4_200_000],
    "cogs":    [1_786_000, 2_192_000, 2_422_000],
    "opex": {
        "Owner Compensation":        [180_000, 195_000, 210_000],
        "Consulting - J. Hayes":     [ 48_000,  48_000,  48_000],
        "Wages & Salaries":          [235_000, 280_000, 315_000],
        "Payroll Taxes & Benefits":  [ 47_000,  56_000,  64_000],
        "Vehicle Expense":           [ 58_000,  72_000,  87_000],
        "Insurance":                 [ 35_000,  40_000,  45_000],
        "Rent & Occupancy":          [ 62_000,  65_000,  68_000],
        "Utilities":                 [ 24_000,  28_000,  31_000],
        "Marketing & Advertising":   [ 18_000,  22_000,  25_000],
        "Legal & Professional":      [ 28_000,  12_000,   8_000],
        "Depreciation & Amortization": [22_000, 25_000,  28_000],
        "Miscellaneous":             [ 19_000,  22_000,  27_000],
    },
}


def generate_pl_pdf():
    filepath = os.path.join(OUTPUT_DIR, "acme_hvac_pl_2021_2023.pdf")
    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        leftMargin=0.9*inch, rightMargin=0.9*inch,
        topMargin=0.8*inch, bottomMargin=0.8*inch
    )
    styles = _base_styles()
    elems = []

    # Header
    elems.append(Paragraph("ACME HVAC SERVICES, LLC", styles["CompanyName"]))
    elems.append(Paragraph("Income Statement", styles["DocTitle"]))
    elems.append(Paragraph(
        "For the Years Ended December 31, 2021, 2022, and 2023",
        styles["SubTitle"]
    ))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3c5e")))
    elems.append(Spacer(1, 0.15*inch))

    d = PL_DATA
    yrs = d["periods"]
    rev = d["revenue"]
    cogs = d["cogs"]
    gp = [rev[i] - cogs[i] for i in range(3)]
    gm_pct = [gp[i] / rev[i] * 100 for i in range(3)]

    total_opex = [
        sum(d["opex"][k][i] for k in d["opex"])
        for i in range(3)
    ]
    da = d["opex"]["Depreciation & Amortization"]
    opex_ex_da = [total_opex[i] - da[i] for i in range(3)]
    operating_income = [gp[i] - total_opex[i] for i in range(3)]
    ebitda = [operating_income[i] + da[i] for i in range(3)]
    ebitda_margin = [ebitda[i] / rev[i] * 100 for i in range(3)]

    HEADER = colors.HexColor("#1a3c5e")
    LIGHT   = colors.HexColor("#e8f0f7")
    SUBTOTAL = colors.HexColor("#c8d8ea")

    col_w = [3.2*inch, 1.15*inch, 1.15*inch, 1.15*inch]

    def row(label, values, bold=False, indent=False, pct_row=False, blank=False):
        if blank:
            return ["", "", "", ""]
        prefix = "    " if indent else ""
        if pct_row:
            return [prefix + label] + [_pct(v) for v in values]
        return [prefix + label] + [_fmt(v) for v in values]

    rows = [
        ["", yrs[0], yrs[1], yrs[2]],
        ["REVENUE", "", "", ""],
        row("  Service Revenue", rev, indent=True),
        row("Total Revenue", rev, bold=True),
        row("", [], blank=True),
        ["COST OF SERVICES", "", "", ""],
        row("  Direct Labor & Materials", cogs, indent=True),
        row("Total Cost of Services", cogs, bold=True),
        row("", [], blank=True),
        row("GROSS PROFIT", gp, bold=True),
        row("  Gross Margin %", gm_pct, indent=True, pct_row=True),
        row("", [], blank=True),
        ["OPERATING EXPENSES", "", "", ""],
    ]
    for label, vals in d["opex"].items():
        rows.append(row("  " + label, vals, indent=True))
    rows += [
        row("Total Operating Expenses", total_opex, bold=True),
        row("", [], blank=True),
        row("OPERATING INCOME", operating_income, bold=True),
        row("", [], blank=True),
        ["EBITDA RECONCILIATION", "", "", ""],
        row("  Operating Income", operating_income, indent=True),
        row("  Add: Depreciation & Amortization", da, indent=True),
        row("EBITDA", ebitda, bold=True),
        row("  EBITDA Margin %", ebitda_margin, indent=True, pct_row=True),
    ]

    t = Table(rows, colWidths=col_w)

    bold_rows = {0, 3, 8, 9, len(rows)-5, len(rows)-3, len(rows)-2}
    section_rows = {1, 5, 12, len(rows)-6}

    style_cmds = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, HEADER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (0, -1), 6),
    ]
    for r in bold_rows:
        if r < len(rows):
            style_cmds.append(("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"))
            style_cmds.append(("BACKGROUND", (0, r), (-1, r), SUBTOTAL))
    for r in section_rows:
        if r < len(rows):
            style_cmds.append(("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"))
            style_cmds.append(("BACKGROUND", (0, r), (-1, r), HEADER))
            style_cmds.append(("TEXTCOLOR", (0, r), (-1, r), colors.white))

    # EBITDA bottom highlight
    style_cmds.append(("BACKGROUND", (0, len(rows)-2), (-1, len(rows)-2), colors.HexColor("#1a3c5e")))
    style_cmds.append(("TEXTCOLOR", (0, len(rows)-2), (-1, len(rows)-2), colors.white))
    style_cmds.append(("FONTNAME", (0, len(rows)-2), (-1, len(rows)-2), "Helvetica-Bold"))

    t.setStyle(TableStyle(style_cmds))
    elems.append(t)

    elems.append(Spacer(1, 0.15*inch))
    elems.append(Paragraph(
        "Prepared by management. For due diligence purposes only. Unaudited.",
        styles["Footer"]
    ))

    doc.build(elems)
    print(f"  ✓ P&L PDF → {filepath}")
    return filepath


# --------------------------------------------------------------------------- #
# Bank Statement PDF
# --------------------------------------------------------------------------- #

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Monthly net deposits (revenue - COGS payments) — seasonality: Q3 peak for HVAC
MONTHLY_REVENUE = [
    240_000, 230_000, 290_000, 320_000, 380_000, 420_000,
    480_000, 460_000, 400_000, 350_000, 310_000, 320_000,
]  # total = $4,200,000

MONTHLY_COGS = [
    138_000, 133_000, 167_000, 184_000, 219_000, 242_000,
    277_000, 265_000, 231_000, 202_000, 179_000, 185_000,
]  # ~57.7% of revenue

# Fixed monthly operating disbursements (base, before specifics below)
MONTHLY_FIXED = [
    ("ACH - ADP PAYROLL", 52_000),
    ("ACH - COMMERCIAL INSURANCE PREM", 3_750),
    ("ACH - RENT - HARBOR INDUSTRIAL", 5_667),
    ("CHECK - UTILITIES / PHONE", 2_583),
    ("ACH - VEHICLE FLEET EXPENSE", 4_000),
]

# Special items by month (1-indexed)
SPECIAL_ITEMS = {
    1:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit")],
    2:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit")],
    3:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit"),
         ("CHECK - LEGAL FEES - GRAHAM & ASSOC",    2_500, "debit")],
    4:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit")],
    5:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit"),
         ("ACH - MARKETING / GOOGLE ADS",           2_100, "debit")],
    6:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit")],
    7:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit"),
         ("ACH - EQUIPMENT RENTAL - UNITED",        3_200, "debit")],
    8:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit")],
    9:  [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit")],
    10: [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit"),
         ("CHECK - VEHICLE PURCHASE FORD F-150",   22_000, "debit")],
    11: [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit")],
    12: [("WIRE - J HAYES CONSULTING LLC",          4_000, "debit"),
         ("ACH - YEAR-END BONUS - EMPLOYEES",       8_500, "debit")],
}


def generate_bank_pdf():
    filepath = os.path.join(OUTPUT_DIR, "acme_hvac_bank_2023.pdf")
    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.8*inch, bottomMargin=0.8*inch
    )
    styles = _base_styles()
    elems = []

    elems.append(Paragraph("ACME HVAC SERVICES, LLC", styles["CompanyName"]))
    elems.append(Paragraph("Business Checking Account — Statement Summary", styles["DocTitle"]))
    elems.append(Paragraph(
        "Account No. ****4821  |  January 1, 2023 – December 31, 2023  |  First National Bank",
        styles["SubTitle"]
    ))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3c5e")))
    elems.append(Spacer(1, 0.12*inch))

    HEADER = colors.HexColor("#1a3c5e")
    LIGHT   = colors.HexColor("#e8f0f7")

    # Opening balance
    opening_balance = 125_432

    # Build transaction rows per month
    all_rows = [[
        "Month", "Date", "Description", "Debits", "Credits", "Balance"
    ]]
    balance = opening_balance
    all_rows.append(["Jan 1", "01/01", "OPENING BALANCE", "", "", _fmt(balance)])

    annual_totals_deb = 0
    annual_totals_cred = 0

    for month_idx, month_name in enumerate(MONTHS):
        m = month_idx + 1
        rev = MONTHLY_REVENUE[month_idx]
        cogs_pay = MONTHLY_COGS[month_idx]
        short = month_name[:3].upper()

        # Revenue deposit (15th)
        dep_date = f"{m:02d}/15"
        balance += rev
        annual_totals_cred += rev
        all_rows.append([short, dep_date, "CUSTOMER PAYMENTS - BATCH DEPOSIT", "", _fmt(rev), _fmt(balance)])

        # COGS / supply payments (10th)
        pay_date = f"{m:02d}/10"
        balance -= cogs_pay
        annual_totals_deb += cogs_pay
        all_rows.append([short, pay_date, "ACH - SUPPLIER PAYMENTS / MATERIALS", _fmt(cogs_pay), "", _fmt(balance)])

        # Fixed monthly expenses
        for desc, amt in MONTHLY_FIXED:
            day = 5 if "PAYROLL" in desc else 1
            date_str = f"{m:02d}/{day:02d}"
            balance -= amt
            annual_totals_deb += amt
            all_rows.append([short, date_str, desc, _fmt(amt), "", _fmt(balance)])

        # Special items
        for desc, amt, direction in SPECIAL_ITEMS.get(m, []):
            date_str = f"{m:02d}/20"
            if direction == "debit":
                balance -= amt
                annual_totals_deb += amt
                all_rows.append([short, date_str, desc, _fmt(amt), "", _fmt(balance)])
            else:
                balance += amt
                annual_totals_cred += amt
                all_rows.append([short, date_str, desc, "", _fmt(amt), _fmt(balance)])

    # Year-end summary row
    all_rows.append(["", "", "ANNUAL TOTALS",
                     _fmt(annual_totals_deb),
                     _fmt(annual_totals_cred),
                     _fmt(balance)])

    col_w = [0.5*inch, 0.55*inch, 3.0*inch, 1.0*inch, 1.0*inch, 0.95*inch]
    t = Table(all_rows, colWidths=col_w, repeatRows=1)

    style_cmds = [
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTSIZE",   (0, 0), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT]),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        # Highlight J. Hayes and vehicle purchase rows
        ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#c8d8ea")),
    ]

    # Highlight notable debit rows
    highlight_keywords = ["J HAYES", "FORD F-150"]
    for r_idx, row in enumerate(all_rows):
        if any(kw in str(row[2]) for kw in highlight_keywords):
            style_cmds.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#fff3cd")))
            style_cmds.append(("FONTNAME",   (0, r_idx), (-1, r_idx), "Helvetica-Bold"))

    t.setStyle(TableStyle(style_cmds))
    elems.append(t)

    elems.append(Spacer(1, 0.12*inch))
    elems.append(Paragraph(
        "Confidential bank records provided for due diligence. "
        "Highlighted rows flagged for QoE review.",
        styles["Footer"]
    ))

    doc.build(elems)
    print(f"  ✓ Bank PDF → {filepath}")
    return filepath


# --------------------------------------------------------------------------- #
# Customer List PDF
# --------------------------------------------------------------------------- #

TOTAL_REVENUE = 4_200_000

CUSTOMERS = [
    ("Lakewood Commercial Properties LLC", 1_302_000),
    ("Riverside Medical Center",             504_000),
    ("Horizon Unified School District",      420_000),
    ("Greenwood Shopping Center",            336_000),
    ("Valley Office Park LLC",               294_000),
    # Customers 6-15 (total: $626,000)
    ("Sunridge Apartments",                   90_000),
    ("Metro Transit Authority",               82_000),
    ("Pine Crest Senior Living",              74_000),
    ("Bayside Hotel & Suites",                68_000),
    ("First Community Bank — HQ",             62_000),
    ("Harbor View Condominiums",              58_000),
    ("Northgate Mall Management",             54_000),
    ("Clearwater Data Center",                50_000),
    ("Westfield Church",                      46_000),
    ("Blue Ridge Manufacturing",              42_000),
    # Customers 16-30 (total: $359,000)
    ("Summit Storage Solutions",              45_000),
    ("Lakeview Dental Group",                 40_000),
    ("Crestwood Veterinary Clinic",           36_000),
    ("Pinebrook Elementary School",           33_000),
    ("Coastal Auto Dealership",               30_000),
    ("Ridgeline Brewery",                     27_000),
    ("Central Library District",              25_000),
    ("Maple Street Fitness",                  22_000),
    ("Harbor Freight Industrial",             20_000),
    ("Sunrise Child Care Center",             18_000),
    ("Midtown Law Offices LLC",               16_000),
    ("Rocky Mountain Realty",                 14_000),
    ("Parkside Restaurant Group",             12_000),
    ("Elm Street Pharmacy",                   11_000),
    ("Valley Urgent Care",                    10_000),
    # Customers 31-47 (total: $359,000)
    ("Thompson Family Trust",                 50_000),
    ("Garcia Enterprises",                    48_000),
    ("Willowbrook HOA",                       38_000),
    ("Chen & Associates CPA",                 32_000),
    ("Ferndale Coffee Roasters",              28_000),
    ("Miller Veterinary Services",            24_000),
    ("Oakdale Preschool",                     21_000),
    ("Santos Plumbing & HVAC",                18_000),
    ("Birchwood Pet Resort",                  16_000),
    ("Lakewood Yoga Studio",                  14_000),
    ("Patel Family Restaurant",               13_000),
    ("Sunrise Bakery & Cafe",                 12_000),
    ("Anderson Chiropractic",                 11_000),
    ("River Road Auto Repair",                10_000),
    ("Meadowbrook Tutoring",                   9_000),
    ("Hilltop Barbershop",                     8_000),
    ("Kim's Dry Cleaning",                     7_000),
]

assert len(CUSTOMERS) == 47, f"Expected 47 customers, got {len(CUSTOMERS)}"
assert sum(r for _, r in CUSTOMERS) == TOTAL_REVENUE, (
    f"Customer revenue sum {sum(r for _, r in CUSTOMERS):,} != {TOTAL_REVENUE:,}"
)


def generate_customer_pdf():
    filepath = os.path.join(OUTPUT_DIR, "acme_hvac_customers_2023.pdf")
    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        leftMargin=0.8*inch, rightMargin=0.8*inch,
        topMargin=0.8*inch, bottomMargin=0.8*inch
    )
    styles = _base_styles()
    elems = []

    elems.append(Paragraph("ACME HVAC SERVICES, LLC", styles["CompanyName"]))
    elems.append(Paragraph("Customer Revenue Schedule", styles["DocTitle"]))
    elems.append(Paragraph("Fiscal Year Ended December 31, 2023", styles["SubTitle"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3c5e")))
    elems.append(Spacer(1, 0.12*inch))

    HEADER  = colors.HexColor("#1a3c5e")
    LIGHT   = colors.HexColor("#e8f0f7")
    WARN    = colors.HexColor("#fff3cd")
    CAUTION = colors.HexColor("#fde8c8")

    rows = [["#", "Customer Name", "2023 Revenue", "% of Total", "Cumulative %"]]
    cum = 0.0
    for i, (name, rev) in enumerate(CUSTOMERS):
        pct = rev / TOTAL_REVENUE * 100
        cum += pct
        rows.append([
            str(i + 1),
            name,
            _fmt(rev),
            _pct(pct),
            _pct(cum),
        ])

    # Totals row
    rows.append(["", "TOTAL — 47 Customers", _fmt(TOTAL_REVENUE), "100.0%", "100.0%"])

    col_w = [0.35*inch, 3.4*inch, 1.2*inch, 0.85*inch, 0.95*inch]
    t = Table(rows, colWidths=col_w, repeatRows=1)

    style_cmds = [
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT]),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        # Totals row
        ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#c8d8ea")),
        ("LINEABOVE",  (0, -1), (-1, -1), 1, HEADER),
    ]

    # Highlight top customer (>15% = high risk)
    style_cmds.append(("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8d7da")))
    style_cmds.append(("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"))

    # Caution top 5
    for r in range(2, 6):
        style_cmds.append(("BACKGROUND", (0, r), (-1, r), CAUTION))

    t.setStyle(TableStyle(style_cmds))
    elems.append(t)

    elems.append(Spacer(1, 0.12*inch))

    # Concentration summary box
    top1_pct  = CUSTOMERS[0][1] / TOTAL_REVENUE * 100
    top3_rev  = sum(r for _, r in CUSTOMERS[:3])
    top3_pct  = top3_rev / TOTAL_REVENUE * 100
    top5_rev  = sum(r for _, r in CUSTOMERS[:5])
    top5_pct  = top5_rev / TOTAL_REVENUE * 100
    top10_rev = sum(r for _, r in CUSTOMERS[:10])
    top10_pct = top10_rev / TOTAL_REVENUE * 100

    summary_rows = [
        ["Concentration Summary", "Revenue", "% of Total"],
        ["Top 1 Customer",  _fmt(CUSTOMERS[0][1]), _pct(top1_pct)],
        ["Top 3 Customers", _fmt(top3_rev),        _pct(top3_pct)],
        ["Top 5 Customers", _fmt(top5_rev),        _pct(top5_pct)],
        ["Top 10 Customers",_fmt(top10_rev),       _pct(top10_pct)],
    ]
    st = Table(summary_rows, colWidths=[2.2*inch, 1.2*inch, 1.0*inch])
    st.setStyle(TableStyle([
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("ALIGN",      (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("BOX",        (0, 0), (-1, -1), 0.5, HEADER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
    ]))
    elems.append(st)

    elems.append(Spacer(1, 0.12*inch))
    elems.append(Paragraph(
        "Red row: single customer >15% of revenue (high concentration risk). "
        "Orange rows: top-5 customers collectively = 68% of revenue.",
        styles["Footer"]
    ))

    doc.build(elems)
    print(f"  ✓ Customer PDF → {filepath}")
    return filepath


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating demo data in: {OUTPUT_DIR}")
    generate_pl_pdf()
    generate_bank_pdf()
    generate_customer_pdf()
    print("\nAll 3 PDFs generated. Ready for QoE analysis.")
