import re
import pandas as pd
from anthropic import Anthropic
from utils import save_artifact

client = Anthropic()


def concentration_analyzer(state: dict) -> dict:
    run_id = state["run_id"]
    docs   = state["ingestion"]["docs"]

    cust_doc = next((d for d in docs if d["type"] == "customer_list"), None)
    if not cust_doc:
        return {
            "concentration": {"error": "No customer_list document found"},
            "status_log":    ["⚠ Concentration — no customer list found, skipping"],
        }

    df = _parse_customer_table(cust_doc)

    if df is None or df.empty:
        return {
            "concentration": {"error": "Could not parse customer table"},
            "status_log":    ["⚠ Concentration — could not parse table"],
        }

    total_rev = df["revenue"].sum()
    df = df.sort_values("revenue", ascending=False).reset_index(drop=True)
    df["pct_of_total"] = (df["revenue"] / total_rev * 100).round(2)
    df["cumulative_pct"] = df["pct_of_total"].cumsum().round(2)

    def top_n(n):
        subset = df.head(n)
        return {
            "revenue":     int(subset["revenue"].sum()),
            "pct_of_total": round(subset["pct_of_total"].sum(), 1),
        }

    result = {
        "source_file":   cust_doc["filename"],
        "total_revenue": int(total_rev),
        "customer_count": len(df),
        "top_customer": {
            "name":    df.iloc[0]["name"],
            "revenue": int(df.iloc[0]["revenue"]),
            "pct_of_total": float(df.iloc[0]["pct_of_total"]),
        },
        "top_1":  top_n(1),
        "top_3":  top_n(3),
        "top_5":  top_n(5),
        "top_10": top_n(10),
        "concentration_risk": df.iloc[0]["pct_of_total"] > 15,
        "top_customers_list": df.head(10)[["name", "revenue", "pct_of_total"]].to_dict("records"),
    }

    save_artifact(run_id, "concentration.json", result)

    top1 = result["top_customer"]
    status = (
        f"✓ Concentration analysis — {result['customer_count']} customers | "
        f"Top customer: {top1['name']} = {top1['pct_of_total']:.1f}% | "
        f"Top 5 = {result['top_5']['pct_of_total']}%"
    )
    return {"concentration": result, "status_log": [status]}


def _parse_customer_table(cust_doc: dict):
    # Text-first: pdfplumber's raw text covers all pages without page-break gaps.
    # The structured table approach misses rows that fall at page boundaries.
    df = _parse_from_text(cust_doc["text"])
    if df is not None and len(df) >= 20:
        return df

    # Fallback: accumulate records from all table slices across pages.
    all_records = []
    for table in cust_doc.get("tables", []):
        if not table:
            continue
        if len(table[0]) == 1:
            part = _parse_single_col_table(table)
        else:
            part = _table_to_df(table)
        if part is not None and not part.empty:
            all_records.append(part)

    if all_records:
        combined = pd.concat(all_records, ignore_index=True)
        combined = combined.drop_duplicates(subset=["name"]).reset_index(drop=True)
        if len(combined) > 5:
            return combined

    return None


def _parse_single_col_table(table: list):
    """
    Handles tables where pdfplumber collapses all columns into one cell.
    Each row looks like: "1 Customer Name LLC $1,302,000 31.0% 31.0%"
    """
    # Pattern: leading row number (optional), name, dollar amount, percentages
    ROW_RE = re.compile(
        r"^\s*(\d+)\s+(.+?)\s+\$([\d,]+)\s+([\d.]+%)\s+([\d.]+%)\s*$"
    )
    records = []
    for row in table:
        cell = row[0] if row else ""
        if not cell:
            continue
        m = ROW_RE.match(str(cell).strip())
        if m:
            name = m.group(2).strip()
            rev  = int(m.group(3).replace(",", ""))
            if name and rev > 0 and "total" not in name.lower():
                records.append({"name": name, "revenue": rev})
    return pd.DataFrame(records) if records else None


def _clean_dollar(val: str) -> int:
    if not val or not isinstance(val, str):
        return 0
    cleaned = re.sub(r"[$,\s]", "", val).strip()
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def _table_to_df(table: list):
    if not table or len(table) < 3:
        return None

    header_idx = None
    for i, row in enumerate(table):
        row_str = " ".join(str(c) for c in (row or []) if c)
        if re.search(r"customer name|customer|# customer", row_str, re.IGNORECASE):
            header_idx = i
            break

    if header_idx is None:
        return None

    headers = [str(c).strip().lower() if c else "" for c in table[header_idx]]
    name_col = next((i for i, h in enumerate(headers)
                     if "name" in h or "customer" in h), None)
    rev_col  = next((i for i, h in enumerate(headers)
                     if "revenue" in h or "amount" in h), None)

    if name_col is None or rev_col is None:
        return None

    records = []
    for row in table[header_idx + 1:]:
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
        name = str(row[name_col]).strip() if row[name_col] else ""
        rev  = _clean_dollar(str(row[rev_col]) if row[rev_col] else "")
        if name and rev > 0 and "total" not in name.lower():
            records.append({"name": name, "revenue": rev})

    return pd.DataFrame(records) if records else None


def _parse_from_text(text: str):
    """Parse from raw text as last resort. Handles merged-column PDF text."""
    ROW_RE = re.compile(
        r"^\s*(\d+)\s+(.+?)\s+\$([\d,]+)\s+([\d.]+%)\s+([\d.]+%)\s*$"
    )
    records = []
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if m:
            name = m.group(2).strip()
            rev  = int(m.group(3).replace(",", ""))
            if name and rev > 0 and "total" not in name.lower():
                records.append({"name": name, "revenue": rev})
    return pd.DataFrame(records) if records else None
