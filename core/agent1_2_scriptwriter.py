# -*- coding: utf-8 -*-
"""
core/agent1_2_scriptwriter.py

工业级全风格 AI 漫剧管线 —— 第一棒：具备【用户主动授权审批闸口 (HITL)】与【终身自省进化】的冲突筛查与短剧编剧闭环
(Agent 1 Conflict-Sieve Proposer + Strict Key Authorization Gate + UniversalEvolutionEngine + Reviewer Loop)

核心工程铁律：
【硬性授权铁律】任何 Agent 在向外部发起真实 API 调用前，必须显式向用户说明：
  1. 调用发起方 (Agent 岗位)
  2. 调用的外部接口平台与 Base URL
  3. 使用的具体模型名称 (Model)
  4. 使用的 API Key 类型与脱敏展示 (如 your_api_key_here)
  5. 预估消耗的 Token 与任务意图
  必须经过用户交互式确认（或显式传参授权），严禁任何静默暗箱扣费！
"""

import datetime
import json
import os
import re
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError

# 自动加载当前目录下的 .env 配置文件
def load_dotenv_file(dotenv_path: Optional[Path] = None):
    candidates = [dotenv_path] if dotenv_path else [
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent / ".env",
        Path.cwd() / ".env",
    ]
    for p in candidates:
        if p and p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    cur = os.environ.get(k, "")
                    if not cur or cur.startswith("your_"):
                        os.environ[k] = v

load_dotenv_file()

# 自动兼容 Pydantic v2 与 v1 环境
try:
    from pydantic import field_validator as _validator_decorator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import validator as _validator_decorator
    PYDANTIC_V2 = False


def compat_validator(field_name: str):
    if PYDANTIC_V2:
        return _validator_decorator(field_name)
    return _validator_decorator(field_name, allow_reuse=True)


def compat_parse_json(model_cls: type[BaseModel], raw_json: str) -> BaseModel:
    if hasattr(model_cls, "model_validate_json"):
        return model_cls.model_validate_json(raw_json)
    return model_cls.parse_raw(raw_json)


def compat_dump_json(instance: BaseModel) -> str:
    if hasattr(instance, "model_dump_json"):
        return instance.model_dump_json(indent=2)
    return json.dumps(instance.dict(), ensure_ascii=False, indent=2)


def compat_json_schema(model_cls: type[BaseModel]) -> Dict[str, Any]:
    if hasattr(model_cls, "model_json_schema"):
        return model_cls.model_json_schema()
    return model_cls.schema()


# ============================================================================
# 0. 全 Agent 通用终身反思与自进化引擎 (Universal Self-Evolution Engine)
# ============================================================================

class PitfallRecord(BaseModel):
    rule_id: str = Field(description="自进化规则唯一编号，如 EVO_001")
    agent_id: str = Field(description="所属 Agent 标识")
    style_scope: str = Field(default="ALL", description="适用风格范围")
    trigger_source: str = Field(description="触发来源：Code_Guard / Reviewer_Audit / User_Feedback")
    symptom: str = Field(description="暴露出的认知偏差或错误现象")
    root_cause: str = Field(description="归因分析出的底层原因")
    auto_patch_instruction: str = Field(description="自动追加进 <agent_status> 的修正准则")
    new_forbidden_words: List[str] = Field(default_factory=list, description="自动扩展进确定性代码护栏的新违禁词")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat(timespec="seconds"))


class UniversalEvolutionEngine:
    def __init__(self, agent_id: str, memory_dir: str = "./memories"):
        self.agent_id = agent_id
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / f"{agent_id}_pitfalls.json"
        self.records: List[PitfallRecord] = self._load_records()

    def _load_records(self) -> List[PitfallRecord]:
        if not self.memory_file.exists():
            return []
        try:
            raw_list = json.loads(self.memory_file.read_text(encoding="utf-8"))
            return [compat_parse_json(PitfallRecord, json.dumps(item, ensure_ascii=False)) for item in raw_list]
        except Exception:
            return []

    def save_records(self) -> None:
        data = [json.loads(compat_dump_json(r)) for r in self.records]
        self.memory_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def reflect_and_evolve(
        self,
        trigger_source: str,
        symptom: str,
        root_cause: str,
        auto_patch_instruction: str,
        style_scope: str = "ALL",
        new_forbidden_words: Optional[List[str]] = None,
    ) -> PitfallRecord:
        for existing in self.records:
            if existing.symptom == symptom and existing.style_scope == style_scope:
                return existing

        rule_id = f"EVO_{len(self.records) + 1:03d}"
        rec = PitfallRecord(
            rule_id=rule_id,
            agent_id=self.agent_id,
            style_scope=style_scope,
            trigger_source=trigger_source,
            symptom=symptom,
            root_cause=root_cause,
            auto_patch_instruction=auto_patch_instruction,
            new_forbidden_words=new_forbidden_words or [],
        )
        self.records.append(rec)
        self.save_records()
        return rec

    def rollback_last_evolution(self) -> Optional[PitfallRecord]:
        if not self.records:
            return None
        popped = self.records.pop()
        self.save_records()
        return popped

    def get_dynamic_forbidden_words(self, style_id: str = "ALL") -> List[str]:
        words: List[str] = []
        for r in self.records:
            if r.style_scope in ("ALL", style_id):
                words.extend(r.new_forbidden_words)
        return list(dict.fromkeys(words))

    def format_experience_for_status_bar(self, style_id: str = "ALL") -> str:
        relevant = [r for r in self.records if r.style_scope in ("ALL", style_id)]
        if not relevant:
            return "暂无历史踩坑记录"
        lines = [f"[{r.rule_id}|{r.style_scope}] 避坑：{r.auto_patch_instruction}" for r in relevant[-5:]]
        return " ； ".join(lines)


# ============================================================================
# 1. 解耦风格的五大主流画风配置字典 (Decoupled StyleProfile Registry)
# ============================================================================

STYLE_PROFILES: Dict[str, Dict[str, Any]] = {
    "3D_DONGHUA": {
        "name": "3D国漫玄幻修仙",
        "positive_anchor": "3d donghua style, Unreal Engine 5 render, subsurface scattering, cinematic volumetric rim light, 8k",
        "forbidden_regexes": [
            r"\b(qipao|cheongsam)\b",
            r"\b(female|girl|woman)\b",
            r"\b(muscular bodybuilder)\b",
            r"(?<!without\s)(?<!no\s)\b(beard|mustache)\b",
            r"\b(modern tracksuit|bicycle|high school)\b",
        ],
    },
    "MODERN_CAMPUS": {
        "name": "现代都市校园青春",
        "positive_anchor": "modern high school campus, chinese oversized tracksuit school uniform with zipper, dappled sunlight through leaves, clean natural lighting, 8k",
        "forbidden_regexes": [
            r"\b(ancient|armor|sword|robe|hanfu|martial arts|flying sword)\b",
            r"\b(sailor uniform|pleated skirt|blazer|necktie)\b",
        ],
    },
    "TRADITIONAL_INK": {
        "name": "新中式写意水墨",
        "positive_anchor": "traditional chinese ink painting, guochao watercolor, artistic brush strokes, splash ink, rice paper texture, ethereal",
        "forbidden_regexes": [
            r"\b(3d|cgi|plastic|glossy|octane render|photorealistic|neon)\b",
        ],
    },
    "CYBERPUNK_MECHA": {
        "name": "科幻赛博硬核机械",
        "positive_anchor": "cyberpunk sci-fi style, hard surface mechanical details, neon volumetric fog, chromatic aberration, ray tracing reflection",
        "forbidden_regexes": [
            r"\b(ancient|straw sandals|hemp vest|wooden hairpin|ink wash)\b",
        ],
    },
    "DARK_MANHWA": {
        "name": "暗黑韩漫条漫风",
        "positive_anchor": "dark fantasy manhwa style, sharp ink lineart, dramatic cel shading, extreme dynamic angle, high contrast comic panel",
        "forbidden_regexes": [
            r"\b(3d|photorealistic|clay|soft pastel)\b",
        ],
    },
}


# ============================================================================
# 2. 强类型数据契约：自主冲突筛查报告 + 分镜表 (Data Layer Guardrails)
# ============================================================================

BASE_PSYCHOLOGICAL_FORBIDDEN_WORDS = [
    "心里", "想起了", "如鼠见猫", "觉得", "暗道", "心想", "暗自", "思忖", "暗暗", "回忆起"
]

ACTIVE_STYLE_ID: str = "3D_DONGHUA"
DYNAMIC_LEARNED_PSYCH_WORDS: List[str] = []


class ConflictType(str, Enum):
    LIFE_OR_DEATH = "Life_Or_Death"
    STATUS_HUMILIATION = "Status_Humiliation"
    OPPORTUNITY_SNATCH = "Opportunity_Snatch"
    SECRET_OMEN = "Secret_Omen"


class ConflictCandidate(BaseModel):
    conflict_id: str = Field(description="冲突候选编号，如 CF_01, CF_02")
    chapter_source: str = Field(description="所属原著章节与段落定位")
    source_excerpt: str = Field(description="对应小说原文的核心冲突原句摘录")
    conflict_type: ConflictType = Field(description="冲突核心类型")
    opposing_forces: str = Field(description="对立双方与核心矛盾")
    stakes_score: int = Field(ge=1, le=10, description="生死/机缘筹码强度 (1-10)")
    status_gap_score: int = Field(ge=1, le=10, description="阶层反差与情绪压迫感强度 (1-10)")
    visual_impact_score: int = Field(ge=1, le=10, description="画面奇观与动作外化表现力 (1-10)")
    selected_for_episode: bool = Field(description="是否被筛选保留进短剧正片")
    target_placement: str = Field(description="编排定位：0-3s黄金钩子 / 中段压迫升级 / 45s反转爽点 / 75-90s集尾断章 / 剔除")
    drop_or_keep_reason: str = Field(description="保留并重排或作为慢热水词剔除的具体导演决策原因")

    @property
    def composite_score(self) -> float:
        return round((self.stakes_score + self.status_gap_score + self.visual_impact_score) / 3.0, 2)


class ConflictSiftingReport(BaseModel):
    discarded_filler_summary: List[str] = Field(
        description="被自动识别并砍掉的原著慢热铺垫、民俗科普、风景描写、走路送信日常清单"
    )
    conflict_candidates: List[ConflictCandidate] = Field(
        description="从原文中扫描提取出的所有潜在冲突点列表"
    )
    selected_opening_hook_id: str = Field(
        description="被选定提权并倒叙前置到 0-3 秒首镜的最高张力冲突 ID"
    )
    selected_cliffhanger_id: str = Field(
        description="被选定作为 75-90 秒集尾断章卡点的最高悬念冲突 ID"
    )

    @compat_validator("conflict_candidates")
    @classmethod
    def check_candidates_not_empty(cls, v: List[ConflictCandidate]) -> List[ConflictCandidate]:
        if not v:
            raise ValueError("冲突筛查失败：未从原文中提炼出任何 ConflictCandidate！")
        kept = [c for c in v if c.selected_for_episode]
        if not kept:
            raise ValueError("冲突筛查失败：至少需要筛选保留 1 个高价值核心冲突！")
        max_score = max(c.composite_score for c in kept)
        if max_score < 7.5:
            raise ValueError(
                f"冲突烈度不足拦截：当前最高冲突综合分仅 {max_score} (<7.5)，请深挖原文中的生死、机缘或阶层压迫冲突！"
            )
        return v


class ShotSize(str, Enum):
    EXTREME_CLOSE_UP = "Extreme Close-Up"
    CLOSE_UP = "Close-Up"
    MEDIUM_SHOT = "Medium Shot"
    FULL_SHOT = "Full Shot"
    WIDE_SHOT = "Wide Shot"


class HookType(str, Enum):
    CRISIS_OPENING = "Crisis_Opening"
    NORMAL_BEAT = "Normal_Beat"
    REVERSAL_TURN = "Reversal_Turn"
    CLIFFHANGER_END = "Cliffhanger_End"


class MotionTier(str, Enum):
    TIER_A = "Tier_A"
    TIER_B = "Tier_B"
    TIER_C = "Tier_C"



class EpisodeContinuityLedger:
    """
    [对标 DramaClaw 虾塘跨集连续性记忆]
    跨集场记账本：持久化记录每集结尾的角色服装状态（如破损/血迹）、持有道具与所处场景位置，
    下一集生成剧本和分镜时自动读取继承，杜绝跨集穿帮。
    """
    def __init__(self, ledger_path: Optional[Path] = None):
        self.ledger_path = ledger_path or (Path(__file__).resolve().parent.parent / "episode_continuity_state.json")
        self.state: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.ledger_path.exists():
            try:
                return json.loads(self.ledger_path.read_text(encoding="utf-8"))
            except Exception:
                return {"episodes": {}, "character_states": {}}
        return {"episodes": {}, "character_states": {}}

    def update_character_state(self, character_id: str, costume_state: str, held_props: List[str], location: str, injury_state: str = "normal"):
        self.state.setdefault("character_states", {})[character_id] = {
            "costume_state": costume_state,
            "held_props": held_props,
            "location": location,
            "injury_state": injury_state,
        }
        self.ledger_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_character_state(self, character_id: str) -> Dict[str, Any]:
        return self.state.get("character_states", {}).get(character_id, {})


class Shot(BaseModel):
    shot_id: str = Field(description="镜头唯一编号，格式严格为 SC01_SH001")
    source_conflict_id: str = Field(description="关联的冲突候选编号，如 CF_01")
    hook_type: HookType = Field(description="该镜头在短剧节奏中的钩子功能定位")
    tension_score: int = Field(ge=1, le=10, description="情绪压强评分(1-10)，首镜必须>=8，集尾必须>=9")
    shot_size: ShotSize = Field(description="标准镜头景别")
    camera_movement: str = Field(description="运镜方式，如 fast zoom in / low angle tilt up")
    visual_action: str = Field(description="纯视觉外化的物理动作与微表情")
    dialogue: Optional[str] = Field(default=None, description="角色台词，严格<=15字")
    sound_effect: str = Field(description="关键动作拟音或环境音效")
    first_frame_anchor: Optional[str] = Field(default="继承上一镜场景与站位锚点", description="首帧构图与承接锚点")
    last_frame_anchor: Optional[str] = Field(default="动作定格尾帧锚点", description="尾帧构图与传下一镜锚点")
    motion_tier: MotionTier = Field(description="动效生成路由分级 Tier_A / Tier_B / Tier_C")
    gen_duration_sec: float = Field(default=6.0, description="视频大模型 API 生成时长挡位(如6.0s)")
    edit_duration_sec: float = Field(default=2.5, description="剪辑时间轴实际截取保留的高光时长(如2.5s)")
    width: int = Field(default=768, description="生成宽度，必须为8的整数倍")
    height: int = Field(default=432, description="生成高度，必须为8的整数倍")
    prompt_en: str = Field(description="ComfyUI 专用英文正面提示词，匹配当前 StyleProfile")
    expected_continuity_check: str = Field(
        description="ACI 自检参数：确认本镜头中角色服装、伤势、道具与 <agent_status> 场记完全一致的核对说明"
    )

    @compat_validator("visual_action")
    @classmethod
    def check_no_psychological_words(cls, v: str) -> str:
        all_forbidden = BASE_PSYCHOLOGICAL_FORBIDDEN_WORDS + DYNAMIC_LEARNED_PSYCH_WORDS
        for word in all_forbidden:
            if word in v:
                raise ValueError(f"视觉外化硬拦截：出现了摄影机拍不到的心理/违规词 '{word}'，必须改为生理动作与物理表现！")
        return v

    @compat_validator("dialogue")
    @classmethod
    def check_dialogue_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 15:
            raise ValueError(f"台词超长拦截（当前 {len(v.strip())} 字）：商业短剧单行字幕不得超过 15 字，请精简！")
        return v

    @compat_validator("width")
    @classmethod
    def check_width_8px(cls, v: int) -> int:
        if v % 8 != 0:
            raise ValueError(f"宽度参数 {v} 违反 ComfyUI Latent 8 像素步进定律！请改为 768 或 832。")
        return v

    @compat_validator("height")
    @classmethod
    def check_height_8px(cls, v: int) -> int:
        if v % 8 != 0:
            raise ValueError(f"高度参数 {v} 违反 ComfyUI Latent 8 像素步进定律！请改为 432 或 464。")
        return v

    @compat_validator("prompt_en")
    @classmethod
    def check_forbidden_tokens(cls, v: str) -> str:
        profile = STYLE_PROFILES.get(ACTIVE_STYLE_ID, STYLE_PROFILES["3D_DONGHUA"])
        lower_v = v.lower()
        for pattern in profile["forbidden_regexes"]:
            if re.search(pattern, lower_v):
                raise ValueError(f"风格 [{ACTIVE_STYLE_ID}] 提示词拦截：包含高危污染特征 (匹配 {pattern})，请剔除！")
        return v


class EpisodeScript(BaseModel):
    episode_id: str = Field(description="剧集唯一标识，如 EP01")
    style_id: str = Field(default="3D_DONGHUA", description="当前剧集绑定的视觉风格配置 ID")
    title_hook: str = Field(description="本集一句话爆款爽点标题")
    covered_chapters: str = Field(description="本集浓缩覆盖的原著章节范围")
    character_state_summary: str = Field(description="本集角色服装、伤势与随身道具状态汇总")
    conflict_sifting_report: ConflictSiftingReport = Field(
        description="常驻前置步骤：原文脱水与冲突提炼筛查报告"
    )
    shots: List[Shot] = Field(description="本集完整分镜序列")

    @compat_validator("shots")
    @classmethod
    def validate_waveform(cls, shots: List[Shot]) -> List[Shot]:
        if len(shots) < 4:
            raise ValueError("分镜数量过少：单集短剧至少需要 4 个以上分镜以构成完整情绪波形！")
        if shots[0].hook_type != HookType.CRISIS_OPENING or shots[0].tension_score < 8:
            raise ValueError("黄金3秒拦截：第 1 个镜头必须是 Crisis_Opening 且 tension_score >= 8！")
        if shots[-1].hook_type != HookType.CLIFFHANGER_END or shots[-1].tension_score < 9:
            raise ValueError("集尾卡点拦截：最后一个镜头必须是 Cliffhanger_End 且 tension_score >= 9！")
        return shots


class MultiEpisodeAdaptationPlan(BaseModel):
    novel_title: str = Field(description="原著名称与输入章节范围")
    style_id: str = Field(default="3D_DONGHUA", description="全局视觉风格 ID")
    global_dehydration_rate: str = Field(description="全局脱水比例说明")
    episodes: List[EpisodeScript] = Field(description="按单集 60-90 秒黄金容量切分后的剧集列表")


class ReviewResult(BaseModel):
    passed: bool = Field(description="是否通过冲突烈度、短剧钩子与场记连续性独立审查")
    veto_triggered: bool = Field(description="是否触发一票否决项")
    score: int = Field(ge=0, le=100, description="综合评分 (0-100)")
    critique_feedback: str = Field(description="若未通过，给出可直接用于下一轮修正的具体修改指令")
    reflection_root_cause: str = Field(
        default="",
        description="审计官归因：指出编剧 Agent 本次产生偏差的认知根源，供自进化引擎写入 memories"
    )


# ============================================================================
# 3. 多模型统一兼容路由层 (内置硬性用户授权审批闸口)
# ============================================================================

PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "name_cn": "DeepSeek 官方平台",
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "supports_json_schema": False,
        "strip_think_tags": True,
    },
    "kimi": {
        "name_cn": "月之暗面 Kimi (Moonshot AI)",
        "base_url": "https://api.moonshot.cn/v1",
        "env_key": "MOONSHOT_API_KEY",
        "default_model": "moonshot-v1-128k",
        "supports_json_schema": False,
        "strip_think_tags": True,
    },
    "qwen": {
        "name_cn": "阿里云百炼 (通义千问 DashScope)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_key": "DASHSCOPE_API_KEY",
        "default_model": "qwen3.7-plus",
        "supports_json_schema": False,
        "strip_think_tags": True,
    },
    "openai": {
        "name_cn": "302.AI / OpenAI 聚合网关",
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
        "supports_json_schema": True,
        "strip_think_tags": False,
    },
    "ollama": {
        "name_cn": "本地离线模型 (Ollama)",
        "base_url": "http://127.0.0.1:11434/v1",
        "env_key": "OLLAMA_API_KEY",
        "default_model": "qwen2.5:7b",
        "supports_json_schema": False,
        "strip_think_tags": True,
    },
}


class UnifiedLLMClient:
    def __init__(
        self,
        provider: str = "deepseek",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        agent_role: str = "通用Agent",
        approval_callback: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        provider_key = provider.lower()
        if provider_key not in PROVIDER_CONFIGS:
            raise ValueError(f"不支持的 provider: {provider}，可选: {list(PROVIDER_CONFIGS.keys())}")

        cfg = PROVIDER_CONFIGS[provider_key]
        self.provider = provider_key
        self.provider_cn = cfg["name_cn"]
        self.model = model or cfg["default_model"]
        self.agent_role = agent_role
        self.env_key = cfg["env_key"]
        self.approval_callback = approval_callback

        env_base = None
        if provider_key == "openai":
            env_base = os.environ.get("OPENAI_BASE_URL")
        elif provider_key == "qwen":
            env_base = os.environ.get("DASHSCOPE_BASE_URL")
        elif provider_key == "kimi":
            env_base = os.environ.get("MOONSHOT_BASE_URL")

        target_base = base_url or env_base or cfg["base_url"]
        self.base_url = target_base.rstrip("/")

        self.api_key = api_key or os.environ.get(cfg["env_key"], "")
        self.supports_json_schema = cfg["supports_json_schema"]
        self.strip_think_tags = cfg["strip_think_tags"]

    def _mask_key(self, key_str: str) -> str:
        """对敏感 Key 进行脱敏安全显示，如 your_api_key_here"""
        if not key_str or len(key_str) < 12:
            return "******"
        return f"{key_str[:7]}...{key_str[-4:]}"

    def request_user_authorization(self, task_intent: str) -> bool:
        """
        【硬性安全闸口】向用户显式声明即将调用的接口与Key，获得许可后才准放行！
        """
        auth_payload = {
            "agent_role": self.agent_role,
            "platform_name": self.provider_cn,
            "base_url": self.base_url,
            "model_name": self.model,
            "key_env_var": self.env_key,
            "masked_key": self._mask_key(self.api_key),
            "task_intent": task_intent,
        }

        # 若外部注入了交互式审批回调，直接走外部回调判定
        if self.approval_callback:
            return self.approval_callback(auth_payload)

        # 默认终端显式声明并等待用户确认（环境非交互时由全局开关接管）
        print("\n" + "=" * 65)
        print("【安全告警：Agent 发起外部 API 扣费调用申请】")
        print(f"• 发起岗位: {auth_payload['agent_role']}")
        print(f"• 目标平台: {auth_payload['platform_name']}")
        print(f"• 请求地址: {auth_payload['base_url']}/chat/completions")
        print(f"• 调用模型: {auth_payload['model_name']}")
        print(f"• 扣费凭据: {auth_payload['key_env_var']} ({auth_payload['masked_key']})")
        print(f"• 任务意图: {auth_payload['task_intent']}")
        print("=" * 65)

        # 本地终端交互确认
        if os.environ.get("AUTO_APPROVE_ALL_KEYS", "").lower() in ("true", "1", "yes"):
            print(">>> [全局安全策略] 检测到白名单环境变量，自动授权放行。")
            return True

        user_input = input(">>> 是否允许该 Agent 调用此 Key？(y/yes 允许，其他拒绝): ").strip().lower()
        if user_input in ("y", "yes"):
            print(">>> [已获得用户许可] 正在发起网络请求...")
            return True
        else:
            print(">>> [用户拒绝授权] API 调用已强行拦截中断！")
            return False

    @staticmethod
    def clean_json_text(raw_text: str) -> str:
        cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def chat_structured(
        self,
        static_system_prompt: str,
        messages: List[Dict[str, str]],
        schema_cls: type[BaseModel],
        task_intent: str = "结构化数据推理生成",
        temperature: float = 0.3,
    ) -> str:
        import urllib.request

        # 0. API Key 前置硬校验：未配置凭据时直接给出可执行的配置指引，避免发出必然 401 的请求
        if not self.api_key or self.api_key.startswith("your_"):
            raise RuntimeError(
                f"[API Key 未配置] {self.agent_role} 需要 {self.provider_cn} 的凭据。\n"
                f"  1) 在项目根目录执行: cp .env.example .env\n"
                f"  2) 在 .env 中填写: {self.env_key}=你的真实密钥\n"
                f"  3) 重新运行: python scripts/preflight_check.py\n"
                f"  详见 README.md「使用前必读：先配置 API Key」。"
            )

        # 1. 强制执行前置用户授权审批闸口（未获批准绝不发出网络包）
        allowed = self.request_user_authorization(task_intent=task_intent)
        if not allowed:
            raise PermissionError(
                f"安全拦截：用户未批准 {self.agent_role} 调用 {self.provider_cn} 的 API Key ({self.model})！"
            )

        # 2. 授权通过后，将 Pydantic JSON Schema 注入系统提示词，避免字段名幻觉导致 ValidationError
        schema_json = json.dumps(
            schema_cls.model_json_schema() if hasattr(schema_cls, "model_json_schema") else schema_cls.schema(),
            ensure_ascii=False,
        )
        enforced_system = (
            f"{static_system_prompt}\n\n"
            f"【强制输出 JSON Schema 约束】严格按以下 JSON Schema 的字段名与类型输出纯 JSON：\n{schema_json}"
        )
        full_messages = [{"role": "system", "content": enforced_system}] + messages
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
            "response_format": {"type": "json_object"},
        }

        lower_model = self.model.lower()
        if "reasoner" not in lower_model and not lower_model.startswith("o1") and not lower_model.startswith("o3"):
            payload["temperature"] = temperature

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp_json = json.loads(resp.read().decode("utf-8"))
            msg = resp_json["choices"][0]["message"]
            content = msg.get("content", "")
            return self.clean_json_text(content)


# ============================================================================
# 4. 固化自主冲突筛查与自省进化的静态前缀 (Context Engineering)
# ============================================================================

STATIC_PROPOSER_SYSTEM_PROMPT = """# Role: 工业级全风格爆款短剧总编剧兼冲突提炼导演 (Agent 1 - Proposer)

你的核心职责是：接收任意长度、包含大量慢热日常铺垫的网文原文，**自主执行“冲突筛查与原著脱水”**，并根据当前指定的 `style_id` 风格配置与末尾 `<agent_status>` 中的【历史自省避坑经验】，将其浓缩重构为高完播率商业短剧分镜脚本 JSON。
"""

STATIC_REVIEWER_SYSTEM_PROMPT = """# Role: 独立短剧冲突烈度、场记连续性与认知归因审计官 (Agent 2 - Independent Reviewer)

你是一个与编剧上下文完全隔离的独立审查 Agent。你负责对照小说原文、冲突筛查报告与分镜 JSON，按 Scale AI Rubric 准则执行严苛审计。
一旦发现未达标项，你不仅要在 `critique_feedback` 中给出具体修改指令，还必须在 `reflection_root_cause` 中指出编剧 Agent 的认知偏差根源，以便写入持久自进化记忆库。
"""


def build_agent_status_bar(
    episode_id: str,
    style_id: str,
    character_lock: str,
    retry_count: int,
    max_retries: int,
    learned_experience_str: str,
    last_error: Optional[str] = None,
) -> str:
    style_cfg = STYLE_PROFILES.get(style_id, STYLE_PROFILES["3D_DONGHUA"])
    error_block = f"\n- 上一轮审查未通过驳回原因 (必须严格修正): {last_error}" if last_error else ""
    return (
        f"<agent_status>\n"
        f"- 当前剧集任务: {episode_id} | 绑定视觉风格: {style_id} ({style_cfg['name']})\n"
        f"- 风格正向基石词: {style_cfg['positive_anchor']}\n"
        f"- 角色连续性状态 (场记锁): {character_lock}\n"
        f"- <learned_experience> 历史自省沉淀准则: {learned_experience_str} </learned_experience>\n"
        f"- 当前自愈迭代轮次: {retry_count}/{max_retries}{error_block}\n"
        f"</agent_status>"
    )


# ============================================================================
# 5. 搭载【用户授权审批闸口】的编剧闭环 Harness
# ============================================================================

class ScriptwriterHarness:
    def __init__(
        self,
        proposer_client: UnifiedLLMClient,
        reviewer_client: Optional[UnifiedLLMClient] = None,
        workspace_dir: str = "./workspace_ep01",
        memory_dir: str = "./memories",
        max_retries: int = 3,
    ):
        self.proposer = proposer_client
        self.reviewer = reviewer_client or proposer_client
        self.workspace = Path(workspace_dir)
        self.scratch_dir = self.workspace / "scratch" / "agent1_scriptwriter"
        self.shared_dir = self.workspace / "shared" / "scripts"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries

        self.evolution_engine = UniversalEvolutionEngine(
            agent_id="agent1_scriptwriter",
            memory_dir=memory_dir,
        )

    def sync_evolution_guardrails(self, style_id: str = "3D_DONGHUA") -> None:
        global ACTIVE_STYLE_ID, DYNAMIC_LEARNED_PSYCH_WORDS
        ACTIVE_STYLE_ID = style_id
        DYNAMIC_LEARNED_PSYCH_WORDS = self.evolution_engine.get_dynamic_forbidden_words(style_id)

    def learn_from_user_feedback(
        self,
        user_feedback: str,
        root_cause: str,
        patch_instruction: str,
        style_scope: str = "ALL",
        new_forbidden_words: Optional[List[str]] = None,
    ) -> PitfallRecord:
        rec = self.evolution_engine.reflect_and_evolve(
            trigger_source="User_Feedback",
            symptom=user_feedback,
            root_cause=root_cause,
            auto_patch_instruction=patch_instruction,
            style_scope=style_scope,
            new_forbidden_words=new_forbidden_words,
        )
        self.sync_evolution_guardrails(style_scope if style_scope != "ALL" else ACTIVE_STYLE_ID)
        return rec

    def deterministic_verify(self, raw_json_str: str, style_id: str = "3D_DONGHUA") -> Tuple[Optional[EpisodeScript], Optional[str]]:
        self.sync_evolution_guardrails(style_id)
        try:
            script_obj = compat_parse_json(EpisodeScript, raw_json_str)
            return script_obj, None
        except ValidationError as e:
            err_msg = f"[代码硬检拦截] 格式或规则违规: {e}"
            self.evolution_engine.reflect_and_evolve(
                trigger_source="Code_Guard",
                symptom="分镜草稿触发确定性 Schema 拦截",
                root_cause=str(e)[:200],
                auto_patch_instruction="严格控制单句台词<=15字，严禁在 visual_action 中使用任何主观心理词汇。",
                style_scope=style_id,
            )
            return None, err_msg
        except Exception as e:
            return None, f"[代码硬检拦截] JSON 解析失败: {e}"

    def run_episode_adaptation(
        self,
        episode_id: str,
        novel_text: str,
        character_lock: str,
        style_id: str = "3D_DONGHUA",
    ) -> Path:
        self.sync_evolution_guardrails(style_id)
        last_error: Optional[str] = None

        for attempt in range(1, self.max_retries + 1):
            learned_exp = self.evolution_engine.format_experience_for_status_bar(style_id)
            status_bar = build_agent_status_bar(
                episode_id=episode_id,
                style_id=style_id,
                character_lock=character_lock,
                retry_count=attempt,
                max_retries=self.max_retries,
                learned_experience_str=learned_exp,
                last_error=last_error,
            )

            user_message = (
                f"【待筛查与改编的小说原文】\n{novel_text}\n\n"
                f"【输出要求】请先生成 conflict_sifting_report 冲突提炼报告，再生成 shots 分镜，严格输出纯 JSON：\n"
                f"{json.dumps(compat_json_schema(EpisodeScript), ensure_ascii=False)}\n\n"
                f"{status_bar}"
            )

            # 1. 调用 Proposer 生成草稿（受授权闸口保护）
            raw_draft = self.proposer.chat_structured(
                static_system_prompt=STATIC_PROPOSER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
                schema_cls=EpisodeScript,
                task_intent=f"生成剧集 {episode_id} 冲突筛查脱水报告与分镜脚本草稿",
            )

            draft_path = self.scratch_dir / f"{episode_id}_attempt_{attempt}.json"
            draft_path.write_text(raw_draft, encoding="utf-8")

            # 2. 第一层验证：代码硬检（零 API 成本）
            script_obj, code_err = self.deterministic_verify(raw_draft, style_id=style_id)
            if code_err:
                last_error = code_err
                continue

            # 3. 第二层验证：独立 Reviewer 审查（受授权闸口保护）
            review_prompt = (
                f"【原始小说】\n{novel_text}\n\n"
                f"【待审查分镜与冲突筛查报告 JSON】\n{raw_draft}\n\n"
                f"{status_bar}"
            )
            raw_review = self.reviewer.chat_structured(
                static_system_prompt=STATIC_REVIEWER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": review_prompt}],
                schema_cls=ReviewResult,
                task_intent=f"对剧集 {episode_id} 分镜执行独立严苛审计与认知归因",
                temperature=0.1,
            )
            review_res = compat_parse_json(ReviewResult, raw_review)

            if not review_res.passed or review_res.veto_triggered or review_res.score < 90:
                rejection_reason = f"审查官打分 {review_res.score} 未达标: {review_res.critique_feedback}"
                self.evolution_engine.reflect_and_evolve(
                    trigger_source="Reviewer_Audit",
                    symptom=review_res.critique_feedback[:120],
                    root_cause=review_res.reflection_root_cause or "未完全遵循爆款短剧冲突前置或外化规范",
                    auto_patch_instruction=review_res.critique_feedback,
                    style_scope=style_id,
                )
                last_error = rejection_reason
                continue

            final_path = self.shared_dir / f"{episode_id}_storyboard_verified.json"
            final_path.write_text(compat_dump_json(script_obj), encoding="utf-8")
            return final_path

        raise RuntimeError(f"自愈熔断跳闸：剧集 {episode_id} 连续 {self.max_retries} 轮自我审查均未达标！")


if __name__ == "__main__":
    print(f"[硬性安全规则生效] 任何 Agent 调用 Key 前必须明确声明接口、模型与脱敏凭据，获得用户许可后方可放行！")