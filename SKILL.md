---
name: ai-donghua-pipeline-strict
description: 工业级 16:9 AI 漫剧 10-Agent 强制执行契约。任何本地 AI 助手（WorkBuddy 等）在本仓库工作时必须严格遵守此契约，严禁私自改写简化脚本或跳过质检与对口型环节。
---

# AI 漫剧管线强制执行契约 (Strict Execution Contract)

## 五大不可逾越的红线

1. **严禁绕开 `core/` 重写简化脚本**：
   - 必须使用 `core/agent0_orchestrator.py` ~ `core/agent8_9_motion_editor.py` 与 `workflows/` 中的标准管线。
   - 禁止在缺乏授权的情况下临时编造无逻辑关联的测试台词（如“谁捞的鱼”），剧本与分镜必须经由 Agent 1 + Agent 2 严格产出。
2. **参考图前置审校铁律**：
   - 使用 `IPAdapter` 锁脸前，**必须先人工或由 Agent 5 校验参考图本身**（古装汉服、正确性别、年龄、夜戏色调）。参考图错了，后续所有镜头必错。
3. **对白镜头强制对口型（禁止纯 I2V 硬贴音轨）**：
   - 凡是人物正脸开口说话的镜头，**严禁仅用无声图生视频（Hailuo/Wan）再硬贴 TTS 音轨**！
   - 必须路由至 `workflows/WF_09_LipSync_AudioDriven.json`（音频驱动嘴型与眨眼）或 `WF_04_MiniMax_H3_TwoStage_AudioVideo.json`（音画同出）。
4. **手部畸变强制闭环修复（FaceDetailer 不修手）**：
   - `FaceDetailer`（`face_yolov8m.pt`）仅修复面部，对扭曲手指完全无效。
   - 所有出图必须经 Agent 5 检查手部与解剖结构；发现手部崩坏必须走 `WF_06` / SAM (`sam_vit_b.pth`) + `VAEEncodeForInpaint` (Denoise 1.0) 局部重绘。
5. **8GB 显存与云端控费铁律**：
   - 本地 ComfyUI 0.44 严禁传 `--medvram`（不存在），必须用 `--reserve-vram 0.8`；任何重任务前必须先 `POST /free` 卸载显存，防止 16GB 物理内存 OOM Kill。
   - 权重下载必须用 `zipfile.testzip()` 校验 `data.pkl`，严禁只看文件字节数。
   - 调用 Hailuo-02 等付费视频 API 前，必须先调用 `HailuoCostGuard.estimate_batch_cost()` 报价确认，严禁未报价盲目全量提交导致余额耗尽。
   - 剪映草稿必须通过 `pyJianYingDraft` 补齐完整目录骨架（`Resources/`、`matting/`、`Timelines/`、`draft_settings`），并同步输出 `Premiere Pro XML` 作为保底工程。
