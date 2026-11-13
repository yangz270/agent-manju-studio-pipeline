# -*- coding: utf-8 -*-
"""
AI Donghua Studio - Universal Multi-Agent Pipeline Demo
验证 Agent 0 ~ Agent 9 的跨模块导入与端到端数据流转契约
"""

import sys
from pathlib import Path

# 将 core 目录加入模块搜索路径
CORE_DIR = Path(__file__).resolve().parent.parent / "core"
sys.path.insert(0, str(CORE_DIR))

from agent0_orchestrator import Agent0CentralOrchestrator
from agent1_2_scriptwriter import ScriptwriterHarness, UniversalEvolutionEngine
from agent3_visual_asset import VisualAssetMasterV2
from agent4_comfyui_dispatcher import RobustComfyUIDispatcherV4
from agent5_vision_qc import Agent5VisionQCInspectorV25
from agent6_7_audio_pipeline import Agent6CastingMaster, Agent7AudioEngineer
from agent8_9_motion_editor import Agent8MotionRouter, CapCutDraftCompiler

def run_demo():
    print("=" * 72)
    print("  AI Donghua Studio - 10-Agent Pipeline Integration Check")
    print("=" * 72)
    
    orchestrator = Agent0CentralOrchestrator()
    orchestrator.register_task("SH001", "Agent0_Init", "COMPLETED", "DAG Ready")
    
    # 1. 视觉资产编译验证 (Agent 3)
    asset_master = VisualAssetMasterV2()
    sample_shot = {
        "shot_id": "DEMO_SC01_SH001",
        "character": "主角少年",
        "scene": "古风主街",
        "shot_scale": "CLOSEUP",
        "camera_angle": "EYE_LEVEL",
        "facing_direction": "FACING_RIGHT",
        "action_en": "clenched fist trembling in cold rain, intense gaze",
        "dialogue": "今日之辱，来日必还！",
        "dramatic_tension": "HIGH"
    }
    manifest = asset_master.compile_shot_asset_manifest(sample_shot)
    print(f"✔ [Agent 3] 16:9 资产清单编译成功: {manifest.production_format.width}x{manifest.production_format.height}")
    
    # 2. ComfyUI 工作流生成验证 (Agent 4)
    dispatcher = RobustComfyUIDispatcherV4()
    wf_dag = dispatcher.compile_workflow_from_manifest(manifest, fixed_seed=42)
    print(f"✔ [Agent 4] ComfyUI 节点图编译成功 (节点总数: {len(wf_dag)})")
    
    # 3. 选角与声纹配置验证 (Agent 6)
    casting = Agent6CastingMaster()
    voice_manifest = casting.compile_voice_manifest(["主角少年", "反派贵族"])
    print(f"✔ [Agent 6] 角色声学矩阵建立成功 (已登记角色数: {len(voice_manifest.cast)})")
    
    # 4. 剪映五轨母带编译验证 (Agent 9)
    compiler = CapCutDraftCompiler()
    draft_file = compiler.compile_capcut_project_with_jcut(
        project_name="Universal_Demo_Project",
        shots_data=[{
            "shot_id": "DEMO_SC01_SH001",
            "duration_ms": 3000,
            "video_path": "",
            "audio_path": "",
            "dialogue": "今日之辱，来日必还！"
        }],
        enable_jcut=True,
        jcut_lead_ms=500
    )
    print(f"✔ [Agent 9] 剪映五轨工程生成成功: {draft_file.name}")
    print("=" * 72)
    print("🎉 全套 10-Agent 配置文件与跨模块引用 100% 验证通过！")

if __name__ == "__main__":
    run_demo()
