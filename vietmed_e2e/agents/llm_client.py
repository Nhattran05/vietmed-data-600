# -*- coding: utf-8 -*-
"""
vietmed_e2e/agents/llm_client.py
Hàm gọi LLM dùng chung cho các Agents và Dialogue Simulation:
Ưu tiên OpenRouter (google/gemma-4-31b-it) theo yêu cầu, fallback sang Google Gemini nếu lỗi.
"""

import os
import sys
import re
import json
import time
import urllib.request
from typing import Dict, Any, Optional

from vietmed_e2e.config import (
    OPENROUTER_API_KEY,
    GOOGLE_API_KEY,
    DEFAULT_MODEL,
    GEMINI_MODELS,
    LLM_PROVIDER,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Khởi tạo Gemini client nếu có GOOGLE_API_KEY
_gemini_client = None
if GOOGLE_API_KEY:
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as ex:
        print(f"[LLM Client Warning] Không thể khởi tạo google.genai Client: {ex}")

def call_openrouter(
    prompt: str,
    system_prompt: str = "",
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_retries: int = 3
) -> str:
    """Gọi model qua OpenRouter API."""
    key = os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY chưa được cấu hình trong .env!")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Nhattran05/vietmed-data-600",
        "X-Title": "VietMed E2E Clinical Simulation Pipeline"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    data = json.dumps(payload).encode("utf-8")

    last_err = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=50) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                if "choices" in res_json and len(res_json["choices"]) > 0:
                    content = res_json["choices"][0]["message"]["content"]
                    if content:
                        return content.strip()
        except Exception as ex:
            last_err = ex
            print(f"  [OpenRouter Retry {attempt+1}] Gặp lỗi: {str(ex)[:100]}", flush=True)
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"OpenRouter gọi model {model} thất bại sau {max_retries} lần: {last_err}")

def call_gemini(
    prompt: str,
    system_prompt: str = "",
    max_retries: int = 2
) -> str:
    """Gọi Gemini với cơ chế retry và fallback qua các model khả dụng."""
    if not _gemini_client:
        raise RuntimeError("GOOGLE_API_KEY chưa được cấu hình hoặc google.genai client chưa sẵn sàng!")

    full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

    last_err = None
    for outer in range(2):
        for model_name in GEMINI_MODELS:
            for attempt in range(max_retries):
                try:
                    res = _gemini_client.models.generate_content(
                        model=model_name,
                        contents=full_prompt
                    )
                    if res and res.text:
                        return res.text.strip()
                except Exception as ex:
                    err_str = str(ex)
                    print(f"  [Gemini Warning] Model {model_name} (lần {attempt+1}) gặp lỗi: {err_str[:90]}", flush=True)
                    last_err = ex
                    if "429" in err_str or "404" in err_str:
                        break
                    time.sleep(1.0)
        if outer == 0:
            print("  [API Cooling] Đang tạm nghỉ 8s chờ giải phóng quota...", flush=True)
            time.sleep(8.0)

    raise RuntimeError(f"Tất cả các model Gemini đều thất bại: {last_err}")

def call_llm(
    prompt: str,
    system_prompt: str = "",
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_retries: int = 3
) -> str:
    """
    Hàm gọi LLM hợp nhất:
    Ưu tiên OpenRouter (google/gemma-4-31b-it), fallback sang Gemini nếu lỗi.
    """
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    if provider == "openrouter":
        try:
            return call_openrouter(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_retries=max_retries
            )
        except Exception as ex:
            print(f"  [LLM Fallback] OpenRouter lỗi: {ex}. Chuyển sang Gemini fallback...", flush=True)
            return call_gemini(prompt=prompt, system_prompt=system_prompt, max_retries=2)
    else:
        return call_gemini(prompt=prompt, system_prompt=system_prompt, max_retries=max_retries)

def extract_json(raw: str) -> Any:
    """Trích xuất JSON (dict hoặc list) từ phản hồi LLM an toàn và chuẩn xác."""
    if not raw:
        return {}
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        # Thử tìm object dict
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        # Thử tìm mảng list
        m_arr = re.search(r"\[[\s\S]*\]", raw)
        if m_arr:
            try:
                return json.loads(m_arr.group(0))
            except Exception:
                pass
    return {}

def extract_json_payload(raw: str) -> Optional[Dict[str, Any]]:
    """Trích xuất JSON dictionary payload từ chuỗi phản hồi của LLM."""
    res = extract_json(raw)
    if isinstance(res, dict):
        return res
    return None

def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5,
    model: str = DEFAULT_MODEL
) -> Any:
    """Gọi LLM và tự động bóc tách JSON."""
    raw = call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature
    )
    return extract_json(raw)

def call_llm_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5,
    model: str = DEFAULT_MODEL
) -> str:
    """Gọi LLM lấy văn bản thô."""
    return call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature
    )
