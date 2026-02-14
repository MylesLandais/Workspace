from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uuid
import time

app = FastAPI(title="Comfy Mock Server")

class Workflow(BaseModel):
    nodes: list
    metadata: dict = {}

_store: Dict[str, Dict] = {}

@app.post("/run_workflow")
async def run_workflow(wf: Workflow):
    run_id = str(uuid.uuid4())
    _store[run_id] = {"status": "running", "workflow": wf.dict(), "created": time.time(), "result": None}
    # Simulate quick processing
    _store[run_id]["status"] = "completed"
    _store[run_id]["result"] = {"image_path": f"/tmp/{run_id}.png"}
    return {"run_id": run_id, "status": _store[run_id]["status"]}

@app.get("/results/{run_id}")
async def get_results(run_id: str):
    if run_id not in _store:
        raise HTTPException(status_code=404, detail="run_id not found")
    return {"run_id": run_id, **_store[run_id]}

@app.get("/health")
async def health():
    return {"status": "ok"}
