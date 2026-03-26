from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import json
import uuid
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = DATA_DIR / "reports"
TASK_FILE = DATA_DIR / "tasks.json"
REPORT_FILE = DATA_DIR / "reports.json"

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

app = FastAPI(title="AI Industry Report System", version="0.2.0")

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


def build_report_markdown(topic: str, time_range: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f'''# {topic}行业动态分析报告

## 1. 报告概览
- 主题：{topic}
- 时间范围：{time_range}
- 生成时间：{now}

## 2. 核心结论
1. 当前 {topic} 相关动态呈现持续活跃趋势。
2. 公开信息中可重点关注政策、市场、竞品、风险四类变化。
3. 建议将该主题纳入持续周报监控范围。

## 3. 重点动态
### 3.1 政策动态
- 已完成 MVP 数据流转和报告输出链路搭建。

### 3.2 市场动态
- 已完成任务创建、状态跟踪、报告归档主链路。

### 3.3 竞品动态
- 已预留 DeerFlow / 外部搜索 / RSS 接入位。

### 3.4 风险提示
- 当前版本仍以 MVP 为主，数据源暂未切换为真实抓取。

## 4. 趋势判断
- 从系统能力看，已具备创建任务、生成报告、查询报告的闭环。
- 下一阶段重点是接真实数据源与 DeerFlow 执行链。

## 5. 建议动作
1. 接入真实搜索或 RSS 数据源。
2. 接入 DeerFlow 作为分析编排引擎。
3. 增加 PDF 导出与前端报告页面。
4. 增加定时周报能力。
'''


def generate_report(task_id: str, topic: str, time_range: str):
    try:
        tasks[task_id]["status"] = "running"
        save_json(TASK_FILE, tasks)
        time.sleep(2)
        report_id = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
        markdown = build_report_markdown(topic, time_range)
        report_path = REPORT_DIR / f"{report_id}.md"
        report_path.write_text(markdown, encoding="utf-8")
        reports[report_id] = {
            "reportId": report_id,
            "taskId": task_id,
            "title": f"{topic}行业动态分析报告",
            "topic": topic,
            "timeRange": time_range,
            "summary": f"这是关于“{topic}”的自动生成行业动态分析报告。",
            "markdownPath": str(report_path),
            "markdownContent": markdown,
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
    return {"msg": "AI Industry Report System Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/task/create")
def create_task(req: CreateTaskRequest, background_tasks: BackgroundTasks):
    task_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    tasks[task_id] = {
        "taskId": task_id,
        "topic": req.topic,
        "timeRange": req.timeRange,
        "status": "pending",
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_json(TASK_FILE, tasks)
    background_tasks.add_task(generate_report, task_id, req.topic, req.timeRange)
    return {"taskId": task_id, "status": "pending"}


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
        return {"taskId": task_id, "status": task.get("status"), "report": None}
    return reports.get(report_id)


@app.get("/api/reports")
def list_reports():
    items: List[dict] = list(reports.values())
    items.sort(key=lambda x: x["createdAt"], reverse=True)
    return {"items": items}
