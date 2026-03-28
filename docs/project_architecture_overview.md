# 项目整体架构图

当前项目推荐以 V3 作为主线，也就是 `app/backend/mvp_main_v3.py` + `live_report_service_v2.py` 这套结构。

## 1. 总体架构

```mermaid
flowchart LR
    user["用户 / 研究员"]

    subgraph frontend["Frontend 静态页面"]
        index["index.html<br/>任务创建"]
        report["report.html<br/>报告查看"]
        runtime["runtime-status.html<br/>运行状态"]
    end

    subgraph backend["FastAPI Backend V3"]
        api["mvp_main_v3.py<br/>任务 API / 健康检查 / 报告查询"]
        selector["runtime_mode_selector.py<br/>模式选择"]
        status["deerflow_status.py<br/>运行探测"]
        service["live_report_service_v2.py<br/>统一报告生成服务"]
        mapper["deerflow_result_mapper.py<br/>结果映射"]
        settings["settings.py<br/>环境变量配置"]
        store["data/tasks_v3.json<br/>data/reports_v3.json<br/>data/reports/*.md"]
    end

    subgraph local["Local Chain"]
        tavily["tavily_connector.py<br/>实时搜索"]
        pipeline["analysis_pipeline.py<br/>信号分析"]
        deepseek["deepseek_connector.py<br/>LLM 总结"]
        renderer["markdown_renderer.py<br/>Markdown -> HTML"]
    end

    subgraph deerflow["DeerFlow Chain"]
        probe["health probe<br/>连通性检查"]
        client["deerflow_runtime_client.py<br/>技能调用 / 异步轮询"]
        skill["DeerFlow Runtime<br/>Skill 执行"]
    end

    subgraph runtime_env["部署与运行"]
        compose["docker-compose.v2.yml<br/>当前默认启动入口"]
        env[".env / 环境变量<br/>TAVILY / DEEPSEEK / DEERFLOW"]
    end

    user --> index
    user --> report
    user --> runtime

    index --> api
    report --> api
    runtime --> api

    api --> selector
    api --> status
    api --> service
    api --> store

    selector --> settings
    status --> probe
    probe --> client

    service --> selector
    service --> settings
    service --> tavily
    tavily --> pipeline
    pipeline --> deepseek
    deepseek --> renderer

    service --> client
    client --> skill
    skill --> mapper
    mapper --> api

    compose --> frontend
    compose --> backend
    env --> settings
    env --> client
```

## 2. 一次任务的执行流

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端页面
    participant A as mvp_main_v3.py
    participant S as LiveReportServiceV2
    participant M as RuntimeModeSelector
    participant D as DeerFlowRuntimeClient
    participant L as Local Chain
    participant R as 报告存储

    U->>F: 输入主题和时间范围
    F->>A: POST /api/task/create
    A->>M: 判断当前模式
    A->>A: 创建 task 记录
    A-->>F: 返回 taskId

    A->>S: 后台生成报告
    S->>M: 是否优先 DeerFlow

    alt DeerFlow 可用且优先
        S->>D: run_skill(skill, payload)
        D->>D: 同步调用或异步轮询
        D-->>S: 返回 DeerFlow 结果
        S-->>A: deerflow 模式结果
    else 本地链路
        S->>L: Tavily -> AnalysisPipeline -> DeepSeek -> HTML
        L-->>S: 本地报告结果
        S-->>A: local 模式结果
    end

    A->>R: 写入 tasks / reports / markdown 文件
    F->>A: 轮询 task / report
    A-->>F: 返回状态、模式、报告内容、诊断信息
```

## 3. 关键职责划分

- 我们自己的应用负责：任务记录、报告存储、状态展示、前端页面、调度入口。
- DeerFlow 负责：执行编排、技能运行、多步任务处理。
- 本地链路负责：在 DeerFlow 不可用或未配置时，继续完成报告生成。

## 4. 关键入口文件

- 后端主入口：`app/backend/mvp_main_v3.py`
- 统一服务层：`app/backend/live_report_service_v2.py`
- DeerFlow 客户端：`app/backend/deerflow_runtime_client.py`
- DeerFlow 结果映射：`app/backend/deerflow_result_mapper.py`
- 模式选择：`app/backend/runtime_mode_selector.py`
- 运行状态探测：`app/backend/deerflow_status.py`
- 前端首页：`frontend/index.html`
- 运行方式：`docker-compose.v2.yml`

## 5. 当前你可以这样理解这个项目

- 这不是一个单纯的“报告脚本”，而是一个有任务管理和运行模式切换能力的 AI 产品雏形。
- V3 后端已经把两条执行路径统一到了一个接口层里：`local chain` 和 `deerflow chain`。
- 前端目前还是静态页，但已经能覆盖任务创建、状态查看、报告查看这三个核心场景。
- 后续真正变复杂的地方，主要会在 DeerFlow 真实运行时的接入、结果结构标准化、以及任务调度能力增强。
