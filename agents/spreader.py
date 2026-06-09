import json
import os
import pandas as pd
from anthropic import Anthropic
from utils import save_artifact, run_dir

client = Anthropic()

_SYSTEM = """You are a financial analyst extracting structured data from an income statement.

Return ONLY valid JSON — no markdown fences, no explanation. Structure:
{
  "company": "string",
  "periods": ["FY2021", "FY2022", "FY2023"],
  "revenue":       [int, int, int],
  "cogs":          [int, int, int],
  "gross_profit":  [int, int, int],
  "line_items": [
    {"name": "exact name from document", "values": [int, int, int]}
  ],
  "da":     [int, int, int],
  "ebitda": [int, int, int]
}

Rules:
- All monetary values are plain integers (no $ signs, no commas)
- line_items = operating expense line items only (not revenue, COGS, or EBITDA)
- Use the exact line item names as they appear in the source document
- If a value is missing for a period, use 0
"""


def financial_spreader(state: dict) -> dict:
    run_id = state["run_id"]
    docs   = state["ingestion"]["docs"]

    pl_doc = next((d for d in docs if d["type"] == "profit_loss"), None)
    if not pl_doc:
        return {
            "spread":     {"error": "No profit_loss document found"},
            "status_log": ["⚠ Spreader — no P&L document found, skipping"],
        }

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        system=_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Source: {pl_doc['filename']}\n\n"
                f"Income Statement:\n{pl_doc['text']}"
            ),
        }],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else parts[0]
    data = json.loads(raw)

    periods = data["periods"]

    # Build DataFrame
    df_rows = (
        [("Revenue",      data["revenue"]),
         ("COGS",         data["cogs"]),
         ("Gross Profit", data["gross_profit"])]
        + [(item["name"], item["values"]) for item in data["line_items"]]
        + [("D&A",    data["da"]),
           ("EBITDA", data["ebitda"])]
    )
    df = pd.DataFrame(
        {p: [v[i] for _, v in df_rows] for i, p in enumerate(periods)},
        index=[label for label, _ in df_rows],
    )
    df.index.name = "Line Item"

    # Metrics per period
    metrics = {}
    for i, p in enumerate(periods):
        rev    = data["revenue"][i]
        gp     = data["gross_profit"][i]
        ebitda = data["ebitda"][i]
        metrics[p] = {
            "revenue":           rev,
            "gross_profit":      gp,
            "gross_margin_pct":  round(gp     / rev * 100, 1) if rev else 0,
            "ebitda":            ebitda,
            "ebitda_margin_pct": round(ebitda / rev * 100, 1) if rev else 0,
        }
    for i in range(1, len(periods)):
        prev = data["revenue"][i - 1]
        curr = data["revenue"][i]
        if prev:
            metrics[periods[i]]["revenue_growth_pct"] = round((curr - prev) / prev * 100, 1)

    csv_path = os.path.join(run_dir(run_id), "spread.csv")
    df.to_csv(csv_path)

    result = {
        "source_file": pl_doc["filename"],
        "parsed":      data,
        "metrics":     metrics,
        "csv_path":    csv_path,
    }
    save_artifact(run_id, "spread.json", {**result, "csv_path": csv_path})

    last = periods[-1]
    m = metrics[last]
    status = (
        f"✓ Financials spread — {last}: "
        f"Revenue ${m['revenue']:,.0f} | "
        f"EBITDA ${m['ebitda']:,.0f} ({m['ebitda_margin_pct']}% margin)"
    )
    return {"spread": result, "status_log": [status]}
