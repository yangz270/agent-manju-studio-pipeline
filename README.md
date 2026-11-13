# AI-Donghua-Studio-Pipeline (工业级 AI 漫剧 / 3D 动画全流程多智能体生产管线)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![ComfyUI Ready](https://img.shields.io/badge/ComfyUI-2026%20Decoupled-orange.svg)](https://github.com/comfyanonymous/ComfyUI)
[![Hardware: 8GB VRAM](https://img.shields.io/badge/Hardware-RTX%205060%208GB%20Optimized-red.svg)]()

> 面向商业级 16:9 横屏 AI 漫剧与 3D 国漫短剧的端到端自动化生产框架。  
> 针对 **8GB 显存级消费级显卡（RTX 4060 / 5060 Laptop 等）** 深度调优，从原著脱水、Character Bible 资产锁定、ComfyUI 异步调度、四维审美质检，到广播级情感配音、FlashVSR 1.1 1080P 超分，以及剪映 / Premiere Pro XML 五轨工程自动化总装。

---

## ⚠️ 使用前必读：先配置 API Key

本管线会调用 **DeepSeek / MiniMax / OpenAI 兼容网关** 三家商业 API，**没有配置密钥无法运行**。
脚本内置了硬闸口：缺少必需密钥时会直接拒绝启动，不会跑到一半才报 401。

```bash
# 1. 生成配置文件
cp .env.example .env

# 2. 编辑 .env，填入你自己的密钥（标 [必需] 的三项缺一不可）
#    DEEPSEEK_API_KEY  —— Agent 1/2 编剧脱水与黄金 Hook 审查
#    MINIMAX_API_KEY   —— Agent 6/7 拟真配音与海螺视频
#    OPENAI_API_KEY    —— Agent 5 四维审美质检（可用 302.AI 等网关）

# 3. 启动前自检（缺失会打印具体申请入口）
python scripts/preflight_check.py
```

| 变量 | 是否必需 | 用途 | 申请入口 |
| :--- | :--- | :--- | :--- |
| `DEEPSEEK_API_KEY` | **必需** | 剧本脱水、0–3s 黄金 Hook | <https://platform.deepseek.com/api_keys> |
| `MINIMAX_API_KEY` | **必需** | 情感配音、海螺视频 | <https://platform.minimaxi.com/user-center/basic-information/interface-key> |
| `OPENAI_API_KEY` | **必需** | GPT-4o 审美质检 | 302.AI 或任意 OpenAI 兼容网关 |
| `DASHSCOPE_API_KEY` | 可选 | Qwen-VL 视觉审图备份 | 阿里云百炼 |
| `MOONSHOT_API_KEY` | 可选 | Kimi 长篇原著扫描 | Moonshot 开放平台 |

> 🔒 仓库只提供 `.env.example` 模板，真实的 `.env` 已被 `.gitignore` 忽略。
> 💰 `AUTO_APPROVE_ALL_KEYS` 默认 `false`，每次调用付费接口前都会弹出人工确认，不会暗箱扣费。


---

## 架构拓扑 (10-Agent Multi-Agent Topology)

系统由 **Agent 0** 担任中央调度大脑，严格通过 SQLite 状态机与 HITL（人机协同授权闸口）编排四大工业大组共 10 个专业岗位：

```text
                                  【Agent 0: 总控编排与模型路由调度器】
                        (SQLite 任务状态机 + 动态三层模型路由器 + 预算熔断器 + 故障降级梯队)
                                               │
     ┌───────────────────────────┬─────────────┴─────────────┬───────────────────────────┐
     ▼                           ▼                           ▼                           ▼
【第一组：剧作核心】         【第二组：视觉工程】         【第三组：角色声音】         【第四组：动效与剪辑总装】
 • Agent 1: 冲突编剧(Proposer)• Agent 3: 视觉资产总监(16:9) • Agent 6: 选角大师(Casting) • Agent 8: 动效分发路由(FlashVSR)
 • Agent 2: 黄金Hook审查(QC) • Agent 4: 工作流编译与调度  • Agent 7: 配音工程(MiniMax) • Agent 9: 剪映/PR五轨母带总装
                              • Agent 5: 四维美学质检(VLM)
```

### 10 大岗位职责矩阵

| 岗位序号 | 岗位名称 | 核心职责 | 默认驱动模型 | 显存 / 算力策略 |
| :--- | :--- | :--- | :--- | :--- |
| **Agent 0** | 总控编排与 HITL 闸口 | SQLite 任务状态机、外部 API 扣费授权、故障梯队降级 | 本地 Python 核心 | 零额外开销 |
| **Agent 1** | 冲突挖掘编剧 | 0~3s 黄金 Hook 锁定、台词脱水（<=15 字）、动作纯物理外化 | **DeepSeek-V3** | API 直连 |
| **Agent 2** | 黄金 Hook 质检员 | 一票否决权，审查台词字数与隐形心理独白 | **GPT-4o / Claude 3.5** | API 直连 |
| **Agent 3** | 视觉资产总监 (16:9) | Character Bible（白底立绘+裁小脸四宫格）、LOD 景别过滤、6500K/3200K 色温锁 | **Krea2 / Qwen-Image 2.1** | 本地 ComfyUI |
| **Agent 4** | 工作流编译与调度 | 2026 三件套解耦加载、CFG=1 铁律、路线 A/B 双内补、显存释放 | **ComfyUI HTTP/WS API** | 8G `--reserve-vram 0.8` |
| **Agent 5** | 四维美学质检员 | Scale AI 4D 评审标准、物理坏帧雷达（黑白帧筛查）、自动下发自愈补丁 | **GPT-4o Vision / 本地雷达** | 混合双模 |
| **Agent 6** | 选角大师 (Casting) | 人物声学小传画像、声纹母本锁定 (`Voice_Master.wav`)、男女声频段避让 | **规则引擎 / LLM** | 本地算力 |
| **Agent 7** | 拟真配音专家 | 呼吸停顿注入 (`<break/>`)、EBU R128 (-16 LUFS) 响度规范、物理拟音建模 | **MiniMax T2A / FFmpeg** | API + 本地声学 |
| **Agent 8** | 动效路由与运镜师 | 三级动效智能分流（LivePortrait / 16:9 视差推拉 / 视频API）、FlashVSR 1.1 超分 | **LivePortrait / FlashVSR** | 8G 极限调优 |
| **Agent 9** | 剪映/PR 母带总装 | 五轨合流（1080P切片、J-Cut 500ms 对白、Foley拟音、Ducking音乐、白字黑边字幕） | **本地 Python 编译器** | 本地沙盒零开销 |

---

## 快速上手 (Quick Start)

### 1. 克隆仓库与安装依赖
```bash
git clone https://github.com/yangz270/agent-manju-studio-pipeline.git
cd agent-manju-studio-pipeline
pip install -r requirements.txt
```

### 2. 配置商业 API 凭据（**必需，否则无法运行**）
复制 `.env.example` 为 `.env`，填入你自己的商业 API Key，详见上文「使用前必读」：
```bash
cp .env.example .env
python scripts/preflight_check.py   # 未配置齐全会直接拒绝启动
```

### 3. 环境与显存体检
```bash
python scripts/health_check.py
```

### 4. 运行端到端全链路演示
```bash
python examples/run_pipeline_demo.py
```
Windows 用户也可以直接双击 `scripts/start.bat` 一键运行（会先自动执行 API Key 前置校验）！

---

## 许可证 (License)

本项目采用 [MIT License](LICENSE) 开源协议。
