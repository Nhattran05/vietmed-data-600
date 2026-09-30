# -*- coding: utf-8 -*-
"""
vietmed_e2e/pipeline.py
LangGraph Orchestration Pipeline E2E:
Phase 1: Profile Generation (7 nodes)
  -> Bridge Node
Phase 2: Fog of War Planning (1 node)
Phase 3: Dialogue Simulation (Physician -> Checklist Update -> Fog Gate -> Patient -> Condition Check -> Closing -> Polish -> Format Output)
"""

import sys
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from vietmed_e2e.schemas.state import E2EState
from vietmed_e2e.knowledge.kb_loader import kb_instance

# Profile Gen Sub-Agents
from vietmed_e2e.agents.demographic_agent import generate_demographics
from vietmed_e2e.agents.clinical_context_agent import generate_clinical_context
from vietmed_e2e.agents.medical_history_agent import generate_medical_history
from vietmed_e2e.agents.persona_edge_case_agent import generate_persona_edge_case
from vietmed_e2e.agents.doctor_agent import generate_doctor_profile
from vietmed_e2e.agents.repair_agent import repair_profiles
from vietmed_e2e.validators.consistency_validator import validate_profiles

# Dialogue Simulation & Fog of War Nodes
from vietmed_e2e.dialogue.planning_node import planning_node
from vietmed_e2e.dialogue.physician_node import physician_node
from vietmed_e2e.dialogue.checklist_update_node import checklist_update_node, condition_check
from vietmed_e2e.dialogue.fog_gate_node import fog_gate_node
from vietmed_e2e.dialogue.patient_node import patient_node
from vietmed_e2e.dialogue.closing_node import closing_node
from vietmed_e2e.dialogue.polish_node import polish_node
from vietmed_e2e.dialogue.format_output_node import format_output_node
from vietmed_e2e.dialogue.form_filler_node import ground_truth_form_node

if hasattr(sys.stdout, "reconfigure"):

    sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# 1. PHASE 1: PROFILE GENERATION NODES
# ==============================================================================

def demographic_node(state: E2EState) -> Dict[str, Any]:
    kb_entry = state["kb_entry"]
    demo_data = generate_demographics(
        kb_entry=kb_entry,
        age=state.get("age"),
        gender=state.get("gender"),
        occupation=state.get("occupation"),
        patient_name=state.get("patient_name"),
        address=state.get("address"),
        force_confirm_identity=state.get("force_confirm_identity")
    )
    return {
        "demographic_data": demo_data,
        "age": demo_data.get("age", 45),
        "gender": demo_data.get("gender", "Nam"),
        "occupation": demo_data.get("occupation", "Lao động tự do"),
        "patient_name": demo_data.get("name", "Bệnh nhân"),
        "display_name": demo_data.get("display_name", "Bệnh nhân"),
        "address": demo_data.get("address", ""),
        "confirm_identity": demo_data.get("confirm_identity", True)
    }

def clinical_context_node(state: E2EState) -> Dict[str, Any]:
    kb_entry = state["kb_entry"]
    demo_data = state["demographic_data"]
    clinical_data = generate_clinical_context(kb_entry, demo_data)
    return {
        "clinical_context_data": clinical_data,
        "chief_complaint": clinical_data.get("chief_complaint", ""),
        "onset_duration": clinical_data.get("onset_duration", "")
    }

def medical_history_node(state: E2EState) -> Dict[str, Any]:
    kb_entry = state["kb_entry"]
    demo_data = state["demographic_data"]
    clinical_data = state["clinical_context_data"]
    force_prior = state.get("force_prior_visit")
    med_hist_data = generate_medical_history(kb_entry, demo_data, clinical_data, force_prior_visit=force_prior)
    return {
        "medical_history_data": med_hist_data
    }

def persona_node(state: E2EState) -> Dict[str, Any]:
    kb_entry = state["kb_entry"]
    demo_data = state["demographic_data"]
    clinical_data = state["clinical_context_data"]
    med_hist_data = state["medical_history_data"]
    sentiment = state.get("sentiment", "Positive")

    persona_res = generate_persona_edge_case(
        kb_entry=kb_entry,
        demographic_data=demo_data,
        clinical_context_data=clinical_data,
        medical_history_data=med_hist_data,
        sentiment=sentiment
    )

    return {
        "persona_data": {
            "speaking_style": persona_res.get("speaking_style", ""),
            "edge_case": persona_res.get("edge_case", "")
        }
    }

def doctor_node(state: E2EState) -> Dict[str, Any]:
    kb_entry = state["kb_entry"]
    patient_preview = {
        "name": state.get("patient_name"),
        "age": state.get("age"),
        "gender": state.get("gender"),
        "occupation": state.get("occupation"),
        "chief_complaint": state.get("chief_complaint")
    }
    doctor_res = generate_doctor_profile(
        kb_entry=kb_entry,
        patient_data=patient_preview,
        doctor_name=state.get("doctor_name"),
        gender=state.get("doctor_gender")
    )
    return {
        "doctor_data": doctor_res,
        "doctor_name": doctor_res.get("name", "Bác sĩ")
    }

def assembly_node(state: E2EState) -> Dict[str, Any]:
    demo = state["demographic_data"]
    clinical = state["clinical_context_data"]
    med_hist = state["medical_history_data"]
    persona = state["persona_data"]
    doctor = state["doctor_data"]

    final_patient = {
        "name": demo.get("name", ""),
        "display_name": demo.get("display_name", demo.get("name", "")),
        "gender": demo.get("gender", ""),
        "age": demo.get("age", 40),
        "occupation": demo.get("occupation", ""),
        "address": demo.get("address", ""),
        "confirm_identity": demo.get("confirm_identity", True),
        "chief_complaint": clinical.get("chief_complaint", ""),
        "onset_duration": clinical.get("onset_duration", ""),
        "medical_history": med_hist,
        "speaking_style": persona.get("speaking_style", ""),
        "edge_case": persona.get("edge_case", "")
    }

    final_doctor = {
        "name": doctor.get("name", ""),
        "display_name": doctor.get("display_name", doctor.get("name", "")),
        "gender": doctor.get("gender", ""),
        "age": doctor.get("age", 45),
        "seniority_level": doctor.get("seniority_level", ""),
        "speciality": doctor.get("speciality", ""),
        "communication_tone": doctor.get("communication_tone", "")
    }

    return {
        "final_patient": final_patient,
        "final_doctor": final_doctor
    }

def validator_node(state: E2EState) -> Dict[str, Any]:
    kb_entry = state["kb_entry"]
    final_patient = state["final_patient"]
    final_doctor = state["final_doctor"]

    validation_res = validate_profiles(
        kb_entry=kb_entry,
        patient_data=final_patient,
        doctor_data=final_doctor,
        deep_llm_check=False
    )

    return {
        "validation_passed": validation_res.is_valid,
        "validation_errors": validation_res.errors
    }

def repair_node(state: E2EState) -> Dict[str, Any]:
    kb_entry = state["kb_entry"]
    current_patient = state["final_patient"]
    current_doctor = state["final_doctor"]
    errors = state.get("validation_errors", [])
    repair_attempts = state.get("repair_attempts", 0) + 1

    repaired_patient, repaired_doctor = repair_profiles(
        kb_entry=kb_entry,
        patient_data=current_patient,
        doctor_data=current_doctor,
        validation_errors=errors
    )

    return {
        "final_patient": repaired_patient,
        "final_doctor": repaired_doctor,
        "repair_attempts": repair_attempts
    }

def should_repair_or_bridge(state: E2EState) -> Literal["repair_node", "bridge_to_dialogue_node"]:
    is_valid = state.get("validation_passed", False)
    repair_attempts = state.get("repair_attempts", 0)
    max_repairs = state.get("max_repairs", 2)

    if is_valid or repair_attempts >= max_repairs:
        return "bridge_to_dialogue_node"
    return "repair_node"

# ==============================================================================
# 2. BRIDGE: PHASE 1 -> PHASE 2 & 3
# ==============================================================================

def build_clinical_note_from_profile(kb_entry: Dict[str, Any], patient: Dict[str, Any], doctor: Dict[str, Any]) -> str:
    """Xây dựng hồ sơ lâm sàng Ground Truth từ kết quả sinh Profile Phase 1."""
    disease_name = kb_entry.get("name", "Bệnh lý")
    category = kb_entry.get("category", "Nội khoa")
    symptoms = kb_entry.get("symptoms", "")
    causes = kb_entry.get("causes", "")
    initial_care = kb_entry.get("initial_care", "")
    treatment = kb_entry.get("treatment", "")

    p_name = patient.get("name", "Bệnh nhân")
    p_display = patient.get("display_name", p_name)
    p_gender = patient.get("gender", "Nam")
    p_age = patient.get("age", 45)
    p_occ = patient.get("occupation", "Lao động")
    p_addr = patient.get("address", "Hà Nội")
    d_name = doctor.get("name", "Bác sĩ")
    d_display = doctor.get("display_name", d_name)

    chief = patient.get("chief_complaint", "")
    onset = patient.get("onset_duration", "")
    med_hist = patient.get("medical_history", {})

    note_lines = [
        f"BỆNH LÝ: {disease_name} (Chuyên khoa: {category})",
        f"BÁC SĨ PHỤ TRÁCH: {d_name} (Xưng hô: {d_display})",
        f"BỆNH NHÂN: {p_name} (Xưng hô: {p_display}), {p_gender}, {p_age} tuổi. Địa chỉ: {p_addr}. Nghề nghiệp: {p_occ}.",
        f"LÝ DO KHÁM & KHỞI PHÁT: {chief}. Thời gian kéo dài: {onset}.",
        f"TRIỆU CHỨNG LÂM SÀNG CỐT LÕI: {symptoms}",
        f"NGUYÊN NHÂN & CƠ CHẾ SINH BỆNH: {causes}",
        "TIỀN SỬ Y KHOA ĐÃ XÁC THỰC:"
    ]

    if isinstance(med_hist, dict):
        conds = med_hist.get("chronic_conditions", [])
        if conds:
            note_lines.append(f"- Bệnh nền: {conds}")
        meds = med_hist.get("current_medications", [])
        if meds:
            note_lines.append(f"- Thuốc đang điều trị: {meds}")
        priors = med_hist.get("prior_pain_treatments", [])
        if priors:
            note_lines.append(f"- Tự điều trị tại nhà: {priors}")
        surgs = med_hist.get("past_surgeries_trauma", [])
        if surgs:
            note_lines.append(f"- Chấn thương / phẫu thuật cũ: {surgs}")
        allergies = med_hist.get("allergies_intolerances", [])
        if allergies:
            note_lines.append(f"- Dị ứng: {allergies}")
        life = med_hist.get("lifestyle_risk_factors", {})
        if life:
            note_lines.append(f"- Thói quen & tư thế lao động: {life}")
        prev_visits = med_hist.get("previous_medical_visits")
        if prev_visits:
            note_lines.append(f"- Tiền sử đi khám tại BV/PK trước đó: {prev_visits}")
        else:
            note_lines.append("- Tiền sử đi khám trước đó: Chưa từng đi khám BV/PK nào trước đây về triệu chứng này")

    note_lines.append(f"XỬ TRÍ BAN ĐẦU & CẬN LÂM SÀNG: {initial_care}")
    note_lines.append(f"HƯỚNG ĐIỀU TRỊ & PHÁC ĐỒ CHUẨN: {treatment}")

    return "\n".join(note_lines)

def bridge_to_dialogue_node(state: E2EState) -> Dict[str, Any]:
    """Map profile output sang dialogue input format."""
    kb_entry = state.get("kb_entry", {})
    pat = state.get("final_patient", {})
    doc = state.get("final_doctor", {})

    # Nếu chưa có clinical_note, tự động build từ profile
    clinical_note = state.get("clinical_note")
    if not clinical_note:
        clinical_note = build_clinical_note_from_profile(kb_entry, pat, doc)

    return {
        "clinical_note": clinical_note,
        "disease_name": kb_entry.get("name", state.get("disease_name", "Bệnh lý")),
        "doctor_profile": {
            "name": doc.get("name", "Bác sĩ"),
            "display_name": doc.get("display_name", "Bác sĩ"),
            "gender": doc.get("gender", "Nam"),
            "age": doc.get("age", 45),
            "style": doc.get("communication_tone", "Ân cần, đĩnh đạc, gặng hỏi chi tiết và giải thích cặn kẽ")
        },
        "patient_profile": {
            "name": pat.get("name", "Bệnh nhân"),
            "display_name": pat.get("display_name", "Bệnh nhân"),
            "gender": pat.get("gender", "Nam"),
            "age": pat.get("age", 45),
            "occupation": pat.get("occupation", ""),
            "address": pat.get("address", ""),
            "confirm_identity": pat.get("confirm_identity", True),
            "persona": pat.get("speaking_style", "Mộc mạc, dân dã, dùng từ ngữ cảm giác thuần Việt")
        }
    }

# ==============================================================================
# 3. BUILD UNIFIED LANGGRAPH PIPELINE
# ==============================================================================

def build_vietmed_e2e_graph():
    """
    Xây dựng StateGraph hợp nhất cho toàn bộ hệ thống VietMed E2E.
    """
    workflow = StateGraph(E2EState)

    # 1. Phase 1 Nodes: Profile Generation
    workflow.add_node("demographic_node", demographic_node)
    workflow.add_node("clinical_context_node", clinical_context_node)
    workflow.add_node("medical_history_node", medical_history_node)
    workflow.add_node("persona_node", persona_node)
    workflow.add_node("doctor_node", doctor_node)
    workflow.add_node("assembly_node", assembly_node)
    workflow.add_node("validator_node", validator_node)
    workflow.add_node("repair_node", repair_node)

    # 2. Bridge Node
    workflow.add_node("bridge_to_dialogue_node", bridge_to_dialogue_node)

    # 3. Phase 2 & 3 Nodes: Fog of War + Dialogue Simulation
    workflow.add_node("planning_node", planning_node)
    workflow.add_node("physician_node", physician_node)
    workflow.add_node("checklist_update_node", checklist_update_node)
    workflow.add_node("fog_gate_node", fog_gate_node)
    workflow.add_node("patient_node", patient_node)
    workflow.add_node("closing_node", closing_node)
    workflow.add_node("polish_node", polish_node)
    workflow.add_node("format_output_node", format_output_node)
    workflow.add_node("ground_truth_form_node", ground_truth_form_node)

    # Edges - Phase 1
    workflow.add_edge(START, "demographic_node")
    workflow.add_edge("demographic_node", "clinical_context_node")
    workflow.add_edge("clinical_context_node", "medical_history_node")
    workflow.add_edge("medical_history_node", "persona_node")
    workflow.add_edge("persona_node", "doctor_node")
    workflow.add_edge("doctor_node", "assembly_node")
    workflow.add_edge("assembly_node", "validator_node")

    # Conditional Edge Phase 1 -> Repair / Bridge
    workflow.add_conditional_edges(
        "validator_node",
        should_repair_or_bridge,
        {
            "repair_node": "repair_node",
            "bridge_to_dialogue_node": "bridge_to_dialogue_node"
        }
    )
    workflow.add_edge("repair_node", "validator_node")

    # Bridge -> Phase 2 (Planning)
    workflow.add_edge("bridge_to_dialogue_node", "planning_node")

    # Phase 2 -> Phase 3 Loop
    workflow.add_edge("planning_node", "physician_node")
    workflow.add_edge("physician_node", "checklist_update_node")
    workflow.add_edge("checklist_update_node", "fog_gate_node")
    workflow.add_edge("fog_gate_node", "patient_node")

    # Conditional Edge from Patient -> Continue or Finish Roleplay
    workflow.add_conditional_edges(
        "patient_node",
        condition_check,
        {
            "continue_roleplay": "physician_node",
            "finish_roleplay": "closing_node"
        }
    )

    workflow.add_edge("closing_node", "polish_node")
    workflow.add_edge("polish_node", "format_output_node")
    workflow.add_edge("format_output_node", "ground_truth_form_node")
    workflow.add_edge("ground_truth_form_node", END)


    return workflow.compile()

# Khởi tạo instance pipeline sẵn sàng sử dụng
vietmed_e2e_pipeline = build_vietmed_e2e_graph()
