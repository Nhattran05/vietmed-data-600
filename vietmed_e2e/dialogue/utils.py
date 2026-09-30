# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/utils.py
Các hàm tiện ích cho Dialogue Simulation.
"""

import re
from typing import List
from vietmed_e2e.schemas.state import DialogueTurn

def format_history_for_prompt(turns: List[DialogueTurn], max_recent: int = 14) -> str:
    """Định dạng lịch sử hội thoại gần nhất cho prompt LLM."""
    if not turns:
        return "(Chưa có lượt thoại nào, buổi khám vừa bắt đầu.)"

    recent_turns = turns[-max_recent:] if len(turns) > max_recent else turns
    formatted = []
    for t in recent_turns:
        speaker_role = "physician" if t.get("speaker") in ["physician", "doctor"] else "patient"
        speaker_name = t.get("speaker_name", "Bác sĩ" if speaker_role == "physician" else "Bệnh nhân")
        text = t.get("text", "")
        formatted.append(f"{speaker_role} ({speaker_name}): {text}")

    return "\n".join(formatted)

def count_words(text: str) -> int:
    """Đếm số từ thực tế của lượt thoại."""
    cleaned = re.sub(r"\[\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\]", " ", text)
    cleaned = re.sub(r"-\s*\*\*(?:Bác sĩ|Bệnh nhân)[^*]*\*\*\:?", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(.*?\)", " ", cleaned)
    return len(cleaned.strip().split())
