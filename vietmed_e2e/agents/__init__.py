# -*- coding: utf-8 -*-
"""
vietmed_e2e/agents
Các Sub-Agents chuyên trách sinh Profile Bệnh nhân & Bác sĩ và LLM Client.
"""

from vietmed_e2e.agents.llm_client import (
    call_llm,
    call_llm_json,
    call_llm_text,
    extract_json,
    extract_json_payload,
    call_openrouter,
    call_gemini
)
from vietmed_e2e.agents.demographic_agent import generate_demographics
from vietmed_e2e.agents.clinical_context_agent import generate_clinical_context
from vietmed_e2e.agents.medical_history_agent import generate_medical_history
from vietmed_e2e.agents.persona_edge_case_agent import generate_persona_edge_case
from vietmed_e2e.agents.doctor_agent import generate_doctor_profile
from vietmed_e2e.agents.repair_agent import repair_profiles

__all__ = [
    "call_llm",
    "call_llm_json",
    "call_llm_text",
    "extract_json",
    "extract_json_payload",
    "call_openrouter",
    "call_gemini",
    "generate_demographics",
    "generate_clinical_context",
    "generate_medical_history",
    "generate_persona_edge_case",
    "generate_doctor_profile",
    "repair_profiles",
]
