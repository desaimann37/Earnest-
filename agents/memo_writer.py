import json
import os
from anthropic import Anthropic
from utils import save_artifact, run_dir

client = Anthropic()

_SYSTEM = """You are a senior CPA at a mid-market advisory firm writing a Quality of Earnings (QoE) memorandum for a private equity buy-side engagement.

REQUIREMENTS — non-negotiable:
1. Every factual claim must carry an inline citation: [Source: <filename>, <section/table>, <specific line or value>]
2. Professional, tight prose — no hedging ("it appears", "it seems", "it may be"). State conclusions directly.
3. Numbers must exactly match the data provided to you. Do not invent or round values.
4. Sections in this order: Executive Summary, Financial Overview, EBITDA Bridge, Customer Concentration, Working Capital & Seasonality, Risk Flags, Recommended Next Steps.
5. Write in markdown. Use ## for section headers, **bold** for key figures, tables where appropriate.
6. Length: 2–3 pages when rendered (roughly 900–1400 words).
7. The Executive Summary must state: company, transaction context, adjusted EBITDA, and the single highest-risk finding.
8. The EBITDA Bridge section must present a formatted markdown table: Reported EBITDA → each add-back line → Adjusted EBITDA.
9. The Risk Flags section must list each risk with its severity badge ([HIGH], [MEDIUM], [LOW]) and a one-sentence mitigation.
10. Recommended Next Steps: 3–5 specific, actionable items — not generic advice.
"""


def memo_writer(state: dict) -> dict:
    run_id        = state["run_id"]
    spread        = state.get("spread", {})
    ebitda        = state.get("ebitda", {})
    concentration = state.get("concentration", {})
    risks         = state.get("risks", [])
    docs          = state["ingestion"]["docs"]

    # Build comprehensive data payload
    payload = _build_payload(spread, ebitda, concentration, risks, docs)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                "Write the Quality of Earnings memorandum for the following deal.\n\n"
                "=== FINANCIAL DATA ===\n" + payload
            ),
        }],
    )

    memo_md = response.content[0].text.strip()

    # Save markdown
    md_path = os.path.join(run_dir(run_id), "memo.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(memo_md)
    save_artifact(run_id, "memo.md", memo_md, is_json=False)

    word_count = len(memo_md.split())
    status = f"✓ Memo drafted — {word_count:,} words, {len(risks)} risk flags cited"
    return {"memo": memo_md, "status_log": [status]}


def _build_payload(spread, ebitda, concentration, risks, docs) -> str:
    lines = []

    # Company
    company = spread.get("parsed", {}).get("company", "Acme HVAC Services, LLC")
    lines.append(f"COMPANY: {company}")
    lines.append(f"TRANSACTION: Buy-side QoE, preliminary diligence\n")

    # Financial performance
    lines.append("--- FINANCIAL PERFORMANCE ---")
    for period, m in spread.get("metrics", {}).items():
        growth = f" | YoY Growth: {m.get('revenue_growth_pct', 'N/A')}%" if 'revenue_growth_pct' in m else ""
        lines.append(
            f"{period}: Revenue ${m['revenue']:,} | "
            f"Gross Profit ${m['gross_profit']:,} ({m['gross_margin_pct']}% margin) | "
            f"EBITDA ${m['ebitda']:,} ({m['ebitda_margin_pct']}% margin){growth}"
        )

    # P&L line items
    lines.append("\nOperating Expense Detail (most recent year):")
    for item in spread.get("parsed", {}).get("line_items", []):
        lines.append(f"  {item['name']}: ${item['values'][-1]:,}")
    lines.append(f"Source: {spread.get('source_file', 'P&L')}\n")

    # EBITDA bridge
    lines.append("--- EBITDA BRIDGE ---")
    lines.append(f"Reported EBITDA: ${ebitda.get('reported_ebitda', 0):,}")
    for ab in ebitda.get("add_backs", []):
        lines.append(
            f"  Add-back: {ab['description']} | "
            f"+${ab['amount']:,} | {ab['category']} | "
            f"{ab['justification']} | "
            f"[Source: {ab['citation']}]"
        )
    lines.append(f"Adjusted EBITDA: ${ebitda.get('adjusted_ebitda', 0):,}")
    if ebitda.get("notes"):
        lines.append(f"Notes: {ebitda['notes']}\n")

    # Customer concentration
    lines.append("--- CUSTOMER CONCENTRATION ---")
    lines.append(f"Total customers: {concentration.get('customer_count', 'N/A')}")
    lines.append(f"Total revenue: ${concentration.get('total_revenue', 0):,}")
    top = concentration.get("top_customer", {})
    lines.append(f"Top customer: {top.get('name', 'N/A')} — ${top.get('revenue', 0):,} ({top.get('pct_of_total', 0):.1f}%)")
    lines.append(f"Top 3: {concentration.get('top_3', {}).get('pct_of_total', 'N/A')}% | Top 5: {concentration.get('top_5', {}).get('pct_of_total', 'N/A')}% | Top 10: {concentration.get('top_10', {}).get('pct_of_total', 'N/A')}%")
    lines.append("Top 10 customers:")
    for i, c in enumerate(concentration.get("top_customers_list", [])[:10]):
        lines.append(f"  {i+1}. {c['name']}: ${c['revenue']:,} ({c['pct_of_total']}%)")
    lines.append(f"Source: {concentration.get('source_file', 'customer list')}\n")

    # Risks
    lines.append("--- RISK FLAGS ---")
    for r in risks:
        lines.append(
            f"[{r['severity'].upper()}] {r['title']}: {r['description']} | {r['citation']}"
        )

    # Document inventory
    lines.append("\n--- SOURCE DOCUMENTS ---")
    for d in docs:
        lines.append(f"  {d['filename']} → classified as: {d['type']}")

    return "\n".join(lines)
