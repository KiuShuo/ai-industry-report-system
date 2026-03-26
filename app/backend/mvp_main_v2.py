from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import json
import uuid
import time

from live_report_service_v2 import LiveReportServiceV2
from runtime_mode_selector import RuntimeModeSelector

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = DATA_DIR / "reports"
TASK_FILE = DATA_DIR / "tasks_v2.json"
REPORT_FILE = DATA_DIR / "reports_v2.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


tasks: Dict[str, dict] = load_json(TASK_FILE, {})
reports: Dict[str, dict] = load_json(REPORT_FILE, {})
service = LiveReportServiceV2()
mode_selector = RuntimeModeSelector()

app = FastAPI(title="AI Industry Report System V2", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateTaskRequest(BaseModel):
    topic: str
    timeRange: str = "7d"


def generate_report(task_id: str, topic: str, time_range: str):
    try:
        tasks[task_id]["status"] = "running"
        tasks[task_id]["mode"] = mode_selector.current_mode()
        save_json(TASK_FILE, tasks)
        time.sleep(1)

        result = service.generate(topic, time_range, prefer_deerflow=mode_selector.prefer_deerflow())
        report_id = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
        markdown = result.get("markdown", "") or json.dumps(result, ensure_ascii=False, indent=2)
        html = result.get("html", "")
        report_path = REPORT_DIR / f"{report_id}.md"
        report_path.write_text(markdown, encoding="utf-8")

        reports[report_id] = {
            "reportId": report_id,
            "taskId": task_id,
            "title": f"{topic}行业动态分析报告",
            "topic": topic,
            "timeRange": time_range,
            "summary": f"这是关于“{topic}”的自动生成行业动态分析报告。",
            "mode": result.get("mode", mode_selector.current_mode()),
            "markdownPath": str(report_path),
            "markdownContent": markdown,
            "htmlContent": html,
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        tasks[task_id]["status"] = "finished"
        tasks[task_id]["reportId"] = report_id
        tasks[task_id]["finishedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        save_json(REPORT_FILE, reports)
        save_json(TASK_FILE, tasks)
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        save_json(TASK_FILE, tasks)


@app.get("/")
def root():
    return {"msg": "AI Industry Report System V2 Running", "mode": mode_selector.current_mode()}


@app.get("/health")
def health():
    return {"status": "ok", "mode": mode_selector.current_mode()}


@app.post("/api/task/create")
def create_task(req: CreateTaskRequest, background_tasks: BackgroundTasks):
    task_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    tasks[task_id] = {
        "taskId": task_id,
        "topic": req.topic,
        "timeRange": req.timeRange,
        "status": "pending",
        "mode": mode_selector.current_mode(),
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_json(TASK_FILE, tasks)
    background_tasks.add_task(generate_report, task_id, req.topic, req.timeRange)
    return {"taskId": task_id, "status": "pending", "mode": mode_selector.current_mode()}


@app.get("/api/task/status/{task_id}")
def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.get("/api/report/{task_id}")
def get_report_by_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    report_id = task.get("reportId")
    if not report_id:
        return {"taskId": task_id, "status": task.get("status"), "report": None, "mode": task.get("mode")}
    return reports.get(report_id)


@app.get("/api/reports")
def list_reports():
    items: List[dict] = list(reports.values())
    items.sort(key=lambda x: x["createdAt"], reverse=True)
    return {"items": items, "mode": mode_selector.current_mode()}
