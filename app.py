import os
import sys
import json

# Ensure project root is on path when launched from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from utils import new_run_id, run_dir, RUNS_DIR

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Earnest by Verity",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
.status-log { font-family: monospace; font-size: 0.85rem; line-height: 1.7; }
.status-log .done   { color: #1a8e2a; }
.status-log .active { color: #2563eb; font-weight: bold; }
.status-log .warn   { color: #d68910; }
.artifact-link { font-size: 0.8rem; color: #555; }
[data-testid="stSidebar"] { background: #f0f4f8; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Earnest")
    st.markdown("*by **Verity** — Agentic Quality of Earnings*")
    st.divider()

    if "run_id" in st.session_state and st.session_state.run_id:
        rid = st.session_state.run_id
        rdir = run_dir(rid)
        st.markdown(f"**Run ID**")
        st.code(rid, language=None)
        st.markdown("**Artifacts**")

        artifacts = [
            ("spread.csv",           "📊 Financial Spread"),
            ("ebitda_bridge.json",   "🔢 EBITDA Bridge"),
            ("concentration.json",   "👥 Concentration"),
            ("risks.json",           "⚠ Risk Flags"),
            ("memo.md",              "📝 Memo (Markdown)"),
        ]
        for fname, label in artifacts:
            fpath = os.path.join(rdir, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    st.download_button(
                        label=label,
                        data=f.read(),
                        file_name=fname,
                        key=f"dl_{fname}",
                    )
    else:
        st.markdown("*Run an analysis to see artifacts.*")

    st.divider()
    st.markdown("**Demo data**")
    if st.button("Load Acme HVAC demo"):
        demo_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "demo_data", "acme_hvac"
        )
        pdfs = [f for f in os.listdir(demo_dir) if f.endswith(".pdf")] if os.path.exists(demo_dir) else []
        if pdfs:
            st.session_state["demo_files"] = demo_dir
            st.success(f"{len(pdfs)} demo files ready")
        else:
            st.error("Run `python scripts/generate_demo_data.py` first")


# ── Main page ───────────────────────────────────────────────────────────────
st.title("Earnest — Quality of Earnings Engine")
st.markdown(
    "Upload deal documents (P&L, bank statements, customer list) "
    "and generate a draft QoE memo in ~2 minutes. *Powered by Verity.*"
)

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_files = st.file_uploader(
        "Drop documents here",
        accept_multiple_files=True,
        type=["pdf", "csv", "xlsx"],
        help="Supported: P&L (PDF), Bank Statements (PDF), Customer List (PDF/CSV)",
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

# Check for demo mode
using_demo = st.session_state.get("demo_files") and not uploaded_files

if run_btn and (uploaded_files or using_demo):

    # ── Set up run ──────────────────────────────────────────────────────────
    rid    = new_run_id()
    doc_dir = os.path.join(run_dir(rid), "docs")
    os.makedirs(doc_dir, exist_ok=True)

    if using_demo:
        import shutil
        demo_dir = st.session_state["demo_files"]
        for fname in os.listdir(demo_dir):
            if fname.endswith(".pdf"):
                shutil.copy(os.path.join(demo_dir, fname), os.path.join(doc_dir, fname))
    else:
        for f in uploaded_files:
            with open(os.path.join(doc_dir, f.name), "wb") as out:
                out.write(f.read())

    st.session_state["run_id"] = rid

    # ── Status panel ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Analysis Status")
    status_placeholder = st.empty()
    log_lines: list[str] = []

    def append_log(msg: str):
        log_lines.append(msg)
        html = "<div class='status-log'>" + "".join(
            f"<div class='{'done' if msg.startswith('✓') else 'active' if msg.startswith('→') else 'warn'}'>{msg}</div>"
            for msg in log_lines
        ) + "</div>"
        status_placeholder.markdown(html, unsafe_allow_html=True)

    append_log(f"→ Starting run {rid} — {len(os.listdir(doc_dir))} documents loaded")

    # ── Import and stream graph ─────────────────────────────────────────────
    try:
        from graph import qoe_graph

        initial_state = {
            "run_id":        rid,
            "doc_dir":       doc_dir,
            "ingestion":     None,
            "spread":        None,
            "ebitda":        None,
            "concentration": None,
            "risks":         None,
            "memo":          None,
            "pdf_path":      None,
            "status_log":    [],
        }

        # Agent display names for "→ Running X..." pre-step messages
        AGENT_LABELS = {
            "ingestion":     "Parsing and classifying documents",
            "spreader":      "Spreading financials",
            "normalizer":    "Normalizing EBITDA",
            "concentration": "Analyzing customer concentration",
            "risk_flagger":  "Flagging risks",
            "memo_writer":   "Drafting QoE memo",
            "pdf_exporter":  "Exporting PDF",
        }

        final_state = {**initial_state}

        for chunk in qoe_graph.stream(initial_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                # Pre-step "running" message
                label = AGENT_LABELS.get(node_name, node_name)
                append_log(f"→ {label}...")

                # Post-step completion messages
                for msg in updates.get("status_log", []):
                    append_log(msg)

                # Merge updates into final state
                final_state.update(updates)

        append_log("✓ Analysis complete")

        # ── Memo display ────────────────────────────────────────────────────
        st.divider()
        st.markdown("### Quality of Earnings Memorandum")

        memo_md = final_state.get("memo", "")
        if memo_md:
            st.markdown(memo_md)
        else:
            st.warning("Memo generation failed — check logs above.")

        # ── PDF download ────────────────────────────────────────────────────
        pdf_path = final_state.get("pdf_path", "")
        if pdf_path and os.path.exists(pdf_path):
            st.divider()
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇ Download QoE Memo (PDF)",
                    data=f.read(),
                    file_name="qoe_memo_acme_hvac.pdf",
                    mime="application/pdf",
                    type="primary",
                )

    except Exception as e:
        st.error(f"Analysis failed: {e}")
        raise

elif run_btn:
    st.warning("Please upload documents or load the demo data first.")

# ── Intro when idle ──────────────────────────────────────────────────────────
if not run_btn:
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**What this produces**")
        st.markdown("""
- 3-year financial spread
- EBITDA bridge with add-backs
- Customer concentration analysis
- 5–7 risk flags with severity
- 2–3 page QoE memo (PDF)
        """)
    with col_b:
        st.markdown("**7-agent pipeline**")
        st.markdown("""
1. `ingestion` — classify & parse docs
2. `spreader` — build income statement
3. `normalizer` — identify add-backs
4. `concentration` — revenue by customer
5. `risk_flagger` — flag material risks
6. `memo_writer` — draft QoE memo
7. `pdf_exporter` — render PDF
        """)
    with col_c:
        st.markdown("**Every run saves**")
        st.markdown("""
- `spread.csv` — clean financials
- `ebitda_bridge.json` — add-back detail
- `concentration.json` — customer stats
- `risks.json` — structured risk list
- `memo.md` + `memo.pdf` — final output
        """)
