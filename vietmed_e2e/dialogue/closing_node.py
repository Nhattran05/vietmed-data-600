# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/closing_node.py
Closing Node:
Bác sĩ tổng kết dặn dò lần cuối, giải tỏa âu lo và bệnh nhân cảm ơn chào ra về.
"""

from typing import Dict, Any

from vietmed_e2e.schemas.state import E2EState, DialogueTurn
from vietmed_e2e.agents.llm_client import call_llm, extract_json_payload
from vietmed_e2e.sanitizer.dialogue_sanitizer import sanitize_spoken_text
from vietmed_e2e.dialogue.utils import format_history_for_prompt

def closing_node(state: E2EState) -> Dict[str, Any]:
    """
    Sinh 2 lượt kết thúc: Bác sĩ dặn dò ân cần, Bệnh nhân cảm ơn chào tạm biệt.
    """
    doc = state.get("doctor_profile", {}) or state.get("final_doctor", {})
    pat = state.get("patient_profile", {}) or state.get("final_patient", {})
    history_text = format_history_for_prompt(state.get("turns", []))
    turns_count = state.get("current_turn_count", 0)

    doc_name = doc.get("name", "Bác sĩ")
    pat_name = pat.get("name", "Bệnh nhân")

    prompt = f"""Bạn là Bác sĩ {doc_name}. Buổi khám bệnh đã hoàn thành đầy đủ.
Dưới đây là lịch sử buổi khám:
{history_text}

Hãy đưa ra 1-2 câu kết luận ngắn gọn, ân cần (tối đa không quá 25 từ), dặn bệnh nhân giữ gìn sức khỏe, uống thuốc đúng giờ và hẹn ngày tái khám. Tuyệt đối không tự xưng "bác sĩ" cứng nhắc, hãy xưng "tôi" hoặc dặn dò tự nhiên.
Trả về định dạng JSON duy nhất:
{{
  "text": "Lời dặn dò kết thúc của Bác sĩ",
  "is_parsed": true
}}"""

    raw_doc = call_llm(prompt)
    payload = extract_json_payload(raw_doc)
    doc_raw = payload.get("text", raw_doc) if payload else raw_doc
    doc_text = sanitize_spoken_text(doc_raw)

    turn_doc: DialogueTurn = {
        "turn_id": turns_count + 1,
        "speaker": "physician",
        "speaker_name": doc_name,
        "text": doc_text,
        "covered_item": "Kết luận và chào tạm biệt",
        "timestamp": None,
        "is_parsed": True
    }

    pat_reply = sanitize_spoken_text("Dạ vâng, cảm ơn bác sĩ nhiều lắm. Tôi về sẽ uống thuốc và tập luyện đúng như bác sĩ dặn. Chào bác sĩ tôi về ạ.")
    turn_pat: DialogueTurn = {
        "turn_id": turns_count + 2,
        "speaker": "patient",
        "speaker_name": pat_name,
        "text": pat_reply,
        "covered_item": "Chào ra về",
        "timestamp": None,
        "is_parsed": False
    }

    print(f"\n  [Closing] 🩺 {doc_name}: {doc_text}")
    print(f"  [Closing] 👤 {pat_name}: {pat_reply}", flush=True)

    return {
        "turns": [turn_doc, turn_pat],
        "current_turn_count": turns_count + 2,
        "is_finished": True
    }
