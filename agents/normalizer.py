import json
from anthropic import Anthropic
from utils import save_artifact

client = Anthropic()

_SYSTEM = """You are a Quality of Earnings analyst specializing in EBITDA normalization for SMB acquisitions.

Review the income statement data and bank statement provided. Identify potential EBITDA add-backs — expenses that should be excluded from normalized EBITDA because they are:
1. Owner compensation above fair market rate
2. Personal expenses run through the business
3. Related-party transactions at non-market rates
4. One-time or non-recurring items

For each add-back:
- Be specific: quote the exact line item or transaction from the source
- Justify each add-back with a brief, defensible rationale
- Use market data or benchmarks where relevant (e.g., "market CEO comp for $4M HVAC = ~$120K")

Return ONLY valid JSON — no markdown, no explanation:
{
  "reported_ebitda": int,
  "add_backs": [
    {
      "description": "string (clear label for the bridge line)",
      "amount":       int,
      "category":     "owner_comp | personal_expense | one_time | related_party | other",
      "justification": "string (1-2 sentences)",
      "citation":     "string (e.g., 'P&L FY2023, line: Owner Compensation $210,000')"
    }
  ],
  "adjusted_ebitda": int,
  "notes": "string (any caveats or items requiring further diligence)"
}
"""


def ebitda_normalizer(state: dict) -> dict:
    run_id = state["run_id"]
    spread = state.get("spread", {})
    docs   = state["ingestion"]["docs"]

    bank_doc = next((d for d in docs if d["type"] == "bank_statement"), None)

    # Build context for Claude
    last_period = spread["parsed"]["periods"][-1] if spread.get("parsed") else "FY2023"
    metrics     = spread.get("metrics", {}).get(last_period, {})
    reported_ebitda = metrics.get("ebitda", 0)

    line_items_summary = "\n".join(
        f"  - {item['name']}: ${item['values'][-1]:,}"
        for item in spread.get("parsed", {}).get("line_items", [])
    )

    bank_text = bank_doc["text"][:8000] if bank_doc else "(bank statement not available)"

    user_content = f"""
INCOME STATEMENT — {last_period} Operating Expenses:
{line_items_summary}

Reported EBITDA ({last_period}): ${reported_ebitda:,}
Source document: {spread.get('source_file', 'P&L')}

BANK STATEMENT (2023):
{bank_text}
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
    data = json.loads(raw)

    # Verify math
    total_addbacks = sum(a["amount"] for a in data["add_backs"])
    data["adjusted_ebitda"] = data["reported_ebitda"] + total_addbacks
    data["total_addbacks"]  = total_addbacks

    save_artifact(run_id, "ebitda_bridge.json", data)

    status = (
        f"✓ EBITDA normalized — "
        f"Reported: ${data['reported_ebitda']:,} → "
        f"Adjusted: ${data['adjusted_ebitda']:,} "
        f"({len(data['add_backs'])} add-backs, +${total_addbacks:,})"
    )
    return {"ebitda": data, "status_log": [status]}
