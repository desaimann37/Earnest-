from langgraph.graph import StateGraph, END
from state import QoEState
from agents.ingestion     import ingestion_agent
from agents.spreader      import financial_spreader
from agents.normalizer    import ebitda_normalizer
from agents.concentration import concentration_analyzer
from agents.risk_flagger  import risk_flagger
from agents.memo_writer   import memo_writer
from agents.pdf_exporter  import pdf_exporter


def build_graph():
    g = StateGraph(QoEState)

    g.add_node("ingestion",     ingestion_agent)
    g.add_node("spreader",      financial_spreader)
    g.add_node("normalizer",    ebitda_normalizer)
    g.add_node("concentration", concentration_analyzer)
    g.add_node("risk_flagger",  risk_flagger)
    g.add_node("memo_writer",   memo_writer)
    g.add_node("pdf_exporter",  pdf_exporter)

    g.set_entry_point("ingestion")
    g.add_edge("ingestion",     "spreader")
    g.add_edge("spreader",      "normalizer")
    g.add_edge("normalizer",    "concentration")
    g.add_edge("concentration", "risk_flagger")
    g.add_edge("risk_flagger",  "memo_writer")
    g.add_edge("memo_writer",   "pdf_exporter")
    g.add_edge("pdf_exporter",  END)

    return g.compile()


qoe_graph = build_graph()
