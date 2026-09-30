# -*- coding: utf-8 -*-
"""
vietmed_e2e/schemas/state.py
TypedDict State cho toàn bộ LangGraph E2E Pipeline:
Phase 1 (Profile Generation) -> Phase 2 (Fog of War) -> Phase 3 (Dialogue Simulation).
"""

import operator
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field

from vietmed_e2e.schemas.patient import PatientProfile
from vietmed_e2e.schemas.doctor import DoctorProfile
from vietmed_e2e.schemas.fog import RevealItem

# ==============================================================================
# 1. DIALOGUE TURN SCHEMA
# ==============================================================================

class DialogueTurn(TypedDict, total=False):
    turn_id: int
    speaker: str          # "physician" | "patient"
    speaker_name: str
    text: str
    covered_item: Optional[str]
    timestamp: Optional[str]
    is_parsed: bool

# ==============================================================================
# 2. METADATA SCHEMAS
# ==============================================================================

class ProfileMetadata(BaseModel):
    target_disease: str
    disease_stt: int
    speciality_group: str
    sentiment: str
    validation_status: str = Field("PENDING", description="Trạng thái kiểm định: PASSED, REPAIRED, FAILED")
    validation_errors: List[str] = Field(default_factory=list)
    repair_count: int = Field(0, description="Số lần sửa lỗi qua Repair Agent")
    source_reference: str

class ProfileGenerationOutput(BaseModel):
    patient: PatientProfile
    doctor: DoctorProfile
    metadata: ProfileMetadata

# ==============================================================================
# 3. UNIFIED E2E STATE
# ==============================================================================

class E2EState(TypedDict, total=False):
    # ===== PHASE 1: Profile Generation =====
    kb_entry: Dict[str, Any]
    disease_stt: int
    disease_name: str
    specialty_group: str
    sentiment: str                 # "Positive" | "Negative"
    scenario_index: int            # Kịch bản thứ mấy (1-10)
    force_prior_visit: Optional[bool]  # Ép buộc True/False hoặc None để roll ngẫu nhiên 60/40
    force_confirm_identity: Optional[bool] # Ép buộc Bác sĩ hỏi confirm danh tính (70/30)

    # Demographic & Context
    age: int
    gender: str
    occupation: str
    address: Optional[str]
    patient_name: str
    doctor_name: str
    doctor_gender: str
    chief_complaint: str
    onset_duration: str

    # Agent Raw Outputs
    demographic_data: Dict[str, Any]
    clinical_context_data: Dict[str, Any]
    medical_history_data: Dict[str, Any]
    persona_data: Dict[str, Any]
    doctor_data: Dict[str, Any]

    # Validation & Repair
    validation_passed: bool
    validation_errors: List[str]
    repair_attempts: int
    max_repairs: int

    # Final Assembled Profiles
    final_patient: Dict[str, Any]
    final_doctor: Dict[str, Any]
    final_metadata: Dict[str, Any]

    # ===== PHASE 2: Fog of War =====
    reveal_sequence: List[Dict[str, Any]]    # Ordered reveal mapping from Planning Module
    revealed_keys: List[str]                 # Currently unlocked keys
    patient_visible_context: str             # Filtered context for Patient-LLM
    hidden_topics_hint: str                  # Hint on boundaries for Patient-LLM

    # ===== PHASE 3: Dialogue Simulation =====
    clinical_note: str                       # Full ground truth (only for Physician)
    doctor_profile: Dict[str, Any]           # Mapped from final_doctor
    patient_profile: Dict[str, Any]          # Mapped from final_patient

    checklist: List[str]                     # Remaining clinical checklist
    completed_checklist: List[str]           # Completed items
    current_focus: Optional[str]             # Current target clinical item

    turns: Annotated[List[DialogueTurn], operator.add]
    polished_turns: Optional[List[DialogueTurn]]
    current_turn_count: int
    target_turns: int
    max_hard_limit: int
    duration_minutes: int
    is_finished: bool
    final_markdown: str
    ground_truth_form: Optional[Dict[str, Any]]

