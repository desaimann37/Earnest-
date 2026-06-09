# Earnest — by Verity

**Agentic Quality of Earnings engine for SMB acquisitions.**

Drop in a P&L, bank statement, and customer list. Get a draft QoE memo in ~2 minutes.

## What it does

7-agent LangGraph pipeline powered by Claude:

1. **Ingestion** — classifies and parses PDFs
2. **Financial Spreader** — builds 3-year income statement
3. **EBITDA Normalizer** — identifies add-backs from bank statements
4. **Concentration Analyzer** — computes customer revenue concentration
5. **Risk Flagger** — synthesizes ranked risk flags
6. **Memo Writer** — drafts full QoE memo with source citations
7. **PDF Exporter** — renders professional PDF

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY
python scripts/generate_demo_data.py   # generate Acme HVAC demo data
streamlit run app.py
```

## Demo

Load the **Acme HVAC Services** demo from the sidebar — 3 synthetic PDFs pre-loaded, run the full pipeline in ~2 minutes.

---

*Built for Founders Inc — June 2026*
