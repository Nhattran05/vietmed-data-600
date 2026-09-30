# -*- coding: utf-8 -*-
"""
src/validators/consistency_validator.py
Kiểm định tính nhất quán toàn diện giữa Hồ sơ Bệnh nhân, Hồ sơ Bác sĩ và Tri thức Chuẩn:
1. Clinical consistency: disease <-> symptoms <-> chief complaint (ngắn gọn, không văn nói)
2. Demographic consistency: age/gender/occupation <-> profile & disease
3. Medication consistency: chronic conditions <-> current medications
4. Treatment consistency: disease <-> prior pain treatments (grounded in KB initial care)
5. Temporal consistency: onset, duration, past surgery/trauma years <-> patient age
6. Strict formatting: Không chứa biểu tượng cảm xúc (emojis/icons)
"""

import re
import datetime
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field

from vietmed_e2e.agents.llm_client import call_llm_json

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

def _contains_emoji(text: str) -> bool:
    """Kiểm tra xem chuỗi có chứa icon/emoji không."""
    if not isinstance(text, str):
        return False
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA70-\U0001FAFF"  # Medical & other symbols
        "]+",
        flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))

def run_programmatic_checks(
    kb_entry: Dict[str, Any],
    patient_data: Dict[str, Any],
    doctor_data: Dict[str, Any]
) -> Tuple[List[str], List[str]]:
    """
    Kiểm tra nhanh bằng mã nguồn (Deterministic checks) - 0 latency:
    - Ràng buộc cấu trúc, độ tuổi, năm phẫu thuật, định dạng lý do khám, biểu tượng cảm xúc.
    """
    errors = []
    warnings = []
    current_year = datetime.datetime.now().year

    # 1. Kiểm tra Emoji/Icon trên toàn bộ dữ liệu (Yêu cầu nghiêm ngặt từ người dùng)
    def check_emojis_recursive(obj, path=""):
        if isinstance(obj, str):
            if _contains_emoji(obj):
                errors.append(f"Quy chuẩn thẩm mỹ bị vi phạm: Phát hiện icon/emoji tại trường '{path}'.")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                check_emojis_recursive(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                check_emojis_recursive(v, f"{path}[{i}]")

    check_emojis_recursive(patient_data, "patient")
    check_emojis_recursive(doctor_data, "doctor")

    # 2. Demographic consistency
    age = patient_data.get("age", 0)
    gender = patient_data.get("gender", "")
    occupation = patient_data.get("occupation", "")
    
    if not isinstance(age, int) or age <= 0 or age > 110:
        errors.append(f"Demographic error: Tuổi bệnh nhân ({age}) không hợp lệ (phải từ 1 đến 110).")
    
    if gender not in ["Nam", "Nữ"]:
        errors.append(f"Demographic error: Giới tính bệnh nhân ('{gender}') phải là 'Nam' hoặc 'Nữ'.")

    if not occupation or len(occupation.strip()) < 2:
        errors.append("Demographic error: Nghề nghiệp của bệnh nhân bị bỏ trống hoặc không rõ ràng.")

    # 3. Clinical context formatting (Lý do khám - chief_complaint)
    chief_complaint = patient_data.get("chief_complaint", "")
    if not chief_complaint:
        errors.append("Clinical error: Lý do khám (chief_complaint) không được để trống.")
    else:
        # Bắt buộc KHÔNG dùng văn nói hội thoại, từ cảm thán hoặc xưng hô với bác sĩ
        conversational_markers = [
            "trời ơi", "bác sĩ ơi", "thưa bác sĩ", "chết mất", "ối giời", "than ôi", "chào bác sĩ"
        ]
        cc_lower = chief_complaint.lower()
        for marker in conversational_markers:
            if marker in cc_lower:
                errors.append(
                    f"Clinical error: Lý do khám chứa văn nói/khẩu ngữ hội thoại ('{marker}'). "
                    "Yêu cầu chỉ ghi mô tả cảm giác thực thể ngắn gọn (ví dụ: 'Ngón chân cái sưng vù, đỏ, cảm giác nóng rát và đau khi chạm vào')."
                )
                break

    # 4. Medical history checks
    med_history = patient_data.get("medical_history", {})
    chronic_conditions = med_history.get("chronic_conditions", [])
    current_medications = med_history.get("current_medications", [])
    past_surgeries = med_history.get("past_surgeries_trauma", [])

    # Temporal consistency: Past surgery year vs patient age
    for item in past_surgeries:
        s_year = item.get("year")
        if s_year is not None and isinstance(s_year, int):
            if s_year > current_year:
                errors.append(f"Temporal error: Năm phẫu thuật/chấn thương ({s_year}) ở tương lai.")
            elif (current_year - s_year) > age:
                errors.append(f"Temporal error: Năm phẫu thuật/chấn thương ({s_year}) xảy ra trước khi bệnh nhân sinh ra (tuổi: {age}).")

    # Medication consistency: If chronic conditions have hypertension/diabetes, medication check
    if len(chronic_conditions) > 0:
        for cond in chronic_conditions:
            cond_name = cond.get("condition", "").lower()
            if "tăng huyết áp" in cond_name and not any("amlo" in m.get("name", "").lower() or "losar" in m.get("name", "").lower() or "huyết áp" in m.get("name", "").lower() or "coversyl" in m.get("name", "").lower() for m in current_medications):
                warnings.append(f"Medication warning: Bệnh nhân có tiền sử '{cond.get('condition')}' nhưng danh sách thuốc chưa thấy thuốc hạ áp tương ứng.")
            if "đái tháo đường" in cond_name and not any("metformin" in m.get("name", "").lower() or "glicla" in m.get("name", "").lower() or "tiểu đường" in m.get("name", "").lower() for m in current_medications):
                warnings.append(f"Medication warning: Bệnh nhân có tiền sử '{cond.get('condition')}' nhưng danh sách thuốc chưa thấy thuốc hạ đường huyết tương ứng.")

    # 5. Doctor Profile checks
    doc_age = doctor_data.get("age", 0)
    seniority = doctor_data.get("seniority_level", "")
    if not isinstance(doc_age, int) or doc_age < 24 or doc_age > 85:
        errors.append(f"Doctor error: Tuổi bác sĩ ({doc_age}) không hợp lệ (phải từ 24 đến 85).")

    if "trưởng khoa" in seniority.lower() or "chuyên khoa ii" in seniority.lower():
        if doc_age < 38:
            warnings.append(f"Doctor warning: Bác sĩ cấp bậc cao ({seniority}) nhưng độ tuổi còn khá trẻ ({doc_age} tuổi).")

    if not doctor_data.get("speciality"):
        errors.append("Doctor error: Chuyên khoa điều trị chính (speciality) của bác sĩ không được để trống.")

    return errors, warnings

def run_llm_clinical_check(
    kb_entry: Dict[str, Any],
    patient_data: Dict[str, Any],
    doctor_data: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Sử dụng LLM để thẩm định tính chính xác lâm sàng sâu."""
    system_prompt = """Bạn là Chuyên gia Thẩm định Lâm sàng (Senior Medical Consistency Auditor).
Nhiệm vụ của bạn là kiểm tra tính hợp lý y khoa và độ bám sát Tri thức Chuẩn (Knowledge Base) của cặp Hồ sơ Bệnh nhân & Bác sĩ.

ĐẶC BIỆT CHÚ Ý CÁC TIÊU CHÍ:
1. Clinical consistency: Lý do khám (chief_complaint) và thời gian (onset_duration) có phản ánh đúng triệu chứng bệnh trong KB không? Lý do khám có ngắn gọn, không dùng văn nói khẩu ngữ không?
2. Treatment consistency: Các biện pháp xử trí trước (prior_pain_treatments) có bám sát hoặc tương thích với giải pháp ban đầu trong KB không?
3. Medication & Chronic consistency: Bệnh mạn tính và thuốc dùng có phù hợp thực tế lâm sàng không?
4. Doctor Speciality: Chuyên khoa của bác sĩ có giải quyết đúng bệnh này không?

OUTPUT FORMAT: Trả về JSON duy nhất:
{
  "is_consistent": true/false,
  "inconsistencies": [
    "Mô tả lỗi lâm sàng 1 nếu có",
    "Mô tả lỗi lâm sàng 2 nếu có"
  ]
}
Chỉ đánh dấu is_consistent = false khi có mâu thuẫn y khoa nghiêm trọng hoặc sai lệch hoàn toàn so với KB."""

    user_prompt = f"""[TRI THỨC CHUẨN KB (Bệnh: {kb_entry.get('name')})]
- Nhóm: {kb_entry.get('category')}
- Triệu chứng chuẩn: {kb_entry.get('symptoms')}
- Nguyên nhân chuẩn: {kb_entry.get('causes')}
- Xử trí ban đầu chuẩn: {kb_entry.get('initial_care')}
- Điều trị y tế chuẩn: {kb_entry.get('treatment')}

[HỒ SƠ BỆNH NHÂN CẦN DUYỆT]
- Bệnh nhân: {patient_data.get('name')}, {patient_data.get('gender')}, {patient_data.get('age')} tuổi, {patient_data.get('occupation')}
- Lý do khám: {patient_data.get('chief_complaint')}
- Khởi phát: {patient_data.get('onset_duration')}
- Xử trí đau tại nhà: {patient_data.get('medical_history', {}).get('prior_pain_treatments')}
- Bệnh nền: {patient_data.get('medical_history', {}).get('chronic_conditions')}
- Thuốc đang dùng: {patient_data.get('medical_history', {}).get('current_medications')}

[HỒ SƠ BÁC SĨ CẦN DUYỆT]
- Bác sĩ: {doctor_data.get('name')}, {doctor_data.get('age')} tuổi, {doctor_data.get('seniority_level')}
- Chuyên khoa: {doctor_data.get('speciality')}

Hãy kiểm tra và trả về kết quả JSON."""

    try:
        res = call_llm_json(system_prompt, user_prompt, temperature=0.1)
        is_consistent = res.get("is_consistent", True)
        inconsistencies = res.get("inconsistencies", [])
        return is_consistent, inconsistencies
    except Exception as e:
        return True, [f"Không thể thực hiện kiểm định LLM phụ trợ: {str(e)}"]

def validate_profiles(
    kb_entry: Dict[str, Any],
    patient_data: Dict[str, Any],
    doctor_data: Dict[str, Any],
    deep_llm_check: bool = False,
    **kwargs
) -> ValidationResult:
    """Hàm kiểm định chính tổng hợp 2 tầng: Programmatic (Deterministic) + LLM (Deep Medical)."""
    prog_errors, prog_warnings = run_programmatic_checks(
        kb_entry=kb_entry,
        patient_data=patient_data,
        doctor_data=doctor_data
    )

    all_errors = list(prog_errors)
    all_warnings = list(prog_warnings)

    if not all_errors and deep_llm_check:
        is_llm_valid, llm_inconsistencies = run_llm_clinical_check(
            kb_entry=kb_entry,
            patient_data=patient_data,
            doctor_data=doctor_data
        )
        if not is_llm_valid:
            all_errors.extend(llm_inconsistencies)
        else:
            all_warnings.extend(llm_inconsistencies)

    is_valid = len(all_errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        errors=all_errors,
        warnings=all_warnings
    )
