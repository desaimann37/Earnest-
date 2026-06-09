import json
import os
from datetime import datetime
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(BASE_DIR, "runs")


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]


def run_dir(run_id: str) -> str:
    path = os.path.join(RUNS_DIR, run_id)
    os.makedirs(path, exist_ok=True)
    return path


def save_artifact(run_id: str, filename: str, data, is_json: bool = True) -> str:
    rdir = run_dir(run_id)
    filepath = os.path.join(rdir, filename)
    if is_json:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
    return filepath


def load_artifact(run_id: str, filename: str):
    filepath = os.path.join(RUNS_DIR, run_id, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        if filename.endswith(".json"):
            return json.load(f)
        return f.read()
