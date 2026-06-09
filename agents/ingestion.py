import os
import pdfplumber
from anthropic import Anthropic
from utils import save_artifact

client = Anthropic()

_CLASSIFY_SYSTEM = """Classify this financial document. Return ONLY one of these exact labels — nothing else:
profit_loss
bank_statement
customer_list
tax_return
other"""


def ingestion_agent(state: dict) -> dict:
    doc_dir = state["doc_dir"]
    run_id  = state["run_id"]

    files = sorted([
        f for f in os.listdir(doc_dir)
        if not f.startswith(".") and os.path.isfile(os.path.join(doc_dir, f))
    ])

    docs = []
    for filename in files:
        filepath = os.path.join(doc_dir, filename)
        text, tables = _extract(filepath)
        doc_type = _classify(filename, text)
        docs.append({
            "filename": filename,
            "filepath": filepath,
            "type":     doc_type,
            "text":     text,
            "tables":   tables,
        })

    result = {"docs": docs, "doc_count": len(docs)}

    # Save lightweight version (no raw text) for inspection
    save_artifact(run_id, "ingestion.json", {
        "doc_count": len(docs),
        "docs": [{"filename": d["filename"], "type": d["type"]} for d in docs],
    })

    types_summary = ", ".join(d["type"] for d in docs)
    return {
        "ingestion":  result,
        "status_log": [f"✓ Ingestion — {len(docs)} docs parsed ({types_summary})"],
    }


def _extract(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()
    text, tables = "", []

    if ext == ".pdf":
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                for tbl in (page.extract_tables() or []):
                    if tbl:
                        tables.append(tbl)
    elif ext == ".csv":
        import pandas as pd
        df = pd.read_csv(filepath)
        text = df.to_string()
        tables = [df.values.tolist()]

    return text, tables


def _classify(filename: str, text: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=20,
        system=_CLASSIFY_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Filename: {filename}\n\nFirst 1500 chars:\n{text[:1500]}"
        }],
    )
    return response.content[0].text.strip().lower()
