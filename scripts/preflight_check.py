# -*- coding: utf-8 -*-
"""
AI Donghua Studio —— 启动前 API Key 前置校验 (preflight_check.py)

这是整条管线的【硬闸口】：只要必需凭据缺失，就拒绝进入生产流程，
而不是等到跑了十分钟剧本、到配音那一步才 401 报错。

用法:
    python scripts/preflight_check.py              # 严格模式，缺任一必需 Key 即退出码 1
    python scripts/preflight_check.py --offline    # 离线模式，仅提示不阻断（做代码冒烟测试用）
    python scripts/preflight_check.py --verbose    # 显示脱敏后的 Key 指纹
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 必需：缺一不可，管线主链路会直接调用
REQUIRED_KEYS = {
    "DEEPSEEK_API_KEY": "DeepSeek-V3 · Agent 1/2 编剧与 Hook 审查",
    "MINIMAX_API_KEY": "MiniMax · Agent 6/7 拟真配音与海螺视频",
    "OPENAI_API_KEY": "302.AI / GPT-4o · Agent 5 四维审美质检",
}

# 可选：缺失只影响降级与备份路径
OPTIONAL_KEYS = {
    "DASHSCOPE_API_KEY": "阿里云百炼 Qwen-VL · 视觉审图备份",
    "MOONSHOT_API_KEY": "Moonshot Kimi · 长篇原著扫描",
}

BANNER = "=" * 74


def find_dotenv() -> Path | None:
    """定位 .env：显式环境变量 > 项目根目录 > scripts 目录 > 当前工作目录。"""
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


def load_env(dotenv_path: Path | None) -> None:
    """把 .env 读入 os.environ，但不覆盖已存在的真实环境变量。"""
    if not dotenv_path:
        return
    for line in Path(dotenv_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'\"")
        if v and not os.environ.get(k):
            os.environ[k] = v


def key_state(name: str) -> str:
    v = os.environ.get(name, "")
    if not v or len(v) <= 8 or v.startswith("your_"):
        return ""
    return v


def main() -> int:
    offline = "--offline" in sys.argv
    verbose = "--verbose" in sys.argv

    print(BANNER)
    print("   AI Donghua Studio —— 启动前 API Key 前置校验")
    print(BANNER)

    dotenv_path = find_dotenv()
    if dotenv_path:
        load_env(dotenv_path)
        print(f"[1/3] 已加载配置: {dotenv_path}")
    else:
        print("[1/3] 未找到 .env 配置文件")

    missing = []
    for name, desc in REQUIRED_KEYS.items():
        v = key_state(name)
        if v:
            shown = f"{v[:6]}...{v[-4:]}" if verbose else "已配置"
            print(f"  ✔ {name:<18} {shown:<16} {desc}")
        else:
            print(f"  ✖ {name:<18} {'缺失':<16} {desc}")
            missing.append(name)

    for name, desc in OPTIONAL_KEYS.items():
        v = key_state(name)
        mark = "✔" if v else "○"
        state = "已配置" if v else "未配置(可选)"
        print(f"  {mark} {name:<18} {state:<16} {desc}")

    if missing:
        print(BANNER)
        print("[2/3] 结论：缺少必需 API Key，管线拒绝启动。")
        print(BANNER)
        print("请按以下三步完成配置：")
        print("  1) 生成配置文件      cp .env.example .env")
        print("  2) 编辑 .env 填入真实密钥：")
        for name in missing:
            print(f"       {name}=你的密钥")
        print("  3) 重新执行本校验    python scripts/preflight_check.py")
        print("")
        print("各 Key 申请入口：")
        print("  DEEPSEEK_API_KEY   https://platform.deepseek.com/api_keys")
        print("  MINIMAX_API_KEY    https://platform.minimaxi.com/user-center/basic-information/interface-key")
        print("  OPENAI_API_KEY     https://302.ai （或任意 OpenAI 兼容网关，配 OPENAI_BASE_URL）")
        print(BANNER)
        if offline:
            print("⚠ 当前为 --offline 模式：仅提示，不阻断（仅用于代码冒烟测试）。")
            return 0
        return 1

    print(BANNER)
    print("[2/3] 结论：必需 API Key 全部就绪，允许进入生产流程。")
    print("[3/3] 下一步：python examples/run_pipeline_demo.py")
    print(BANNER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
