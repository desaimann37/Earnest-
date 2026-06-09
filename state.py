from typing import TypedDict, Optional, Annotated
import operator


class QoEState(TypedDict):
    run_id: str
    doc_dir: str
    ingestion: Optional[dict]
    spread: Optional[dict]
    ebitda: Optional[dict]
    concentration: Optional[dict]
    risks: Optional[list]
    memo: Optional[str]
    pdf_path: Optional[str]
    status_log: Annotated[list, operator.add]
