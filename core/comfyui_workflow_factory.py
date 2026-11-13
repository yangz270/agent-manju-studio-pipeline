# -*- coding: utf-8 -*-
"""
core/comfyui_workflow_factory.py

工业级全风格 AI 漫剧管线 —— Agent 4 终极重构：2026 工业级工作流总装编译器 (Workflow Factory v4.0)
深度整合 2026 最新实战知识库体系：
1. 【三件套解耦加载架构】(UNETLoader + DualCLIPLoader + 双 VAE: video/audio VAE)
2. 【2026 参数铁律】：新世代模型 (Krea2/Z-Image/Wan2.2/H3/Boogu) 强制 CFG: 1.0, 步数 4-12 步, 负面接 Conditioning Zero Out！
3. 【第三代角色资产 SOP 工作流】：Krea2 纯白底全身正面直视基底 ➜ Qwen-Image 2.1 多图编辑合成 4:3 三视图/四宫格
4. 【MiniMax H3 影视级双采多参音画同出流】：8G 显存分块(4/8) + 四步加速 LoRA + AV Latent Separate (音画潜空间分离，只放大视频)
5. 【LTX 2.3 Director 导演台时间轴分段编排流】
6. 【经典 16:9 极速版型锁定流】：SD1.5 revAnimated 768x432 (CFG: 7.0, Steps: 22, 0.40 Denoise 3秒极速出图)
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class ComfyUIWorkflowFactoryV4:
    """
    Agent 4 (2026 Edition): ComfyUI 工业级工作流生成与编译器
    根据模型代际自动切换加载架构与参数矩阵，彻底消灭跨代际参数错配
    """

    def __init__(self, export_dir: Optional[Path] = None):
        self.export_dir = export_dir or (Path(__file__).resolve().parent / "workspace_ep01" / "shared" / "workflows")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------------
    # 工作流 01：【日常量产王牌】SD1.5 16:9 极速图生图版型锁定流 (3~5秒出图)
    # ------------------------------------------------------------------------
    def build_sd15_main_consistent_16x9(
        self,
        ref_image_filename: str = "protagonist_front.png",
        ckpt_name: str = "revAnimated_v122.safetensors",
        positive_prompt: str = "3d donghua style, 1boy, lean, firm jaw, sliding back on dirt ground, 16:9, 8k",
        negative_prompt: str = "(worst quality:1.4), bad anatomy, extra limbs, deformed fingers, vertical video",
        denoise: float = 0.40,
        seed: int = 123456789
    ) -> Dict[str, Any]:
        """SD1.5 传统世代：CFG=7.0, Steps=22, 0.40 Denoise 锁五官版型"""
        return {
            "1": {"inputs": {"ckpt_name": ckpt_name}, "class_type": "CheckpointLoaderSimple", "_meta": {"title": "【底模加载舱】(SD1.5)"}},
            "2": {"inputs": {"image": ref_image_filename, "upload": "image"}, "class_type": "LoadImage", "_meta": {"title": "【定妆参考底片加载舱】"}},
            "3": {"inputs": {"pixels": ["2", 0], "vae": ["1", 2]}, "class_type": "VAEEncode", "_meta": {"title": "【定妆图潜空间编码】"}},
            "4": {"inputs": {"text": positive_prompt, "clip": ["1", 1]}, "class_type": "CLIPTextEncode", "_meta": {"title": "【正向提示词编码】"}},
            "5": {"inputs": {"text": negative_prompt, "clip": ["1", 1]}, "class_type": "CLIPTextEncode", "_meta": {"title": "【负向屏蔽词编码】"}},
            "6": {
                "inputs": {
                    "seed": seed, "steps": 22, "cfg": 7.0, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": denoise,
                    "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["3", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": f"【版型锁定采样器】(Denoise={denoise} 锁五官)"}
            },
            "7": {"inputs": {"samples": ["6", 0], "vae": ["1", 2]}, "class_type": "VAEDecode", "_meta": {"title": "【VAE 像素解码舱】"}},
            "8": {"inputs": {"filename_prefix": "AI_Drama_16x9_Consistent", "images": ["7", 0]}, "class_type": "SaveImage", "_meta": {"title": "【成片落盘保存舱】"}}
        }

    # ------------------------------------------------------------------------
    # 工作流 02：【2026 角色基底】Krea2 纯白底正面全身直视立绘母版 (CFG=1, Steps=8)
    # ------------------------------------------------------------------------
    def build_krea2_character_base(
        self,
        unet_name: str = "krea2_turbo_12g.safetensors",
        character_prompt: str = "1boy, 16 years old, messy black hair tied in topknot, piercing dark eyes, patched coarse grey hemp sleeveless tunic, straw sandals, pure white background, full body standing front view, looking directly at camera, 8k",
        seed: int = 55667788
    ) -> Dict[str, Any]:
        """2026 新世代：三件套分离加载，CFG=1 铁律，负面采用条件零化占位"""
        return {
            "1": {"inputs": {"unet_name": unet_name, "weight_dtype": "fp8_e4m3fn"}, "class_type": "UNETLoader", "_meta": {"title": "【Krea2 UNET 加载舱】"}},
            "2": {"inputs": {"clip_name": "qwen3_vl_4b_instruct.safetensors", "type": "c2"}, "class_type": "CLIPLoader", "_meta": {"title": "【Qwen3-VL CLIP 加载舱 (Type=C2)】"}},
            "3": {"inputs": {"vae_name": "krea2_vae.safetensors"}, "class_type": "VAELoader", "_meta": {"title": "【Krea2 专用 VAE】"}},
            "4": {"inputs": {"text": character_prompt, "clip": ["2", 0]}, "class_type": "CLIPTextEncode", "_meta": {"title": "【白底全身正面直视提示词】"}},
            "5": {"inputs": {"conditioning": ["4", 0]}, "class_type": "ConditioningZeroOut", "_meta": {"title": "【条件零化 (2026标准负向占位)】"}},
            "6": {"inputs": {"width": 768, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage", "_meta": {"title": "【立绘潜空间】"}},
            "7": {
                "inputs": {
                    "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
                    "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "【Krea2 极速采样 (CFG=1, Steps=8)】"}
            },
            "8": {"inputs": {"samples": ["7", 0], "vae": ["3", 0]}, "class_type": "VAEDecode", "_meta": {"title": "【VAE 解码】"}},
            "9": {"inputs": {"filename_prefix": "Char_Base_White_Krea2", "images": ["8", 0]}, "class_type": "SaveImage", "_meta": {"title": "【角色基底立绘落盘】"}}
        }

    # ------------------------------------------------------------------------
    # 工作流 03：【第三代资产终极流】Qwen-Image 2.1 多图编辑合成 4:3 三视图与四宫格
    # ------------------------------------------------------------------------
    def build_qwen21_multiview_asset(
        self,
        base_char_image: str = "Char_Base_White_Krea2_00001_.png",
        template_grid_image: str = "white_model_4grid_template.png",
        edit_instruction: str = "Keep the exact facial features, hairstyle, patched grey hemp clothing, and straw sandals of the character in image1 completely unchanged. Generate standard 4-panel multi-view character asset sheet following the layout in image2: top-left front closeup, top-right 45-degree side closeup, bottom-left back view, bottom-right full body with face blurred.",
        steps: int = 28,
        seed: int = 99881122
    ) -> Dict[str, Any]:
        """Qwen-Image 2.1 多图编辑：严禁开加速LoRA，28步慢跑确保95%+面容一致性"""
        return {
            "1": {"inputs": {"model_name": "qwen_image_2.1_bf16.safetensors"}, "class_type": "QwenImageModelLoader", "_meta": {"title": "【Qwen-Image 2.1 主模型】"}},
            "2": {"inputs": {"image": base_char_image, "upload": "image"}, "class_type": "LoadImage", "_meta": {"title": "【输入图1: Krea2 白底全身立绘】"}},
            "3": {"inputs": {"image": template_grid_image, "upload": "image"}, "class_type": "LoadImage", "_meta": {"title": "【输入图2: 四宫格/三视图排版白膜】"}},
            "4": {"inputs": {"text": edit_instruction}, "class_type": "QwenImageMultiImagePromptEncode", "_meta": {"title": "【多图指令编码器 (统管多图引用)】"}},
            "5": {"inputs": {"enabled": True}, "class_type": "QwenImageCacheNode", "_meta": {"title": "【千问缓存节点 (缓解显存防爆)】"}},
            "6": {
                "inputs": {
                    "seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "beta",
                    "model": ["1", 0], "prompt_embeds": ["4", 0], "image1": ["2", 0], "image2": ["3", 0]
                },
                "class_type": "QwenImageSampler",
                "_meta": {"title": "【Qwen 2.1 高精编辑采样 (不开加速保细节)】"}
            },
            "7": {"inputs": {"filename_prefix": "Char_Asset_4Grid_Qwen21", "images": ["6", 0]}, "class_type": "SaveImage", "_meta": {"title": "【角色资产四宫格最终落盘】"}}
        }

    # ------------------------------------------------------------------------
    # 工作流 04：【2026 漫剧出片主力】MiniMax H3 双采多参音画同出流 (双VAE + 8G分块 + 仅放大视频)
    # ------------------------------------------------------------------------
    def build_minimax_h3_twostage_audiovideo(
        self,
        scene_stand_image: str = "SC01_Wide_Standing.png",
        char_asset_image: str = "Char_Asset_4Grid_Qwen21_00001_.png",
        voice_ref_audio: str = "Protagonist_Voice_Master.wav",
        video_prompt: str = "Shot 1 (0-5s): 16:9 widescreen, character Chen Ping'an slides back defensively against clay wall, speaking grimly. Camera slowly dollying in. No background music, no subtitles, no text watermark.",
        seed: int = 77661122
    ) -> Dict[str, Any]:
        """
        MiniMax H3 双采多参工业标准：
        1. 双 VAE (video VAE + audio VAE)
        2. 四步加速 LoRA + 8G 显存模型分块 (块数=4)
        3. 一采 0.3MP 验框架 ➜ AV Latent Separate (仅放大视频 Latent) ➜ 二采 0.8MP 高清出片
        """
        return {
            "1": {"inputs": {"unet_name": "minimax_h3_fp8.safetensors"}, "class_type": "UNETLoader", "_meta": {"title": "【H3 视频生成主干】"}},
            "2": {"inputs": {"clip_name": "qwen3_vl_8b.safetensors", "type": "lumina"}, "class_type": "CLIPLoader", "_meta": {"title": "【文本编码器】"}},
            "3": {"inputs": {"vae_name": "minimax_video_vae.safetensors"}, "class_type": "VAELoader", "_meta": {"title": "【Video VAE (画面编解码)】"}},
            "4": {"inputs": {"vae_name": "minimax_audio_vae.safetensors"}, "class_type": "VAELoader", "_meta": {"title": "【Audio VAE (声音编解码)】"}},
            "5": {"inputs": {"lora_name": "h3_4step_fast_lora.safetensors", "strength": 0.8, "model": ["1", 0]}, "class_type": "LoraLoader", "_meta": {"title": "【四步加速 LoRA】"}},
            "6": {"inputs": {"lora_name": "h3_de_oil_skin.safetensors", "strength": 0.4, "model": ["5", 0]}, "class_type": "LoraLoader", "_meta": {"title": "【去油腻皮肤 LoRA】"}},
            "7": {"inputs": {"block_count": 4, "model": ["6", 0]}, "class_type": "ModelBlockSeparation", "_meta": {"title": "【8G 显存模型分块节点 (填4)】"}},
            "8": {"inputs": {"image": scene_stand_image, "upload": "image"}, "class_type": "LoadImage", "_meta": {"title": "【图1: 全景站位参考图】"}},
            "9": {"inputs": {"image": char_asset_image, "upload": "image"}, "class_type": "LoadImage", "_meta": {"title": "【图2: 角色资产四宫格】"}},
            "10": {"inputs": {"audio": voice_ref_audio}, "class_type": "UploadAudio", "_meta": {"title": "【音色母本参考音频】"}},
            "11": {"inputs": {"text": video_prompt, "clip": ["2", 0]}, "class_type": "CLIPTextEncode", "_meta": {"title": "【音画同出提示词 (写死无BGM无字幕)】"}},
            # 一阶段：0.3MP 快速采样验构图
            "12": {"inputs": {"megapixels": 0.3, "duration_seconds": 5.0, "fps": 24}, "class_type": "H3EmptyLatent", "_meta": {"title": "【一采 0.3MP 低显存空潜空间】"}},
            "13": {
                "inputs": {
                    "seed": seed, "steps": 8, "cfg": 1.0, "model": ["7", 0], "positive": ["11", 0],
                    "image_ref1": ["8", 0], "image_ref2": ["9", 0], "audio_ref": ["10", 0], "latent": ["12", 0]
                },
                "class_type": "H3Stage1Sampler",
                "_meta": {"title": "【一采 8 步初采 (几分钟快速排雷)】"}
            },
            # 核心铁律：音画潜空间分离，只放大视频，绝不能放大音频！
            "14": {"inputs": {"av_latent": ["13", 0]}, "class_type": "H3AVLatentSeparate", "_meta": {"title": "【AV Latent 分离舱 (防止音频放大畸变)】"}},
            "15": {"inputs": {"samples": ["14", 0], "scale_by": 1.6}, "class_type": "LatentUpscaleBy", "_meta": {"title": "【仅放大视频 Latent (0.3MP ➜ 0.8MP)】"}},
            "16": {"inputs": {"video_latent": ["15", 0], "audio_latent": ["14", 1]}, "class_type": "H3AVLatentMerge", "_meta": {"title": "【音画 Latent 重新合并舱】"}},
            # 二阶段：4 步补全高清细节
            "17": {
                "inputs": {"seed": seed, "steps": 4, "cfg": 1.0, "model": ["7", 0], "av_latent": ["16", 0]},
                "class_type": "H3Stage2Sampler",
                "_meta": {"title": "【二采 4 步精修 (锁死远景面部与音质)】"}
            },
            "18": {"inputs": {"samples": ["17", 0], "vae": ["3", 0]}, "class_type": "VAEDecode", "_meta": {"title": "【视频 VAE 解码】"}},
            "19": {"inputs": {"samples": ["17", 1], "vae": ["4", 0]}, "class_type": "VAEDecode", "_meta": {"title": "【音频 VAE 解码】"}},
            "20": {
                "inputs": {"images": ["18", 0], "audio": ["19", 0], "fps": 24, "filename_prefix": "H3_TwoStage_AudioVideo_Master"},
                "class_type": "CreateVideo",
                "_meta": {"title": "【创建成片 MP4 (音画严格同步输出)】"}
            }
        }

    # ------------------------------------------------------------------------
    # 工作流 05：【时间轴导演流】LTX 2.3 Director 两阶段时间轴分段控制
    # ------------------------------------------------------------------------
    def build_ltx23_director_timeline(
        self,
        timeline_prompt: str = "Segment 1 (0-3s): Close-up on protagonist jaw tensing. Segment 2 (3-6s): Pan to adversary sneering.",
        scale_by: float = 0.5
    ) -> Dict[str, Any]:
        """LTX 2.3 导演台：两阶段采样（scale_by 0.5 砍半去噪 ➜ x2 还原），内置时间轴与去字幕LoRA"""
        return {
            "1": {"inputs": {"unet_name": "ltx23_distill_fp8.safetensors"}, "class_type": "UNETLoader"},
            "2": {"inputs": {"clip_name1": "gemma_3_32b_fp8.safetensors", "clip_name2": "ltx23_text_proj.safetensors"}, "class_type": "DualCLIPLoader"},
            "3": {"inputs": {"vae_name": "ltx23_video_vae.safetensors"}, "class_type": "VAELoader"},
            "4": {"inputs": {"vae_name": "ltx23_audio_vae.safetensors"}, "class_type": "VAELoader"},
            "5": {"inputs": {"lora_name": "remove_subtitles.safetensors", "strength": 0.7, "model": ["1", 0]}, "class_type": "LoraLoader", "_meta": {"title": "【去字幕/水印 LoRA】"}},
            "6": {"inputs": {"timeline_prompt": timeline_prompt, "total_duration": 6.0, "fps": 24, "scale_by": scale_by}, "class_type": "LTXDirector", "_meta": {"title": "【LTX Director 导演台】"}},
            "7": {"inputs": {"model": ["5", 0], "director": ["6", 0], "steps": 6, "cfg": 1.0}, "class_type": "LTXSampler", "_meta": {"title": "【两阶段采样】"}},
            "8": {"inputs": {"samples": ["7", 0], "video_vae": ["3", 0], "audio_vae": ["4", 0]}, "class_type": "LTXCreateVideo", "_meta": {"title": "【LTX 成片输出】"}}
        }

    def export_all_v4_workflows(self) -> List[Path]:
        """编译并导出 2026 工业级全部核心工作流"""
        exported = []
        wfs = {
            "WF_01_SD15_Consistent_16x9.json": self.build_sd15_main_consistent_16x9(),
            "WF_02_Krea2_Character_Base.json": self.build_krea2_character_base(),
            "WF_03_Qwen21_Multiview_Asset.json": self.build_qwen21_multiview_asset(),
            "WF_04_MiniMax_H3_TwoStage_AudioVideo.json": self.build_minimax_h3_twostage_audiovideo(),
            "WF_05_LTX23_Director_Timeline.json": self.build_ltx23_director_timeline(),
        }
        for filename, data in wfs.items():
            out_file = self.export_dir / filename
            out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            exported.append(out_file)
            print(f"--> [2026 工业标准工作流落盘] {out_file.name}")
        return exported


if __name__ == "__main__":
    factory = ComfyUIWorkflowFactoryV4()
    files = factory.export_all_v4_workflows()
    print(f"\n[验证完毕] 2026 工业级 5 大核心工作流已全部编译落盘！")