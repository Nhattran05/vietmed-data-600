# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/fog_gate_node.py
Node kiểm soát Fog of War (Sương mù thông tin):
Lọc và chỉ cung cấp cho Patient-LLM những thông tin đã được mở khóa theo tiến trình khám của Bác sĩ.
"""

from typing import Dict, Any, List, Set
from vietmed_e2e.schemas.state import E2EState

def _format_item(val: Any) -> str:
    """Chuyển đổi item sang chuỗi tóm tắt ngắn gọn."""
    if isinstance(val, dict):
        parts = []
        for k, v in val.items():
            if v and str(v).strip():
                parts.append(f"{v}")
        return ", ".join(parts)
    return str(val)

def fog_gate_node(state: E2EState) -> Dict[str, Any]:
    """
    Fog Gate Node:
    1. Kiểm tra completed_checklist và current_focus đối chiếu với reveal_sequence.
    2. Cập nhật tập hợp revealed_keys đã mở khóa.
    3. Tạo patient_visible_context cô đọng, chỉ chứa thông tin bệnh nhân đã được phép biết.
    4. Tạo hidden_topics_hint để nhắc nhở LLM ranh giới thông tin chưa được phép tiết lộ.
    """
    full_med_history = state.get("medical_history_data", {})
    completed_checklist = list(state.get("completed_checklist", []))
    current_focus = state.get("current_focus") or ""
    reveal_sequence = list(state.get("reveal_sequence", []))
    revealed_keys: Set[str] = set(state.get("revealed_keys", []))
    pat = state.get("final_patient", {}) or state.get("patient_profile", {})

    # 1. Luôn mở khóa thông tin ban đầu: patient_identity, chief_complaint, onset_duration, occupation
    revealed_keys.add("patient_identity")
    revealed_keys.add("chief_complaint")
    revealed_keys.add("onset_duration")
    revealed_keys.add("occupation")

    # 2. Mở khóa dựa trên reveal_sequence khớp với completed_checklist hoặc current_focus
    active_items = set(completed_checklist)
    if current_focus:
        active_items.add(current_focus)

    for item in reveal_sequence:
        chk_item = item.get("checklist_item", "")
        # Nếu mục checklist đã hoàn thành hoặc đang được bàn tới
        if any(chk_item == act or chk_item in act or act in chk_item for act in active_items):
            for k in item.get("reveal_keys", []):
                revealed_keys.add(k)

    # 3. Heuristic bổ trợ theo từ khóa trong câu hỏi / mục tiêu của bác sĩ
    focus_lower = current_focus.lower()
    completed_str = " ".join(completed_checklist).lower()
    combined_focus = f"{focus_lower} {completed_str}"

    if any(kw in combined_focus for kw in ["tiền sử", "bệnh nền", "mạn tính", "huyết áp", "tiểu đường"]):
        revealed_keys.add("chronic_conditions")

    if any(kw in combined_focus for kw in ["thuốc đang dùng", "đơn cũ", "uống thuốc gì", "hàng ngày"]):
        revealed_keys.add("current_medications")

    if any(kw in combined_focus for kw in ["tự chữa", "ở nhà", "xoa bóp", "dầu nóng", "dán cao", "thuốc giảm đau"]):
        revealed_keys.add("prior_pain_treatments")

    if any(kw in combined_focus for kw in ["mổ", "chấn thương", "ngã", "tai nạn", "phẫu thuật"]):
        revealed_keys.add("past_surgeries_trauma")

    if any(kw in combined_focus for kw in ["dị ứng", "kê đơn", "đơn thuốc", "uống thuốc", "nhóm thuốc"]):
        revealed_keys.add("allergies_intolerances")
        revealed_keys.add("current_medications")

    if any(kw in combined_focus for kw in ["thói quen", "sinh hoạt", "nghề nghiệp", "thể thao", "tư thế", "lao động"]):
        revealed_keys.add("lifestyle_risk_factors")

    if any(kw in combined_focus for kw in ["đã khám", "đi khám", "từng khám", "khám ở đâu", "bệnh viện", "phòng khám", "chẩn đoán trước", "điều trị trước", "đánh giá điều trị", "điều trị cũ", "phương pháp điều trị", "hiệu quả điều trị", "theo điều trị", "bao lâu", "phác đồ"]):
        revealed_keys.add("previous_medical_visits")

    # 4. Tạo patient_visible_context
    context_lines = []
    pat_full_name = pat.get("name", "Bệnh nhân")
    pat_display = pat.get("display_name", pat_full_name)
    pat_age = pat.get("age", 45)
    pat_addr = pat.get("address", "")

    context_lines.append(f"- Họ và tên của bạn: {pat_full_name} (Xưng hô: {pat_display})")
    context_lines.append(f"- Tuổi: {pat_age} tuổi")
    if pat_addr:
        context_lines.append(f"- Địa chỉ nơi ở: {pat_addr}")
    context_lines.append(f"- Lý do đến khám: {pat.get('chief_complaint', 'Đau nhức khó chịu')}")
    context_lines.append(f"- Thời gian bị đau: {pat.get('onset_duration', 'Gần đây')}")
    if pat.get("occupation"):
        context_lines.append(f"- Nghề nghiệp & sinh hoạt: {pat.get('occupation')}")

    # Tiền sử bệnh nền
    if "chronic_conditions" in revealed_keys:
        conds = full_med_history.get("chronic_conditions", [])
        if conds:
            cond_str = "; ".join(_format_item(c) for c in conds)
            context_lines.append(f"- Tiền sử bệnh nền: {cond_str}")
        else:
            context_lines.append("- Tiền sử bệnh nền: Không có bệnh mạn tính nào đáng kể")

    # Thuốc đang uống
    if "current_medications" in revealed_keys:
        meds = full_med_history.get("current_medications", [])
        if meds:
            med_str = "; ".join(_format_item(m) for m in meds)
            context_lines.append(f"- Thuốc đang uống hàng ngày: {med_str}")
        else:
            context_lines.append("- Thuốc đang uống hàng ngày: Không phải dùng thuốc duy trì")

    # Tự điều trị trước đó
    if "prior_pain_treatments" in revealed_keys:
        priors = full_med_history.get("prior_pain_treatments", [])
        if priors:
            prior_str = "; ".join(_format_item(p) for p in priors)
            context_lines.append(f"- Tự điều trị tại nhà trước khi đi khám: {prior_str}")
        else:
            context_lines.append("- Tự điều trị tại nhà: Chỉ nghỉ ngơi nhẹ, chưa dùng thuốc gì đặc biệt")

    # Chấn thương / mổ cũ
    if "past_surgeries_trauma" in revealed_keys:
        surgs = full_med_history.get("past_surgeries_trauma", [])
        if surgs:
            surg_str = "; ".join(_format_item(s) for s in surgs)
            context_lines.append(f"- Chấn thương / mổ cũ: {surg_str}")
        else:
            context_lines.append("- Chấn thương / mổ cũ: Chưa từng mổ hay bị tai nạn nghiêm trọng")

    # Dị ứng
    if "allergies_intolerances" in revealed_keys:
        allergies = full_med_history.get("allergies_intolerances", [])
        if allergies:
            alg_str = "; ".join(_format_item(a) for a in allergies)
            context_lines.append(f"- Dị ứng: {alg_str}")
        else:
            context_lines.append("- Dị ứng: Chưa từng bị dị ứng thuốc hay thức ăn")

    # Thói quen & tư thế lao động
    if "lifestyle_risk_factors" in revealed_keys:
        life = full_med_history.get("lifestyle_risk_factors", {})
        if isinstance(life, dict):
            posture = life.get("occupational_posture") or life.get("tobacco") or "Làm việc bình thường"
            context_lines.append(f"- Thói quen & tư thế làm việc: {posture}")

    # Lịch sử khám bệnh trước đó
    if "previous_medical_visits" in revealed_keys:
        prev_visits = full_med_history.get("previous_medical_visits")
        if prev_visits:
            if isinstance(prev_visits, list):
                vis_str = "; ".join(_format_item(v) for v in prev_visits)
            else:
                vis_str = str(prev_visits)
            context_lines.append(f"- Tiền sử đi khám BV/PK trước đó: {vis_str}")
        else:
            context_lines.append("- Tiền sử đi khám trước đó: Chưa từng đi khám ở đâu trước đây về tình trạng này")

    # Thang điểm đau VAS (0-10)
    if "pain_intensity_vas" in revealed_keys:
        context_lines.append("- Mức độ đau theo thang điểm: Lúc này khoảng 5 đến 6 điểm; lúc đau dữ dội nhất trong tháng qua (nhất là ban đêm) lên tới 8 hoặc 9 điểm.")

    # Đặc tính cảm giác đau DN4 / Likert
    if "pain_quality_dn4" in revealed_keys:
        context_lines.append("- Cảm giác đau chi tiết: Cảm giác nhức buốt, ê ẩm sâu trong khớp; cử động đột ngột thấy nhói buốt; không cảm thấy rát bỏng hay giật tê điện.")

    # Ảnh hưởng tâm lý & giấc ngủ
    if "mental_sleep_impact" in revealed_keys:
        context_lines.append("- Tác động tâm lý & giấc ngủ: Hay bị mất ngủ từng đợt về đêm vì đau nhức; người mệt mỏi, hơi lo lắng vì sợ không làm được việc nhà hay cơ quan.")

    patient_visible_context = "\n".join(context_lines)


    # 5. Gợi ý ranh giới thông tin chưa mở khóa
    hidden_hints = [
        "- Bạn KHÔNG BIẾT kết quả xét nghiệm, MRI, X-quang (đưa phim cho bác sĩ xem và chờ bác sĩ giải thích).",
        "- Bạn KHÔNG BIẾT tên chẩn đoán y khoa chính thức và TUYỆT ĐỐI KHÔNG dùng tên giải phẫu học chuyên sâu."
    ]
    if "allergies_intolerances" not in revealed_keys:
        hidden_hints.append("- Bạn CHƯA NÓI về dị ứng hoặc thuốc cũ trừ khi bác sĩ chủ động hỏi đến.")
    if "current_medications" not in revealed_keys:
        hidden_hints.append("- Bạn CHƯA TỰ KỂ về đơn thuốc cũ trừ khi bác sĩ hỏi tiền sử dùng thuốc.")
    if "previous_medical_visits" not in revealed_keys:
        hidden_hints.append("- Bạn CHƯA TỰ KỂ về việc từng đi khám ở bệnh viện/phòng khám trước đây trừ khi bác sĩ chủ động hỏi.")

    hidden_topics_hint = "\n".join(hidden_hints)

    return {
        "revealed_keys": list(revealed_keys),
        "patient_visible_context": patient_visible_context,
        "hidden_topics_hint": hidden_topics_hint
    }
