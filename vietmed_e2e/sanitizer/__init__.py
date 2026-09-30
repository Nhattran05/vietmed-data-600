# -*- coding: utf-8 -*-
"""
vietmed_e2e/sanitizer
Làm sạch văn bản hội thoại cho TTS và chuẩn hóa lời thoại Bác sĩ / Bệnh nhân.
"""

from vietmed_e2e.sanitizer.dialogue_sanitizer import (
    sanitize_spoken_text,
    get_backchannel,
    get_doctor_backchannel,
    split_into_sentences,
    split_long_sentence_by_clauses,
    split_turn_into_two_halves,
    inject_patient_backchannels,
    recalculate_timestamps_for_turns,
    MANEUVER_REPLACEMENTS
)

__all__ = [
    "sanitize_spoken_text",
    "get_backchannel",
    "get_doctor_backchannel",
    "split_into_sentences",
    "split_long_sentence_by_clauses",
    "split_turn_into_two_halves",
    "inject_patient_backchannels",
    "recalculate_timestamps_for_turns",
    "MANEUVER_REPLACEMENTS"
]
