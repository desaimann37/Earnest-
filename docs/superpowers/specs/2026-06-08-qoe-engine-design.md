# QoE Engine — Design Spec
_Date: 2026-06-08_

## Overview
Agentic Quality of Earnings engine for SMB acquisitions. Accepts a folder of deal documents, produces a draft QoE memo in ~2 minutes. Demo target: Founders Inc (venture studio).

## Architecture
Sequential LangGraph `StateGraph` — 7 nodes, no conditional edges. Single `QoEState` TypedDict. State checkpointed to `/runs/{run_id}/` after each node.

## State Shape
```
run_id, doc_dir, ingestion, spread, ebitda, concentration, risks, memo, pdf_path
status_log: Annotated[list, operator.add]  # appended per agent
```

## Agent Sequence
ingestion → spreader → normalizer → concentration → risk_flagger → memo_writer → pdf_exporter

## Demo Data
ReportLab PDFs: Acme HVAC Services
- P&L: FY2021-2023, $3.1M→$3.8M→$4.2M, ~43% gross margin, ~$850K EBITDA yr3
- Bank: 12-month 2023, J. Hayes consulting $48K/yr, F-150 purchase $22K
- Customers: 47 customers, top = 31%, top-5 = 68%

## Model
claude-sonnet-4-6

## Artifacts per run
spread.csv, ebitda_bridge.json, concentration.json, risks.json, memo.md, memo.pdf
