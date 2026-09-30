# -*- coding: utf-8 -*-
"""
vietmed_e2e/knowledge/kb_loader.py
Bộ nạp và tra cứu tri thức 60 bệnh từ:
  D:\\test STT\\danh-sach-60-benh-khong-cap-cuu.md
Hỗ trợ cache sang JSON tại data/knowledge_bases/60_diseases_kb.json.
"""

import os
import sys
import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional
from vietmed_e2e.config import KB_60_MD_PATH, KB_JSON_PATH, CACHE_KB_JSON_PATH

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def normalize_text(text: str) -> str:
    """Chuẩn hóa chuỗi tiếng Việt để so khớp không dấu và bỏ ký tự đặc biệt."""
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())

class DiseaseKnowledgeBase:
    def __init__(self):
        self.diseases_60: List[Dict[str, Any]] = []
        self.diseases_by_stt: Dict[int, Dict[str, Any]] = {}
        self.detailed_kb: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        # 1. Nạp từ Markdown gốc
        if not KB_60_MD_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy file nguồn KB: {KB_60_MD_PATH}")

        with open(KB_60_MD_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_category = "Chung"
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## "):
                current_category = line_str.replace("## ", "").split("(")[0].strip()
                continue

            if line_str.startswith("|") and not line_str.startswith("| #") and not line_str.startswith("|---"):
                parts = [p.strip() for p in line_str.split("|")[1:-1]]
                if len(parts) >= 5 and parts[0].isdigit():
                    stt = int(parts[0])
                    name = parts[1]
                    symptoms = parts[2]
                    causes = parts[3]
                    initial_care = parts[4]
                    treatment = parts[5] if len(parts) > 5 else ""

                    entry = {
                        "stt": stt,
                        "name": name,
                        "category": current_category,
                        "symptoms": symptoms,
                        "causes": causes,
                        "initial_care": initial_care,
                        "treatment": treatment,
                        "norm_name": normalize_text(name)
                    }
                    self.diseases_60.append(entry)
                    self.diseases_by_stt[stt] = entry

        # 2. Nạp thêm detailed KB nếu có
        if KB_JSON_PATH.exists():
            try:
                with open(KB_JSON_PATH, "r", encoding="utf-8") as f:
                    items = json.load(f)
                if isinstance(items, list):
                    for item in items:
                        norm = normalize_text(item.get("name", ""))
                        self.detailed_kb[norm] = item
            except Exception:
                pass

        # 3. Ghi cache JSON để các tiến trình khác tái sử dụng
        try:
            CACHE_KB_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_KB_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(self.diseases_60, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_disease(self, query: Any) -> Optional[Dict[str, Any]]:
        """
        Tra cứu bệnh theo STT (int: 1-60) hoặc Tên bệnh (str).
        """
        if isinstance(query, int):
            return self.diseases_by_stt.get(query)

        if isinstance(query, str) and query.strip().isdigit():
            return self.diseases_by_stt.get(int(query.strip()))

        norm_query = normalize_text(str(query))

        # So khớp chính xác hoặc chứa toàn bộ
        for d in self.diseases_60:
            if norm_query == d["norm_name"] or norm_query in d["norm_name"] or d["norm_name"] in norm_query:
                return self._enrich_entry(d)

        # So khớp theo từ khóa quan trọng
        query_words = set(norm_query.split())
        best_match = None
        max_overlap = 0
        for d in self.diseases_60:
            d_words = set(d["norm_name"].split())
            overlap = len(query_words.intersection(d_words))
            if overlap > max_overlap and overlap >= 2:
                max_overlap = overlap
                best_match = d

        if best_match:
            return self._enrich_entry(best_match)

        return None

    def _enrich_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        res = dict(entry)
        norm_name = entry["norm_name"]
        for k_norm, det in self.detailed_kb.items():
            if k_norm in norm_name or norm_name in k_norm:
                res["detailed_symptoms"] = det.get("clinical_symptoms", "")
                res["detailed_treatment"] = det.get("treatment_summary", "")
                res["diagnostic_criteria"] = det.get("diagnostic_criteria", "")
                res["source_doc"] = det.get("source", "")
                break
        return res

# Khởi tạo singleton
kb_instance = DiseaseKnowledgeBase()
