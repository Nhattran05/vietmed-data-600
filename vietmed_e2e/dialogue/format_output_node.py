# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/format_output_node.py
Định dạng toàn bộ các lượt thoại thành Markdown hoàn chỉnh kèm Timestamp [mm:ss - mm:ss].
"""

from typing import Dict, Any
from vietmed_e2e.schemas.state import E2EState
from vietmed_e2e.sanitizer.dialogue_sanitizer import recalculate_timestamps_for_turns, sanitize_spoken_text

def format_output_node(state: E2EState) -> Dict[str, Any]:
    """
    Tạo văn bản Markdown chuẩn hóa lưu trữ hội thoại lâm sàng.
    """
    turns = state.get("polished_turns") or state.get("turns", [])
    disease_name = state.get("disease_name", "")
    duration_min = state.get("duration_minutes", 12)
    doc = state.get("doctor_profile", {}) or state.get("final_doctor", {})
    pat = state.get("patient_profile", {}) or state.get("final_patient", {})

    # Tái tính toán timestamp chuẩn xác
    final_turns = recalculate_timestamps_for_turns(turns, duration_minutes=duration_min)
    total_turns = len(final_turns)

    lines = []
    lines.append(f"# KỊCH BẢN ĐỐI THOẠI KHÁM BỆNH: {disease_name.upper()}")
    lines.append(f"> **Phương pháp sinh:** VietMed E2E Pipeline (Profile Gen + Fog of War + NoteChat)")
    lines.append(f"> **Bác sĩ:** {doc.get('name')} ({doc.get('style', doc.get('communication_tone', ''))})")
    addr_info = f", Địa chỉ: {pat.get('address')}" if pat.get('address') else ""
    lines.append(f"> **Bệnh nhân:** {pat.get('name')} ({pat.get('age')} tuổi{addr_info}, {pat.get('persona', pat.get('speaking_style', ''))})")
    lines.append(f"> **Tổng số lượt thoại:** {total_turns} lượt | **Thời lượng giả định:** ~{duration_min} phút")
    lines.append("\n---\n")

    for t in final_turns:
        ts = t.get("timestamp", "[00:00 - 00:00]")
        speaker_name = t.get("speaker_name", "Bác sĩ" if t.get("speaker") in ["physician", "doctor"] else "Bệnh nhân")
        clean_text = sanitize_spoken_text(t.get("text", ""))
        lines.append(f"- **`{ts}` {speaker_name}:** {clean_text}")

    final_md = "\n".join(lines)

    return {
        "final_markdown": final_md,
        "polished_turns": final_turns
    }
