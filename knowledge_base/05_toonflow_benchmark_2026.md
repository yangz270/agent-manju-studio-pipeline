# 模块 05：Toonflow-app 及 2026 开源 AI 漫剧工业全景深度对标手册

> 对标基准：
> 1. `HBAI-Ltd/Toonflow-app` (20.2k Stars, MIT) — `packages/nodeScaffold/readme.md` 源码级核验
> 2. `dramaclaw/dramaclaw` (6.9k Stars) — 虾导/虾画/虾集 + 3D 高斯片场 + 3D 预演台
> 3. `TWO-ICE/awesome-manyu` (2026 开源漫剧 97 项目全景图：OpenMontage 75k★, huobao-drama 16.9k★, waoowaoo 14.7k★, ViMax 12.8k★, ArcReel 6k★)

---

## 一、 Toonflow-app 源码级底层机制（`packages/nodeScaffold` 实测拆解）

通过直接拆解 `HBAI-Ltd/Toonflow-app/blob/master/packages/nodeScaffold/readme.md` 与 `package.json`，其工业级底座由以下 7 大核心工程机制构成：

1. **宿主共享与 UMD 插件架构 (`@toonflow/nodes-scaffold` + `@toonflow/node-shared`)**：
   - 每个节点编译为独立的 `build/nodes/<Node>.umd.js` 并热同步至 `data/nodes/`；
   - 宿主通过 `window.toonflowNodeHost` 共享 `Vue`、`VueFlow`、`Element Plus`、**`Three.js (v0.184.0)`** 以及 **`Pi Agent SDK` (`runAgentLoop`)**；
   - 文本编辑器共享 `window.toonflowTiptapHost` (`@tiptap/core@3.31.3`)。
2. **共享组件级能力复用 (`@toonflow/node-image` & `@toonflow/node-shared`)**：
   - **`useNodeReferences("in")`**: 自动聚合上游连线输入的文本、图片、视频，在 Prompt 中按 `{{ref 1}}`、`{{ref 2}}` 强绑定引用（彻底解决多角色/多道具乱序问题）；
   - **`@toonflow/node-image` 四大内置算子**：图片编辑、**宫格切分 (Grid Slicing)**、**局部重绘 (Inpainting)**、**重打光 (Relighting)**；
   - **`useNodeFfmpeg()` & `useNodeAsr()`**：节点内置链式 FFmpeg 合成 (`/api/ffmpeg/execute`) 与 100MB 内原速音轨语音转写 (`@toonflow/asr`)。
3. **断点续传与防丢持久化 (`useNodeGeneration` + `resumeMedia`)**：
   - 发起生图/生视频前，先将 `taskId`、`nodeId`、`canvasPath` 写入 `node.data.mediaTask` 并落盘保存画布；
   - 页面刷新、崩溃或断线重连后，自动调用 `ai.resumeMedia(directory, taskId)` 恢复轮询，绝不浪费已扣费的云端任务。
4. **全能视频生成输入协议 (`ai.generateVideo`)**：
   - 原生支持同时传入：`images`（多参考图）、`videos`（参考视频）、`audios`（驱动/参考音频）、`firstFrame`（首帧）、`lastFrame`（尾帧）、`duration`、`resolution`、`ratio`、`generateAudio`、`mode`。
5. **Agent 画布操控协议 (`packages/tools/canvas` + `nodeTools.register`)**：
   - 每个节点用 Zod 注册严格 Schema 的操作函数（如 `node:setText`）；
   - 外部或内置 Agent 通过 `findCanvasNodes`、`getCanvasNodes`（带 64KiB 分页上限防撑爆上下文）、`getNodeTools`、`addNode`、`connectNodes` 自动在画布上铺设节点并执行。
6. **Three.js 3D 导演台与 360°/3D 高斯片场（Toonflow + DramaClaw 核心标配）**：
   - 在浏览器内用 `Three.js 0.184.0` 加载场景白模或 360° 全景/3D 高斯片场，放置 5 种体型人偶并沿轨迹播放行走动画，多机位切换焦距并录制节目轨，直接作为生图/生视频的硬几何参考。
7. **2026 商业合规与开源口型红线（`awesome-manyu` 警示）**：
   - **重大合规隐患**：`Wav2Lip` 在开源界明确标注为 **`❌ 仅研究用途，禁商用`** 且分辨率固定 `96×96`；商业漫剧口型同步已全面转向 **字节开源 `LatentSync` (`Apache-2.0` 可商用，SD 架构高清口型)**、**B 站 `Index-anisora` (`Apache-2.0` 二次元漫剧视频)** 与 **`GPT-SoVITS` (`MIT` 音色克隆)**。

---

## 二、 20 项全维度逐项对标：行业顶配 (Toonflow / DramaClaw) vs 本项目

| 序号 | 细分模块与能力项 | 行业成熟生产线 (Toonflow / DramaClaw / ArcReel) | 本项目 (AI-Donghua-Studio) | 差距等级与根因诊断 |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **原著结构化导入** | 支持 `.docx` / `.txt` / `Fountain` 剧本格式直接导入，自动清洗乱码与分章 | 仅支持纯文本字符串或手写字典传入 | **P1 缺失**：缺 `.docx`/`Fountain` 解析与分章器 |
| **02** | **跨集长程状态记忆** | “虾塘”资产库：跨集维护角色服装变体（受伤/换装）、持有道具、好感度与多集故事弧线 | 单集无状态运行，第 2 集不知道第 1 集末尾角色衣服破损或拿了什么道具 | **P0 缺失**：缺 `EpisodeContinuityLedger` 跨集场记账本 |
| **03** | **剧本三种改编模式** | 支持“自适应 / 忠实原文 / 分阶段”三模式 + 去 AI 味改稿 (`sepia` / `human-writing`) | 只有单一“强冲突浓缩”模式，台词偶有 AI 味 | **P1 待强化**：需补“忠实原文 vs 强冲突”模式切换与去 AI 味规则 |
| **04** | **模型感知时长切分** | 生成分镜前先确认目标模型（Seedance 2.0/2.5 或 H3），自动按 5s / 15s / 30s 硬上限切分段落 | 固定按单句台词时长 + 350ms 留白计算，未绑定下游视频模型最大帧数约束 | **P1 缺失**：需在 Agent 1/8 加入模型时长上限对齐 |
| **05** | **四大资产库完备度** | **角色 + 场景 + 道具 + 声线** 四大平级资产库（含角色三视图、场景多机位、武器/宠物独立白底卡） | 仅有 `CharacterBible` + `SceneBible` + `VoiceCast`，**完全缺失 `PropBible`（武器/法宝/灵宠/植物资产库）** | **P0 致命缺失**：导致画武器/宠物无固定参考图可锁 |
| **06** | **多参考图 `{{ref N}}` 绑定** | `useNodeReferences` 将人、景、物参考图按 `{{ref 1}}`、`{{ref 2}}` 强绑定到提示词槽位 | 仅支持单张角色参考图挂 `IPAdapter`，或靠文本写 `from left to right` | **P0 致命缺失**：多人同框或人+武器交互时无法多图锁定 |
| **07** | **3D 导演台 / 空间预演** | 内置 `Three.js` 3D 白模片场 + 5 种体型人偶走位 + 多机位焦距录制，输出精准空间构图 | 纯靠自然语言描述机位（`LOW_ANGLE`、`CLOSEUP`），复杂走位常出错 | **P0 核心差距**：需用本地 ControlNet Depth/OpenPose 预设库平替 |
| **08** | **场景跨镜头 360° 一致性** | 将单张场景图转为 **360° 全景或 3D 高斯片场**，不同镜头旋转摄像机取景，背景建筑 100% 物理一致 | 每个镜头重新文生图画背景，同一条巷子每一镜的门窗、灯笼位置都在变 | **P0 核心痛点**：正是你说的“几个镜头像强行凑在一起的图”的根源！ |
| **09** | **镜头间首尾帧衔接 (`firstFrame`/`lastFrame`)** | 上一镜的尾帧（或同场景切机位帧）直接连入下一镜的 `firstFrame`，支持首尾帧插值过渡 | 每镜独立生成单张静帧，镜头与镜头之间无视觉锚点承接，也没有 `lastFrame` 约束 | **P0 核心痛点**：导致你指出的“没有首尾帧、不知道要表达什么” |
| **10** | **内置重打光 (Relighting)** | `@toonflow/node-image` 内置重打光算子，把白底角色/道具融合进夜雨/火光环境色温 | 仅靠提示词写 `6500K cold + 3200K rim`，缺乏图像级 Relight 融合节点 | **P1 缺失**：需在合成流加入 IC-Light / 颜色匹配融合 |
| **11** | **风格墙与提取器** | 内置 45 种漫剧风格预设墙 + “上传 1 张参考图自动反推提取全项目视觉风格参数” | 仅内置 4 种硬编码风格字典，且 T14 单图反推未接入自动化代码 | **P1 待补**：需把 T14 反推风格接入 `Agent 3` |
| **12** | **手部与面部精修闭环** | 无内置本地自动修手修脸（全靠云端大模型抽卡） | 已具备 `1.5x` 潜空间放大 + `FaceDetailer` + `HandDetailer` (`hand_yolov8s.pt`) + `SAM` 局部重绘 | **我方领先** |
| **13** | **视觉质量自动审计 (QC)** | 无自动 QC，靠肉眼在画布看 | `Agent 5` 像素方差雷达 + 拉普拉斯纹理检测 + 四宫格单格切分重修 | **我方独有优势** |
| **14** | **口型同步质量与商用合规** | 依赖 Seedance 2.5 / H3 云端原生音画同出，或调用字节 **`LatentSync` (Apache-2.0)** | 本地用 **`Wav2Lip`（❌ 禁商用许可 + 96×96 嘴部发糊 + 0.43% 幅度）** | **P0 重大隐患**：需升级为“裁脸放大 + LivePortrait 微动”或切换 `LatentSync` |
| **15** | **二次元/国漫专用开源视频** | 收录 B 站开源 **`Index-anisora` (Apache-2.0)** 专攻二次元/漫剧动态，及 `Wan2.2` / `LTX-Video` | 本地仅有静态视差推镜，云端仅调通用写实向 `Hailuo-02` | **P1 认知补齐**：动漫视频应认识 `Index-anisora` 与高性价比 H3 |
| **16** | **异步任务持久化 (`resumeMedia`)** | 提交云端前先将 `taskId` 落盘，进程崩溃或断网重开后自动续查，绝不丢单重复扣费 | `v2` 在内存中轮询，脚本一旦中断 `task_id` 丢失，重跑又重新扣一次钱 | **P0 必补**：必须加 `media_tasks_journal.json` 断点续传账本！ |
| **17** | **音色克隆与语音识别校准** | 本地 `GPT-SoVITS` 零成本音色克隆 + `Whisper` / `@toonflow/asr` 逐字时间戳反推对齐字幕 | 云端 MiniMax `speech-02-hd` + 按句子总时长粗略铺字幕（无逐字/逐词 ASR 时间戳校准） | **P1 待强化**：长句内分句字幕需 ASR 校准 |
| **18** | **物理拟音与广播级母带** | 无（仅简单拼接或单条 BGM） | 10 类分层环境/动作拟音 + 侧链 Ducking + `-16.5 LUFS / -1.2 dBTP` 广播级母带 | **我方独有护城河** |
| **19** | **剪映 / PR 工程自动化交付** | 多数仅导出 MP4 或散装素材（仅 `ArcReel` 支持剪映草稿） | 同时输出 **剪映完整骨架 (`pyJianYingDraft`)** + **Premiere Pro FCPXML v4 (含 500ms J-Cut)** | **我方独有护城河** |
| **20** | **交互形态与分支互动剧** | `@vue-flow/core` 无限画布 + **分支互动剧编排与独立 HTML 播放器导出** + 原生 MCP Server | ComfyUI 前端 UI 工作流 + CLI 脚本，无独立选片看板与 MCP Server 封装 | **P2 体验差距**：可输出轻量级 HTML 分镜审片看板 |
