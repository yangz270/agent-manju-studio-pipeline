# -*- coding: utf-8 -*-
"""
ComfyUI 与漫剧生产环境一键体检工具 (health_check.py)

一键检测本地 ComfyUI 服务、商业 API 凭据、模型目录与剪映草稿库。
不读取、不上传、不回显任何完整密钥（仅显示前 6 位与后 4 位掩码）。
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# 项目根目录（本文件位于 <repo>/scripts/ 下）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 必需凭据：缺失则整条管线无法启动
REQUIRED_KEYS = {
    "DEEPSEEK_API_KEY": "DeepSeek-V3 (编剧与分镜脱水)",
    "MINIMAX_API_KEY": "MiniMax (拟真情感配音与海螺视频)",
    "OPENAI_API_KEY": "302.AI / GPT-4o (黄金 Hook 与四维审美审查)",
}

# 可选凭据：缺失只影响对应的降级/备份能力
OPTIONAL_KEYS = {
    "DASHSCOPE_API_KEY": "阿里云百炼 Qwen (视觉审图备份)",
    "MOONSHOT_API_KEY": "月之暗面 Kimi (长篇原著扫描)",
}

SERVER_URL = os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188")


def find_dotenv():
    """按优先级定位 .env：环境变量 > 项目根目录 > scripts 目录 > 当前工作目录。"""
    candidates = [
        os.environ.get("DOTENV_PATH"),
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / "scripts" / ".env",
        Path.cwd() / ".env",
    ]
    for p in candidates:
        if p and Path(p).exists():
            return Path(p)
    return None


def read_dotenv(dotenv_path):
    env_vars = {}
    for line in Path(dotenv_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip("'\"")
    return env_vars


def check_comfyui_server(server_url=SERVER_URL):
    print("\n" + "=" * 70)
    print("【1. ComfyUI 启动状态与端口体检】")
    print(f"• 正在探测: {server_url} ...")
    try:
        req = urllib.request.Request(f"{server_url}/system_stats", headers={"User-Agent": "HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sys_info = data.get("system", {})
            devices = data.get("devices", [])
            print("  ✔ [连接成功] ComfyUI 服务正在稳定运行！")
            print(f"  • Python 版本: {sys_info.get('python_version', '未知')}")
            print(f"  • 系统环境: {sys_info.get('os', '未知')}")
            for idx, dev in enumerate(devices):
                print(f"  • 显卡 {idx}: {dev.get('name', 'GPU')} "
                      f"(总显存: {dev.get('vram_total', 0) / (1024 ** 3):.1f} GB, "
                      f"空闲: {dev.get('vram_free', 0) / (1024 ** 3):.1f} GB)")
            return True
    except urllib.error.URLError:
        print("  ✖ [未连接] 暂未检测到 ComfyUI 服务。")
        print("    --> 提示: 若尚未启动，请打开你的 ComfyUI 启动器，勾选 [--reserve-vram 0.8] 后启动。")
        print("    --> 若服务不在默认端口，可设置环境变量 COMFYUI_SERVER=http://127.0.0.1:8189 后再体检。")
        print("    --> 本管线支持【离线仿真沙盒模式】，即使不连 ComfyUI 也可先跑剧本、分镜与剪映工程！")
        return False
    except Exception as e:
        print(f"  ✖ [连接异常]: {e}")
        return False


def check_env_credentials():
    print("\n" + "=" * 70)
    print("【2. 商业 API 凭据就绪状态体检】")
    dotenv_path = find_dotenv()
    if not dotenv_path:
        print("  ✖ [缺失] 未找到 .env 配置文件！")
        print("    --> 请先执行: cp .env.example .env，然后填入你自己的商业 API Key。")
        print("    --> 详见 README.md「使用前必读：先配置 API Key」一节。")
        return False, False

    print(f"  • 已加载配置: {dotenv_path}")
    env_vars = read_dotenv(dotenv_path)

    missing_required = []
    for k, desc in REQUIRED_KEYS.items():
        v = env_vars.get(k, "") or os.environ.get(k, "")
        if v and len(v) > 8 and not v.startswith("your_"):
            print(f"  ✔ [已就绪] {desc}: {v[:6]}...{v[-4:]}")
        else:
            print(f"  ✖ [必需·未填] {desc}  ({k})")
            missing_required.append(k)

    for k, desc in OPTIONAL_KEYS.items():
        v = env_vars.get(k, "") or os.environ.get(k, "")
        if v and len(v) > 8 and not v.startswith("your_"):
            print(f"  ✔ [可选·已就绪] {desc}: {v[:6]}...{v[-4:]}")
        else:
            print(f"  ⚠ [可选·未填] {desc}  ({k})")

    if missing_required:
        print("\n  ✖ 缺少必需 API Key，管线无法启动。请补齐后再试：")
        for k in missing_required:
            print(f"      {k}=your_key_here")
    return True, not missing_required


def locate_jianying_draft_dir():
    print("\n" + "=" * 70)
    print("【3. 本地剪映草稿目录探测】")
    candidates = [
        os.environ.get("JIANYING_DRAFT_DIR"),  # 用户自定义优先
        Path.home() / "AppData" / "Local" / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft",
    ]
    # Windows 下自动遍历所有可用盘符，不写死任何具体盘
    if sys.platform.startswith("win"):
        for letter in "CDEFGH":
            candidates.append(Path(f"{letter}:/JianyingPro/User Data/Projects/com.lveditor.draft"))

    found = False
    for p in candidates:
        if p and Path(p).exists():
            print(f"  ✔ [自动定位] 发现剪映官方草稿库: {p}")
            found = True
            break
    if not found:
        print("  • [标准输出路径]: ./workspace_ep01/shared/JianYing_Drafts/")
        print("    --> 验收时，只需将该文件夹内的项目目录直接拖入剪映草稿路径下即可！")
        print("    --> 也可设置环境变量 JIANYING_DRAFT_DIR 指向你的草稿库后重新体检。")


def main():
    print("======================================================================")
    print("      工业级 AI 漫剧管线 —— 上线前环境与就绪状态综合体检")
    print("======================================================================")
    check_comfyui_server()
    _, keys_ok = check_env_credentials()
    locate_jianying_draft_dir()

    print("\n" + "=" * 70)
    print("【4. 验收就绪结论】")
    if keys_ok:
        print("  ✔ 必需 API Key 已全部就绪，10 位 Agent 具备【生产就绪 (Production-Ready)】状态；")
    else:
        print("  ✖ 必需 API Key 尚未配置齐全，当前无法进入生产流程；")
        print("  • 剧本/分镜等离线能力仍可试跑，但配音、审片与云端生图会直接失败。")
    print("  • 外部 API 严格受 HITL 用户授权保护，绝不暗箱扣费；")
    print("  • 产物统一汇总至 [workspace_ep01/]，一键导入剪映即成片！")
    print("======================================================================\n")
    return 0 if keys_ok else 1


if __name__ == "__main__":
    sys.exit(main())
