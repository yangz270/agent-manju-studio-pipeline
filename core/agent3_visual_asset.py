# -*- coding: utf-8 -*-
"""
core/agent3_visual_asset.py

工业级全风格 AI 漫剧管线 —— 深度进化版：Agent 3 视觉资产与风格总监 (Visual Asset Master v2.5 - 2026 工业标准完全体)
融合《ComfyUI 2026 实战知识库（模块 00~04）》与 16:9 横屏漫剧工程规范

【Agent 3 核心落地的 6 大工业支柱】：
1. 角色基底图“四要四不要”铁律与第三代资产流水线 (Krea2 + Qwen-Image 2.1)：
   - 基底图铁律：纯白背景 (Pure White BG) + 全身正面站立含鞋 + 直视镜头 + 零动作动词 + 1~2个独特视觉锚点（忌盲目华丽）。
   - 多视图演进：废弃旧版横排四视图，全面生成【4:3 横版三视图+表情特写】或【2×2 四宫格参考图（右下角全身图强制裁掉/虚化小脸，逼迫模型只参考左上/右上高清大脸）】。
2. 场景资产“四要素锁定法” (Scene Bible Four-Pillar Lock)：
   - 严格锁定：① 空间结构；② 光影氛围与物理色温 (Kelvin)；③ 色彩风格；④ 关键识别道具，确保空镜无人物且跨镜头空间连戏。
3. 16:9 影视横屏专精与 LOD 景别细节动态过滤：
   - 锁定 16:9 横屏 (`768×432` 单镜 / `1536×864` 四宫格，严守 8 像素步进)。
   - LOD 过滤：特写锁死瞳孔/微表情/喉结，剔除鞋履防假肢；全景恢复全身比例与草鞋，弱化微观五官词防远景脸部涂抹。
4. 180 度轴线保护与多人同框“序号指代铁律” (Image Index Reference Rule)：
   - 锁定左右视线朝向 (`FACING_RIGHT` vs `FACING_LEFT`) 防跳轴。
   - 多人同框与四宫格分镜中**严禁出现“主角少年/反派贵族”等人名**，强制转换为 `图一(image1)/图二(image2)` + 显式服装颜色声明。
5. 跨代际模型参数自适应护栏 (2026 Generation Guardrail)：
   - 2026 新模型 (Krea2 / Z-Image / Qwen 2.1) 自动锁死 `CFG = 1.0`、负面开启 `ConditioningZeroOut`；
   - 传统极速主力 (SD1.5 revAnimated) 自动匹配 `CFG = 7.0, Steps = 22, Denoise = 0.40`。
"""

import datetime
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# 自动加载当前目录下的 .env 配置文件
def load_dotenv_file(dotenv_path: Optional[Path] = None):
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parent / ".env"
    if dotenv_path.exists():
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v

load_dotenv_file()

try:
    from agent1_2_scriptwriter import (
        STYLE_PROFILES,
        UniversalEvolutionEngine,
    )
except ImportError:
    STYLE_PROFILES = {
        "3D_DONGHUA": {
            "name": "3D国漫玄幻修仙",
            "default_ckpt": "revAnimated_v122.safetensors",
            "positive_anchor": "3d donghua style, Unreal Engine 5 render, subsurface scattering, cinematic volumetric rim light, 8k",
            "negative_anchor": "2d, flat, sketch, watercolor, photo, realistic human, modern clothes",
        },
        "KREA2_GUOFENG": {
            "name": "2026 Krea2 国风仙侠CG",
            "default_ckpt": "krea2_turbo_12g.safetensors",
            "positive_anchor": "eastern fantasy xianxia CG art style, delicate brushwork, cinematic lighting, zero AI sharpness, 8k",
            "negative_anchor": "CONDITIONING_ZERO_OUT",
        }
    }
    class UniversalEvolutionEngine:
        def __init__(self, agent_id: str, memory_dir: str = "./memories"):
            self.memory_file = Path(memory_dir) / f"{agent_id}_pitfalls.json"
        def reflect_and_evolve(self, **kwargs):
            return None


# ============================================================================
# 1. 深度工业级数据契约 (2026 标准版)
# ============================================================================

class CharacterBibleEntry(BaseModel):
    """
    单个角色的冻结定妆档案 (Character Bible - 2026 第三代标准)
    遵守“四要四不要”：纯白底、全身正面含鞋、直视镜头、静态无动作动词、带独特视觉锚点
    """
    character_id: str = Field(..., description="角色唯一ID")
    standard_name: str = Field(..., description="角色正式名")
    image_ref_slot: str = Field(default="图一 (image1)", description="多参引用时的标准序号代称，严禁在分镜直接写人名")
    gender: str = Field(..., description="性别: 男 / 女")
    apparent_age: int = Field(default=16, description="表观年龄")
    social_identity: str = Field(default="古风主街寒门孤儿", description="身份与剧情阶段，防盲目华丽")
    
    # 1~2个跨镜头锁死身份的独特视觉锚点
    unique_visual_anchors: List[str] = Field(
        default_factory=list,
        description="1~2个独特视觉记忆锚点，如 粗麻绳束发髻, 腰间磨损麻绳结"
    )
    
    # 静态特征分层（基底立绘严禁含动作动词）
    face_and_hair: str = Field(..., description="发型、面容骨骼与眉眼静态特征")
    micro_expression_traits: str = Field(default="tense jawline, tight lips, sharp focused pupils", description="分镜微表情特质")
    upper_body_wardrobe: str = Field(..., description="上半身衣着颜色与材质")
    lower_body_wardrobe: str = Field(..., description="下半身裤着颜色与材质")
    footwear: str = Field(default="hand-woven rough straw sandals", description="鞋履（基底立绘必露）")
    distinguishing_marks: str = Field(default="sun-tanned weathered lean physique, visible collarbones, dusty cheeks", description="身体辨识度特征")
    
    character_negative_prompt: str = Field(
        default="beard, mustache, silk robes, golden armor, modern sneakers, clean porcelain face, fat, round face, joyful smile",
        description="角色专属负向屏蔽词"
    )
    
    # 第三代资产图路径（白底全身立绘 + 4:3三视图 + 裁小脸2x2四宫格）
    asset_sheets: Dict[str, str] = Field(
        default_factory=dict,
        description="包含 base_white_fullbody, sheet_4_3_threeview, sheet_2x2_4grid_cropped_smallface"
    )



class PropBibleEntry(BaseModel):
    """
    [对标 Toonflow 独立道具/武器/灵宠/植物资产卡]
    确保武器、法宝、关键容器（竹篓/钱袋/油纸伞）、灵宠异兽拥有独立白底设定图，不再靠单镜头随机脑补。
    """
    prop_id: str = Field(..., description="道具/灵宠唯一ID，如 prop_golden_carp_basket")
    prop_name: str = Field(..., description="名称，如 竹篓金鲤 / 油纸伞 / 飞剑")
    category: str = Field(default="PROP", description="WEAPON | PROP | PET | PLANT")
    visual_tokens_en: str = Field(..., description="英文视觉特征锁定词")
    white_bg_asset_path: str = Field(default="", description="纯白底设定图路径")


class SceneBibleEntry(BaseModel):
    """
    场景空间连续性档案 (Scene Bible - 2026 四要素锁定法)
    只锁四大核心方向：① 空间结构；② 光影氛围与色温；③ 色彩风格；④ 关键识别道具
    """
    scene_id: str = Field(..., description="场次唯一ID")
    scene_name: str = Field(..., description="场景正式名")
    image_ref_slot: str = Field(default="图三 (image3)", description="多参引用时的标准场景序号")
    
    # 四要素锁定
    spatial_structure: str = Field(..., description="要素1：空间结构与建筑体量")
    lighting_atmosphere_and_kelvin: str = Field(..., description="要素2：光影氛围、丁达尔/轮廓光与开尔文色温")
    color_palette: str = Field(..., description="要素3：主色调、辅助色与点缀色")
    key_identifying_props: List[str] = Field(default_factory=list, description="要素4：关键识别道具")
    master_background_path: str = Field(default="./workspace_ep01/shared/assets/scene_master_16x9.png", description="单场景 16:9 纯景母图路径，同场戏所有分镜共用此背景锚点")
    
    scene_negative_prompt: str = Field(
        default="modern buildings, neon signs, paved asphalt, tropical trees, sunny clear sky, characters, people",
        description="场景专属负向屏蔽词（空镜严禁出现人物）"
    )


class ProductionFormat(BaseModel):
    """画幅比例与 8 像素对齐工程规范：专精 16:9 横屏"""
    format_type: str = Field(default="HORIZONTAL_16_9", description="HORIZONTAL_16_9 (16:9 横屏番剧漫剧)")
    width: int = Field(default=768, description="单镜渲染宽度 (768 对齐 8 像素)")
    height: int = Field(default=432, description="单镜渲染高度 (432 对齐 8 像素)")
    grid_width: int = Field(default=1536, description="2x2 四宫格渲染宽度 (1536)")
    grid_height: int = Field(default=864, description="2x2 四宫格渲染高度 (864)")
    aspect_ratio_str: str = Field(default="16:9", description="画幅比例字符")
    safe_zone_padding: str = Field(
        default="cinematic widescreen 16:9 composition, horizontal rule of thirds framing, balanced lateral margins, theatrical breathing headroom, space reserved for bottom subtitles",
        description="16:9 影视横屏构图与安全区保护词"
    )


class ShotCompositionDirectives(BaseModel):
    """电影级构图与轴线控制指令"""
    shot_scale: str = Field(default="CLOSEUP", description="EXTREME_CLOSEUP | CLOSEUP | MEDIUM_SHOT | FULL_SHOT | ESTABLISHING_WIDE")
    camera_angle: str = Field(default="EYE_LEVEL", description="EYE_LEVEL | LOW_ANGLE_HEROIC | HIGH_ANGLE_OPPRESSIVE | DUTCH_TILT")
    camera_motion: str = Field(default="dolly in (机位前推)", description="区分 zoom in (变焦压缩) 与 dolly in (机位前推)")
    eye_line_facing: str = Field(default="FACING_RIGHT", description="FACING_LEFT | FACING_RIGHT | FACING_CAMERA | PROFILE_LEFT | PROFILE_RIGHT")


class DetailedAssetManifest(BaseModel):
    """经 2026 标准打磨的横屏资产清单 (AssetManifest v2.5)"""
    shot_id: str = Field(..., description="镜头唯一ID")
    scene_id: str = Field(..., description="所属场景ID")
    character_id: Optional[str] = Field(default=None, description="绑定角色ID")
    style_id: str = Field(..., description="画风配置标识")
    model_generation_tier: str = Field(default="SD15_FAST", description="SD15_FAST | 2026_DIT_TURBO | QWEN21_EDIT_SLOW")
    
    production_format: ProductionFormat = Field(...)
    composition: ShotCompositionDirectives = Field(...)
    
    checkpoint_or_unet_name: str = Field(...)
    use_three_piece_loader: bool = Field(default=False, description="是否启用 2026 UNET+CLIP+VAE 三件套分离加载")
    use_conditioning_zero_out: bool = Field(default=False, description="是否启用 2026 条件零化替代负向提示词")
    sampler_name: str = Field(default="dpmpp_2m")
    scheduler: str = Field(default="karras")
    steps: int = Field(default=22)
    cfg: float = Field(default=7.0)
    denoise: float = Field(default=1.0)
    
    # 结构化分块提示词
    chunk1_priority_prompt: str = Field(...)
    chunk2_character_scene_prompt: str = Field(...)
    chunk3_style_lighting_prompt: str = Field(...)
    
    assembled_positive_prompt: str = Field(...)
    assembled_negative_prompt: str = Field(...)
    
    # 2026 新增：角色资产四宫格/三视图构建指令 & 多参序号化分镜指令
    krea2_base_sheet_prompt: Optional[str] = Field(default=None, description="Step1: Krea2 白底全身正面直视基底图提示词")
    qwen21_multiview_prompt: Optional[str] = Field(default=None, description="Step2: Qwen 2.1 合成三视图/裁小脸四宫格指令")
    indexed_storyboard_prompt: Optional[str] = Field(default=None, description="严禁人名、改用图一/图二指代的多参分镜提示词")
    
    reference_image_path: Optional[str] = Field(default=None)
    loras: List[Dict[str, Any]] = Field(default_factory=list)
    ref_bindings: Dict[str, str] = Field(default_factory=dict, description="对标 Toonflow useNodeReferences 的 {{ref 1}}~{{ref N}} 多参考图槽位映射")


# ============================================================================
# 2. Agent 3 深度细节把控核心引擎 (VisualAssetMasterV2)
# ============================================================================

class VisualAssetMasterV2:
    """
    Agent 3 v2.5 (2026 Complete Edition): 视觉资产与风格总监
    全面統管：
    - 角色设定基底图“四要四不要”与 Krea2 + Qwen-Image 2.1 第三代资产构建
    - 场景“四要素锁定法”
    - 16:9 横屏 LOD 景别过滤、物理色温一体化、180 度轴线与 `图一/图二` 序号指代
    - 2026 跨代际模型参数自动适配（CFG=1 vs CFG=7）
    """

    # 基底立绘严禁出现的动作动词黑名单（防转三视图时五官/体态畸变）
    FORBIDDEN_BASE_ACTION_VERBS = [
        "running", "jumping", "walking", "turning", "looking back", "sitting", "crouching",
        "fighting", "slashing", "sliding", "低头", "含胸", "回眸", "奔跑", "跳跃", "坐姿"
    ]

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        default_format: str = "HORIZONTAL_16_9"
    ):
        self.workspace_root = workspace_root or Path(__file__).resolve().parent
        self.memories_dir = self.workspace_root / "memories"
        self.evolution_engine = UniversalEvolutionEngine("agent3_asset_master", str(self.memories_dir))
        
        self.format_config = ProductionFormat(
            format_type="HORIZONTAL_16_9",
            width=768,
            height=432,
            grid_width=1536,
            grid_height=864,
            aspect_ratio_str="16:9",
            safe_zone_padding="cinematic widescreen 16:9 composition, horizontal rule of thirds framing, balanced lateral margins, theatrical breathing headroom, space reserved for bottom subtitles"
        )

        self.character_bible: Dict[str, CharacterBibleEntry] = {}
        self.scene_bible: Dict[str, SceneBibleEntry] = {}
        self.prop_bible: Dict[str, PropBibleEntry] = {}
        self._init_default_prop_bible()
        self._bootstrap_bibles()

    def _init_default_prop_bible(self):
        assets_dir = self.workspace_root / "workspace_ep01" / "shared" / "assets"
        self.prop_bible["prop_bamboo_basket_carp"] = PropBibleEntry(
            prop_id="prop_bamboo_basket_carp",
            prop_name="竹篓金鲤",
            category="PET",
            visual_tokens_en="woven bamboo fish basket holding a glowing golden carp splashing water droplets",
            white_bg_asset_path=str(assets_dir / "prop_bamboo_basket_carp_white.png"),
        )
        self.prop_bible["prop_oiled_paper_umbrella"] = PropBibleEntry(
            prop_id="prop_oiled_paper_umbrella",
            prop_name="古风油纸伞",
            category="PROP",
            visual_tokens_en="traditional Chinese oiled paper bamboo umbrella with raindrops dripping from rim",
            white_bg_asset_path=str(assets_dir / "prop_oiled_paper_umbrella_white.png"),
        )

    def bind_multi_references(self, character_ids: List[str], scene_id: str, prop_ids: Optional[List[str]] = None) -> Dict[str, str]:
        """
        [对标 Toonflow useNodeReferences("in")]
        将角色参考图、单场景纯景母图、道具白底图按 {{ref 1}}、{{ref 2}}... 顺序强绑定，杜绝多实体张冠李戴。
        """
        bindings: Dict[str, str] = {}
        idx = 1
        for cid in character_ids:
            if cid in self.character_bible:
                c_entry = self.character_bible[cid]
                bindings[f"{{{{ref {idx}}}}}"] = c_entry.asset_sheets.get("base_white_fullbody", cid)
                idx += 1
        if scene_id in self.scene_bible:
            bindings[f"{{{{ref {idx}}}}}"] = self.scene_bible[scene_id].master_background_path
            idx += 1
        for pid in (prop_ids or []):
            if pid in self.prop_bible:
                bindings[f"{{{{ref {idx}}}}}"] = self.prop_bible[pid].white_bg_asset_path
                idx += 1
        return bindings

    def _bootstrap_bibles(self):
        """初始化符合 2026 知识库规范的角色定妆宝典与四要素场景字典"""
        assets_dir = self.workspace_root / "workspace_ep01" / "shared" / "assets"
        
        # 1. 主角少年（符合四要四不要：静态外貌服装、含鞋履、带独特锚点、忌盲目华丽）
        self.character_bible["char_protagonist"] = CharacterBibleEntry(
            character_id="char_protagonist",
            standard_name="主角少年",
            image_ref_slot="图一 (image1)",
            gender="男",
            apparent_age=16,
            social_identity="古风主街赤贫孤儿、草鞋少年（忌华丽锦衣）",
            unique_visual_anchors=[
                "rough frayed hemp cord tying small black topknot (粗麻绳束小发髻)",
                "patched coarse grey hemp sleeveless vest tied with thick hemp rope belt (打补丁粗麻无袖坎肩系麻绳腰带)"
            ],
            face_and_hair="1boy, 16 years old, messy black hair tied in small topknot with frayed hemp cord, piercing dark obsidian eyes, firm jawline, slender defined throat",
            micro_expression_traits="grim tense expression, trembling swallow movement in throat, razor-sharp vigilant gaze",
            upper_body_wardrobe="patched coarse grey hemp sleeveless vest over dirty cream undershirt, thick frayed hemp rope tied tightly at waist",
            lower_body_wardrobe="faded patched linen trousers rolled up to calves",
            footwear="hand-woven frayed straw sandals, bare ankles",
            distinguishing_marks="sun-tanned weathered lean physique, visible collarbones, dusty cheeks",
            character_negative_prompt="beard, mustache, silk robes, golden armor, modern sneakers, porcelain face, chubby, smile",
            asset_sheets={
                "base_white_fullbody": str(assets_dir / "protagonist_krea2_white_base.png"),
                "sheet_4_3_threeview": str(assets_dir / "protagonist_qwen21_3view.png"),
                "sheet_2x2_4grid_cropped_smallface": str(assets_dir / "protagonist_qwen21_4grid_cropped.png")
            }
        )

        # 2. 反派贵族
        self.character_bible["char_antagonist"] = CharacterBibleEntry(
            character_id="char_antagonist",
            standard_name="反派贵族",
            image_ref_slot="图二 (image2)",
            gender="男",
            apparent_age=19,
            social_identity="古风主街寄居的大骊失势皇子（清贵但非金甲帝王装）",
            unique_visual_anchors=[
                "clean wooden hairpin on neatly coiffed black hair (整洁木簪束发)",
                "refined indigo-dyed silk-trimmed scholar robe with jade pendant on waist (靛青丝边儒衫配腰间青玉佩)"
            ],
            face_and_hair="1young man, 19 years old, fair aristocratic pale complexion, delicate arched eyebrows, haughty narrow eyes, neatly coiffed hair pinned with clean wooden hairpin",
            micro_expression_traits="condescending sneer on lips, relaxed arrogant half-smile, looking down mockingly",
            upper_body_wardrobe="refined indigo-dyed silk trimmed scholar robe with wide sleeves, crisp white inner silk collar",
            lower_body_wardrobe="flowing indigo silk outer garment, jade pendant hanging at waist",
            footwear="clean black cloth scholar boots",
            distinguishing_marks="pampered fair skin, tall slender posture",
            character_negative_prompt="peasant clothes, ragged fabric, straw sandals, muscular build, rough skin, dust",
            asset_sheets={
                "base_white_fullbody": str(assets_dir / "antagonist_krea2_white_base.png"),
                "sheet_2x2_4grid_cropped_smallface": str(assets_dir / "antagonist_qwen21_4grid_cropped.png")
            }
        )

        # 3. 古风主街场景（严格按照模块 04 T05 四要素锁定法构建）
        self.scene_bible["SC01_MAIN_ALLEY"] = SceneBibleEntry(
            scene_id="SC01_MAIN_ALLEY",
            scene_name="古风主街主角少年祖屋小院",
            image_ref_slot="图三 (image3)",
            spatial_structure="narrow impoverished ancient alley courtyard, peeling cracked rammed-earth walls with exposed straw and dry clay, damp dark grey roof tiles, rickety wooden courtyard gate",
            lighting_atmosphere_and_kelvin="bleak winter 6500K cold overcast ambient daylight, subtle 3200K dim warm rim light grazing rooftop edges, faint dreary winter mist, somber shadows under eaves",
            color_palette="desaturated cold slate grey and weathered earthy clay yellow base tone, muted charcoal shadows, pale frost white accents",
            key_identifying_props=[
                "cracked rammed-earth wall with peeling mud",
                "bare dried locust tree branches in corner",
                "muddy earthen ground with patches of cold slush"
            ],
            scene_negative_prompt="modern buildings, neon lights, paved asphalt road, tropical green trees, bright sunny sky, people, characters, crowd"
        )

    def build_third_gen_character_asset_prompts(self, character_id: str) -> Dict[str, str]:
        """
        【2026 第三代角色资产 SOP 生成器 (模块 02 & T03)】
        Step 1: Krea2 纯白背景、全身正面站立含鞋、直视镜头、静态无动词立绘提示词
        Step 2: Qwen-Image 2.1 结合白膜生成 4:3 三视图与 2×2 四宫格（故意裁掉右下角全身小脸）
        """
        char = self.character_bible[character_id]
        anchors_str = ", ".join(char.unique_visual_anchors)
        
        # Step 1: Krea2 纯白底全身基底图（严格校验无动作动词）
        krea2_base_prompt = (
            f"Pure white background, full-body front standing view including footwear, looking directly at camera, "
            f"static neutral standing pose without action verbs, {char.face_and_hair}, {char.upper_body_wardrobe}, "
            f"{char.lower_body_wardrobe}, {char.footwear}, {char.distinguishing_marks}, "
            f"unique visual anchors: {anchors_str}, consistent eastern fantasy 3d donghua CG style, 8k"
        )
        for verb in self.FORBIDDEN_BASE_ACTION_VERBS:
            assert verb not in krea2_base_prompt.lower(), f"角色基底立绘严禁包含动作动词: {verb}"

        # Step 2a: Qwen-Image 2.1 横版 4:3 三视图 + 表情特写提示词 (对齐 T03 模板)
        qwen21_3view_prompt = (
            f"Character design sheet, 4:3 horizontal layout, keep exact facial features, hairstyle, and clothing from image1 ({char.standard_name}). "
            f"Three-view turnaround (full-body front view, full-body side view, full-body back view) on the left, "
            f"paired with 3 large facial expression close-ups (calm, cold sneer, fierce determination) on the right, "
            f"pure white clean background, full body with footwear visible, looking directly at camera, high consistency."
        )

        # Step 2b: Qwen-Image 2.1 2x2 四宫格参考图（防侧脸崩坏神器，故意裁掉右下角小脸）
        qwen21_4grid_prompt = (
            f"2x2 4-panel character reference grid following layout in image2, strictly keeping exact identity and outfit from image1. "
            f"Top-Left: high-res front half-body portrait; Top-Right: high-res 45-degree side profile portrait; "
            f"Bottom-Left: back view and waist prop details ({anchors_str}); "
            f"Bottom-Right: full-body standing view with small head/face intentionally cropped out to force high-res facial reference from top panels."
        )

        return {
            "krea2_base_white_prompt": krea2_base_prompt,
            "qwen21_3view_prompt": qwen21_3view_prompt,
            "qwen21_4grid_cropped_prompt": qwen21_4grid_prompt
        }

    def build_scene_four_pillar_prompt(self, scene_id: str) -> str:
        """
        【场景资产四要素锁定提示词生成器 (对齐模块 04 T05 模板)】
        空镜头无人物纯场景，锁定空间结构、光影氛围、色彩风格、关键道具
        """
        sc = self.scene_bible[scene_id]
        props_str = ", ".join(sc.key_identifying_props)
        return (
            f"Empty scene without any characters, wide angle 16:9 widescreen establishing shot, strong spatial depth. "
            f"[Spatial Structure]: {sc.spatial_structure}. "
            f"[Lighting & Atmosphere]: {sc.lighting_atmosphere_and_kelvin}. "
            f"[Color Palette]: {sc.color_palette}. "
            f"[Key Identifying Props]: {props_str}. "
            f"3d donghua master environment render, 8k."
        )

    def build_indexed_4grid_storyboard_prompt(
        self,
        scene_id: str,
        panel_specs: List[Dict[str, str]]
    ) -> str:
        """
        【2×2 四宫格分镜与多参序号化提示词编译器 (对齐模块 04 T06 & Step 5 铁律)】
        核心铁律：严禁在多人/多格提示词里直接写“主角少年/反派贵族”等角色名！
        必须统一转换为“图一(image1)身穿打补丁粗麻坎肩的少年”、“图二(image2)身穿靛青丝边儒衫的青年”！
        """
        sc = self.scene_bible[scene_id]
        lines = [
            f"4-panel storyboard contact sheet, 2x2 grid standard layout, 16:9 widescreen per panel, 3d donghua CG style.",
            f"From left to right, top to bottom are Panel 1, Panel 2, Panel 3, Panel 4 (strictly using image reference indices, no character names):"
        ]
        for idx, p in enumerate(panel_specs, 1):
            char_id = p.get("character_id", "char_protagonist")
            char = self.character_bible[char_id]
            scale = p.get("shot_scale", "Medium Shot")
            pos_action = p.get("action_with_life_detail", "standing in左侧, tightening fists")
            lines.append(
                f"- Panel {idx}: [{scale}], referencing {char.image_ref_slot} (wearing {char.upper_body_wardrobe}), "
                f"{pos_action}, under {sc.lighting_atmosphere_and_kelvin}."
            )
        lines.append(
            f"Reference Binding: image1 is Character A sheet, image2 is Character B sheet, {sc.image_ref_slot} is the ancient alley courtyard environment reference. "
            f"Maintain 100% consistent facial features, outfit colors, and spatial architecture across all 4 panels."
        )
        return "\n".join(lines)

    def _resolve_lod_character_prompt(self, char_entry: CharacterBibleEntry, shot_scale: str) -> str:
        """LOD 景别分级注入：特写剔除鞋履防假肢，全景恢复全身与草鞋"""
        scale = shot_scale.upper()
        if scale in ("EXTREME_CLOSEUP", "CLOSEUP"):
            return (
                f"{char_entry.face_and_hair}, {char_entry.micro_expression_traits}, "
                f"{char_entry.distinguishing_marks}"
            )
        elif scale == "MEDIUM_SHOT":
            return (
                f"{char_entry.face_and_hair}, {char_entry.upper_body_wardrobe}, "
                f"{char_entry.distinguishing_marks}"
            )
        else:
            return (
                f"full body view, {char_entry.face_and_hair}, {char_entry.upper_body_wardrobe}, "
                f"{char_entry.lower_body_wardrobe}, {char_entry.footwear}, {char_entry.distinguishing_marks}"
            )

    def compile_shot_asset_manifest(
        self,
        shot_data: Dict[str, Any],
        style_id: str = "3D_DONGHUA",
        scene_id: str = "SC01_MAIN_ALLEY",
        character_id: Optional[str] = "char_protagonist",
        model_tier: str = "SD15_FAST",
        composition_override: Optional[ShotCompositionDirectives] = None
    ) -> DetailedAssetManifest:
        """
        全自动化深度细节编译管线（支持 SD15_FAST 与 2026_DIT_TURBO 跨代际自适应切换）
        """
        shot_id = shot_data.get("shot_id", "SC01_SH001")
        style_cfg = STYLE_PROFILES.get(style_id, STYLE_PROFILES.get("3D_DONGHUA", {}))

        # 1. 跨代际模型参数自动标定（模块 00 & 01 核心铁律）
        if model_tier == "2026_DIT_TURBO":
            ckpt_name = "krea2_turbo_12g.safetensors"
            use_three_piece = True
            use_zero_out = True
            steps, cfg, sampler, scheduler = 8, 1.0, "euler", "normal"
        elif model_tier == "QWEN21_EDIT_SLOW":
            ckpt_name = "qwen_image_2.1_bf16.safetensors"
            use_three_piece = True
            use_zero_out = True
            steps, cfg, sampler, scheduler = 28, 1.0, "euler", "beta"
        else:
            ckpt_name = style_cfg.get("default_ckpt", "revAnimated_v122.safetensors")
            use_three_piece = False
            use_zero_out = False
            steps, cfg, sampler, scheduler = 22, 7.0, "dpmpp_2m", "karras"

        # 2. 构图、运镜（区分 zoom in 与 dolly in）与 180 度轴线解析
        comp = composition_override or ShotCompositionDirectives(
            shot_scale=shot_data.get("shot_scale", "CLOSEUP"),
            camera_angle=shot_data.get("camera_angle", "EYE_LEVEL"),
            camera_motion=shot_data.get("camera_motion", "dolly in (机位前推)"),
            eye_line_facing=shot_data.get("eye_line_facing", "FACING_RIGHT")
        )

        facing_map = {
            "FACING_RIGHT": "profile angled to right, looking toward right frame, three-quarter right face",
            "FACING_LEFT": "profile angled to left, looking toward left frame, three-quarter left face",
            "FACING_CAMERA": "looking directly forward at camera, centered horizontal eye contact",
            "PROFILE_LEFT": "pure cinematic side profile facing left",
            "PROFILE_RIGHT": "pure cinematic side profile facing right"
        }
        facing_prompt = facing_map.get(comp.eye_line_facing, "looking toward right frame")

        # 3. 获取并执行 LOD 角色特征提纯
        char_entry = self.character_bible.get(character_id)
        if char_entry:
            char_lod_prompt = self._resolve_lod_character_prompt(char_entry, comp.shot_scale)
            char_neg = char_entry.character_negative_prompt
            asset_prompts = self.build_third_gen_character_asset_prompts(character_id)
        else:
            char_lod_prompt = shot_data.get("character_desc", "1boy, lean young martial artist")
            char_neg = ""
            asset_prompts = {}

        # 4. 场景四要素与物理色温光影提取
        scene_entry = self.scene_bible.get(scene_id)
        if scene_entry:
            scene_material_prompt = f"{scene_entry.spatial_structure}, {', '.join(scene_entry.key_identifying_props)}"
            lighting_kelvin_prompt = f"{scene_entry.lighting_atmosphere_and_kelvin}, {scene_entry.color_palette}"
            scene_neg = scene_entry.scene_negative_prompt
        else:
            scene_material_prompt = "weathered ancient courtyard"
            lighting_kelvin_prompt = "cinematic diffuse lighting"
            scene_neg = ""

        action_prompt = shot_data.get("action_en", "sliding back on ground, back hitting mud wall")
        if comp.shot_scale.upper() in ("EXTREME_CLOSEUP", "CLOSEUP"):
            # LOD 动作提纯：特写镜头自动剥离下半身与鞋履词，防止特写画面长出假肢假腿！
            for lower_token in ["straw sandals", "sandals", "shoes", "boots", "bare feet", "bare ankles", "feet", "footwear"]:
                pattern = re.compile(r'\b' + re.escape(lower_token) + r'\b', re.IGNORECASE)
                action_prompt = pattern.sub('', action_prompt)
            action_prompt = ", ".join([t.strip() for t in action_prompt.split(",") if t.strip()])
        style_pos = style_cfg.get("positive_anchor", "3d donghua style, Unreal Engine 5 render, cinematic 16:9 lighting, 8k")
        style_neg = style_cfg.get("negative_anchor", "2d, flat, sketch, photo")

        # 5. 三层结构化分块提示词组装
        chunk1 = (
            f"({comp.shot_scale.lower()} shot:1.25), {comp.camera_angle.lower().replace('_', ' ')}, "
            f"{self.format_config.safe_zone_padding}, {facing_prompt}, {action_prompt}"
        )
        chunk2 = f"{char_lod_prompt}, background of {scene_material_prompt}"
        chunk3 = (
            f"illuminated by {lighting_kelvin_prompt}, color temperature consistency, "
            f"rim light wrapping character edges, {style_pos}"
        )
        assembled_positive = f"{chunk1}, {chunk2}, {chunk3}"

        if use_zero_out:
            cleaned_neg = "CONDITIONING_ZERO_OUT (2026 新世代条件零化占位)"
        else:
            base_neg = "(worst quality:1.4), (low quality:1.4), bad anatomy, extra limbs, extra fingers, missing fingers, deformed hands"
            ui_neg = "watermark, signature, text overlays, subtitles, crop out of frame, pillarbox, vertical video borders"
            assembled_negative = f"{base_neg}, {ui_neg}, {style_neg}, {char_neg}, {scene_neg}"
            cleaned_neg = ", ".join(dict.fromkeys([t.strip() for t in assembled_negative.split(",") if t.strip()]))

        # 生成去人名、按图一/图二指代的分镜提示词
        indexed_prompt = (
            f" referencing {char_entry.image_ref_slot if char_entry else '图一'} "
            f"(strictly wearing {char_entry.upper_body_wardrobe if char_entry else 'coarse tunic'}), "
            f"{action_prompt}, camera movement: {comp.camera_motion}"
        )

        manifest = DetailedAssetManifest(
            shot_id=shot_id,
            scene_id=scene_id,
            character_id=character_id,
            style_id=style_id,
            model_generation_tier=model_tier,
            production_format=self.format_config,
            composition=comp,
            checkpoint_or_unet_name=ckpt_name,
            use_three_piece_loader=use_three_piece,
            use_conditioning_zero_out=use_zero_out,
            sampler_name=sampler,
            scheduler=scheduler,
            steps=steps,
            cfg=cfg,
            denoise=1.0 if not shot_data.get("use_img2img") else 0.40,
            chunk1_priority_prompt=chunk1,
            chunk2_character_scene_prompt=chunk2,
            chunk3_style_lighting_prompt=chunk3,
            assembled_positive_prompt=assembled_positive,
            assembled_negative_prompt=cleaned_neg,
            krea2_base_sheet_prompt=asset_prompts.get("krea2_base_white_prompt"),
            qwen21_multiview_prompt=asset_prompts.get("qwen21_4grid_cropped_prompt"),
            indexed_storyboard_prompt=indexed_prompt,
            reference_image_path=char_entry.asset_sheets.get("sheet_2x2_4grid_cropped_smallface") if char_entry else None,
            loras=[]
        )

        out_dir = self.workspace_root / "workspace_ep01" / "shared" / "manifests"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{shot_id}_manifest_v25.json"
        out_file.write_text(json.dumps(manifest.dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest


# ============================================================================
# 3. 全面验证与自测
# ============================================================================

def run_agent3_v25_validation():
    print("=" * 76)
    print("【工业级全风格 AI 漫剧管线】Agent 3 v2.5 (2026 知识库完全体 + 16:9 横屏) 验证")
    print("=" * 76)

    master = VisualAssetMasterV2(default_format="HORIZONTAL_16_9")

    # 1. 验证第三代角色资产构建 (Krea2 白底全身无动词 + Qwen 2.1 裁右下小脸四宫格)
    char_prompts = master.build_third_gen_character_asset_prompts("char_protagonist")
    print("\n--> [1. 第三代角色资产 SOP 验证]")
    print(f"    • Krea2 白底基底图是否满足四要四不要: {'Pure white background' in char_prompts['krea2_base_white_prompt']}")
    print(f"    • Qwen 2.1 四宫格是否声明裁掉右下角小脸: {'intentionally cropped out' in char_prompts['qwen21_4grid_cropped_prompt']}")

    # 2. 验证场景四要素锁定
    scene_prompt = master.build_scene_four_pillar_prompt("SC01_MAIN_ALLEY")
    print("\n--> [2. 场景四要素锁定法验证]")
    print(f"    • 空镜无人物 + 四要素结构化锁定: {'[Spatial Structure]' in scene_prompt and 'Empty scene' in scene_prompt}")

    # 3. 验证四宫格分镜严禁人名、改用图一/图二指代铁律
    grid_prompt = master.build_indexed_4grid_storyboard_prompt(
        "SC01_MAIN_ALLEY",
        [
            {"character_id": "char_protagonist", "shot_scale": "Close-up", "action_with_life_detail": "positioned on left side, throat swallowing hard, back hitting clay wall"},
            {"character_id": "char_antagonist", "shot_scale": "Medium Shot", "action_with_life_detail": "standing on stone steps on right side, casually playing with jade pendant while sneering"}
        ]
    )
    print("\n--> [3. 多人同框序号指代铁律验证]")
    print(f"    • 是否彻底消除中文人名并改用图一/图二: {'主角少年' not in grid_prompt and '图一 (image1)' in grid_prompt and '图二 (image2)' in grid_prompt}")

    # 4. 验证 SD1.5 与 2026 新世代模型跨代际参数切换
    shot_cu = {
        "shot_id": "SC01_SH001_CU",
        "shot_scale": "CLOSEUP",
        "camera_angle": "LOW_ANGLE_HEROIC",
        "camera_motion": "dolly in (机位前推)",
        "eye_line_facing": "FACING_RIGHT",
        "action_en": "throat swallowing hard with tight grimace, back hitting earthen wall"
    }
    m_sd15 = master.compile_shot_asset_manifest(shot_cu, model_tier="SD15_FAST")
    m_2026 = master.compile_shot_asset_manifest(shot_cu, model_tier="2026_DIT_TURBO")

    print("\n--> [4. 跨代际模型参数护栏验证]")
    print(f"    • SD1.5 极速流: CFG={m_sd15.cfg}, Steps={m_sd15.steps}, 分辨率={m_sd15.production_format.width}x{m_sd15.production_format.height}")
    print(f"    • 2026 Turbo流: CFG={m_2026.cfg}, Steps={m_2026.steps}, 三件套分离={m_2026.use_three_piece_loader}, 条件零化={m_2026.use_conditioning_zero_out}")

    assert m_sd15.cfg == 7.0 and m_2026.cfg == 1.0, "跨代际 CFG 护栏必须精准切换！"
    assert "straw sandals" not in m_sd15.assembled_positive_prompt, "特写镜头 LOD 必须剔除草鞋词！"
    assert "intentionally cropped out" in char_prompts["qwen21_4grid_cropped_prompt"], "四宫格必须包含裁小脸指令！"

    print("\n>>> [Agent 3 v2.5 全项自检 100% 通过] 已彻底融合 2026 知识库全部细节铁律！")


if __name__ == "__main__":
    run_agent3_v25_validation()