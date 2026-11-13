# -*- coding: utf-8 -*-
"""
core/agent0_orchestrator.py
Agent 0: 中央总控编排与 SQLite DAG 任务状态机 (Central Orchestrator & HITL Gate)
负责管理 Agent 1 ~ Agent 9 的全生命周期状态流转、预算熔断、故障降级与人机协同审批。
"""

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class BudgetExceededError(RuntimeError):
    """单集预算超限熔断异常"""
    pass


class APIBudgetCircuitBreaker:
    """
    [全 API 统一预算熔断器]
    防止任何单集任务因盲目全量提交 Hailuo-02 1080P、302.ai 云端视频代理或 VLM 死循环重试而烧光余额。
    """
    DEFAULT_UNIT_COSTS_RMB = {
        "hailuo-02-1080p": 3.50,
        "hailuo-2.3-fast-1080p": 2.31,
        "hailuo-02-768p": 2.00,
        "302ai-cloud-render": 0.50,
        "gpt-4o-vision": 0.06,
        "qwen-vl-plus": 0.02,
        "deepseek-chat": 0.01,
        "moonshot-long": 0.30,
        "minimax-speech-02-hd": 0.02,
    }

    def __init__(self, max_episode_budget_rmb: float = 6.0, max_retries_per_shot: int = 2):
        self.max_episode_budget_rmb = max_episode_budget_rmb
        self.max_retries_per_shot = max_retries_per_shot
        self.spent_rmb = 0.0
        self.call_ledger: List[Dict[str, Any]] = []

    def check_and_record(self, api_name: str, count: int = 1, custom_unit_cost: Optional[float] = None) -> float:
        unit = custom_unit_cost if custom_unit_cost is not None else self.DEFAULT_UNIT_COSTS_RMB.get(api_name, 0.05)
        cost = round(unit * count, 4)
        if self.spent_rmb + cost > self.max_episode_budget_rmb:
            raise BudgetExceededError(
                f"[预算熔断拦截] 本次调用 {api_name} (预计 ¥{cost:.2f}) 将使单集累计花费达到 "
                f"¥{self.spent_rmb + cost:.2f}，超出单集上限 ¥{self.max_episode_budget_rmb:.2f}！已强制中止扣费。"
            )
        self.spent_rmb = round(self.spent_rmb + cost, 4)
        self.call_ledger.append({"api": api_name, "count": count, "cost_rmb": cost})
        return self.spent_rmb


class TaskNodeRecord(BaseModel):
    task_id: str
    shot_id: str
    agent_stage: str
    status: str = Field(default="PENDING", description="PENDING | RUNNING | COMPLETED | FAILED | BLOCKED_HITL")
    output_artifact: Optional[str] = None
    updated_at: float = Field(default_factory=time.time)

class Agent0CentralOrchestrator:
    """
    Agent 0: 工业级 AI 漫剧管线总控状态机与路由器
    """
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(__file__).resolve().parent.parent
        self.db_path = self.workspace_root / "pipeline_state.db"
        self._init_sqlite_dag()

    def _init_sqlite_dag(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dag_tasks (
                task_id TEXT PRIMARY KEY,
                shot_id TEXT,
                agent_stage TEXT,
                status TEXT,
                output_artifact TEXT,
                updated_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def register_task(self, shot_id: str, agent_stage: str, status: str = "PENDING", artifact: str = "") -> str:
        task_id = f"{shot_id}_{agent_stage}"
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO dag_tasks (task_id, shot_id, agent_stage, status, output_artifact, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, shot_id, agent_stage, status, artifact, time.time()))
        conn.commit()
        conn.close()
        return task_id

    def get_pipeline_summary(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT task_id, shot_id, agent_stage, status, output_artifact FROM dag_tasks ORDER BY updated_at ASC")
        rows = cursor.fetchall()
        conn.close()
        return [
            {"task_id": r[0], "shot_id": r[1], "agent_stage": r[2], "status": r[3], "output_artifact": r[4]}
            for r in rows
        ]


class MediaTaskJournal:
    """
    [对标 Toonflow useNodeGeneration + resumeMedia]
    异步媒体任务持久化断点续传账本：
    提交云端生图/生视频前先把 task_id 落盘，脚本重启或断网恢复后优先查已有 task_id，绝不重复提交扣第 2 次费！
    """
    def __init__(self, journal_path: Optional[Path] = None):
        self.journal_path = journal_path or (Path(__file__).resolve().parent.parent / "media_tasks_journal.json")
        self._records: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.journal_path.exists():
            try:
                return json.loads(self.journal_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self):
        self.journal_path.write_text(json.dumps(self._records, ensure_ascii=False, indent=2), encoding="utf-8")

    def record_submission(self, shot_id: str, provider: str, task_id: str, cost_rmb: float, payload_hash: str = ""):
        self._records[shot_id] = {
            "shot_id": shot_id,
            "provider": provider,
            "task_id": task_id,
            "status": "SUBMITTED",
            "cost_rmb": cost_rmb,
            "payload_hash": payload_hash,
            "output_path": None,
            "updated_at": time.time(),
        }
        self._save()

    def get_resumable_task(self, shot_id: str) -> Optional[Dict[str, Any]]:
        rec = self._records.get(shot_id)
        if rec and rec.get("status") in ("SUBMITTED", "COMPLETED"):
            return rec
        return None

    def mark_completed(self, shot_id: str, output_path: str):
        if shot_id in self._records:
            self._records[shot_id]["status"] = "COMPLETED"
            self._records[shot_id]["output_path"] = output_path
            self._records[shot_id]["updated_at"] = time.time()
            self._save()


def generate_html_review_board(
    episode_title: str,
    shots: List[Dict[str, Any]],
    assets: Dict[str, str],
    output_html_path: Optional[Path] = None,
    budget_spent_rmb: float = 0.0,
) -> Path:
    """
    [对标 Toonflow / DramaClaw 无限画布审片台]
    生成零依赖单文件可视化 HTML 审片看板 (storyboard_review_board.html)，
    同屏展示：角色/场景/道具参考图、分镜台词、首尾帧锚点、关键帧预览、配音试听与单镜成本。
    """
    out_p = output_html_path or (Path(__file__).resolve().parent.parent / "storyboard_review_board.html")
    asset_cards = "".join(
        f"<div class='card'><div class='tag'>{k}</div><img src='{v}' alt='{k}'/><code>{v}</code></div>"
        for k, v in assets.items()
    )
    shot_rows = ""
    for s in shots:
        sid = s.get("shot_id", "SH")
        dlg = s.get("dialogue", "")
        act = s.get("action_en", s.get("visual_action", ""))
        ff = s.get("first_frame_anchor", "继承场景母图")
        lf = s.get("last_frame_anchor", "定格动作尾帧")
        img = s.get("image_path", "")
        aud = s.get("audio_path", "")
        shot_rows += (
            f"<tr><td><b>{sid}</b></td><td>{dlg}</td><td>{act}</td>"
            f"<td><small>首帧: {ff}<br/>尾帧: {lf}</small></td>"
            f"<td><img src='{img}' style='max-width:220px;border-radius:6px'/><div><code>{img}</code></div></td>"
            f"<td><audio controls src='{aud}' style='width:180px'></audio></td></tr>"
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/><title>{episode_title} - 可视化分镜与资产审片看板</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;margin:24px}}
h1,h2{{color:#f8fafc}} .meta{{background:#1e293b;padding:12px 18px;border-radius:8px;margin-bottom:20px}}
.grid{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px}}
.card{{background:#1e293b;padding:12px;border-radius:8px;width:220px}} .card img{{width:100%;border-radius:6px}}
.tag{{font-size:12px;color:#38bdf8;margin-bottom:6px;font-weight:600}}
table{{width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;overflow:hidden}}
th,td{{padding:12px;border-bottom:1px solid #334155;text-align:left;vertical-align:top;font-size:14px}}
th{{background:#0f172a;color:#94a3b8}} code{{font-size:11px;color:#94a3b8;word-break:break-all}}
</style></head><body>
<h1>{episode_title} · 审片看板</h1>
<div class="meta">已用云端预算：<b>¥{budget_spent_rmb:.2f}</b> ｜ 分镜总数：<b>{len(shots)}</b></div>
<h2>一、 角色 / 场景母图 / 道具资产锚点</h2>
<div class="grid">{asset_cards}</div>
<h2>二、 分镜脚本、首尾帧承接与视听预览</h2>
<table><thead><tr><th>镜号</th><th>台词 (<=15字)</th><th>物理动作</th><th>首尾帧承接</th><th>关键帧 (16:9)</th><th>配音试听</th></tr></thead>
<tbody>{shot_rows}</tbody></table></body></html>"""
    out_p.write_text(html, encoding="utf-8")
    return out_p
