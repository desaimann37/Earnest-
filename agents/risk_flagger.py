import json
from anthropic import Anthropic
from utils import save_artifact

client = Anthropic()

_SYSTEM = """You are a sell-side M&A advisor reviewing a Quality of Earnings package for a potential acquisition target.

Analyze the provided financial data and identify 5–7 material risks a buyer should evaluate. Each risk should be specific to this company's data — no generic boilerplate.

Return ONLY valid JSON array — no markdown, no explanation:
[
  {
    "title":       "string (concise risk name, ≤8 words)",
    "severity":    "high | medium | low",
    "description": "string (2-3 sentences, specific to the data — include actual numbers)",
    "citation":    "string (exact source: document name + data point)"
  }
]

Severity guide:
- high:   deal-breaker or significant valuation impact if not resolved
- medium: warrants diligence but manageable with reps/warranties or price adjustment
- low:    worth noting but unlikely to affect deal terms
"""


def risk_flagger(state: dict) -> dict:
    run_id        = state["run_id"]
    spread        = state.get("spread", {})
    ebitda        = state.get("ebitda", {})
    concentration = state.get("concentration", {})

    # Build context
    metrics = spread.get("metrics", {})
    periods = spread.get("parsed", {}).get("periods", [])

    metrics_text = "\n".join(
        f"  {p}: Revenue ${m['revenue']:,} | "
        f"EBITDA ${m['ebitda']:,} ({m['ebitda_margin_pct']}% margin)"
        + (f" | Growth {m.get('revenue_growth_pct', 'N/A')}%" if 'revenue_growth_pct' in m else "")
        for p, m in metrics.items()
    )

    addbacks_text = "\n".join(
        f"  - {a['description']}: +${a['amount']:,} ({a['category']}) — {a['justification']}"
        for a in ebitda.get("add_backs", [])
    )

    top_customers_text = "\n".join(
        f"  {i+1}. {c['name']}: ${c['revenue']:,} ({c['pct_of_total']}%)"
        for i, c in enumerate(concentration.get("top_customers_list", [])[:5])
    )

    user_content = f"""
FINANCIAL PERFORMANCE:
{metrics_text}

EBITDA BRIDGE:
  Reported EBITDA: ${ebitda.get('reported_ebitda', 0):,}
  Total Add-backs: ${ebitda.get('total_addbacks', 0):,}
  Adjusted EBITDA: ${ebitda.get('adjusted_ebitda', 0):,}
  Add-back detail:
{addbacks_text}

CUSTOMER CONCENTRATION:
  Total customers: {concentration.get('customer_count', 'N/A')}
  Top customer: {concentration.get('top_customer', {}).get('name', 'N/A')} = {concentration.get('top_customer', {}).get('pct_of_total', 0):.1f}%
  Top 5 customers: {concentration.get('top_5', {}).get('pct_of_total', 'N/A')}%
  Top customer list:
{top_customers_text}

EBITDA NORMALIZER NOTES:
{ebitda.get('notes', 'None')}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else parts[0]
    risks = json.loads(raw)

    save_artifact(run_id, "risks.json", risks)

    high   = sum(1 for r in risks if r["severity"] == "high")
    medium = sum(1 for r in risks if r["severity"] == "medium")
    status = (
        f"✓ Risk flags — {len(risks)} risks identified "
        f"({high} high, {medium} medium, {len(risks)-high-medium} low)"
    )
    return {"risks": risks, "status_log": [status]}
