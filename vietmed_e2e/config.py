# -*- coding: utf-8 -*-
"""
vietmed_e2e/config.py
Cấu hình tập trung cho toàn bộ hệ thống VietMed E2E Pipeline:
Profile Generation + Dialogue Simulation + Fog of War.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thư mục gốc vietmed_e2e và workspace
E2E_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = E2E_DIR.parent

# Tải .env từ workspace
env_path = WORKSPACE_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it")

# Danh sách fallback Gemini models khi OpenRouter quá tải hoặc gặp lỗi
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-flash-latest",
]

# Đường dẫn tài liệu tri thức chuẩn (Ground Truth Knowledge)
KB_60_MD_PATH = WORKSPACE_ROOT / "danh-sach-60-benh-khong-cap-cuu.md"
KB_JSON_PATH = WORKSPACE_ROOT / "medical_knowledge_base.json"
CACHE_KB_JSON_PATH = E2E_DIR / "knowledge" / "60_diseases_kb.json"

# Đường dẫn thư mục đầu vào kịch bản (input-600)
INPUT_600_DIR = WORKSPACE_ROOT / "input-600"

# Đường dẫn thư mục đầu ra chuẩn (output-600)
OUTPUT_600_DIR = WORKSPACE_ROOT / "output-600"
OUTPUT_600_DIR.mkdir(parents=True, exist_ok=True)
