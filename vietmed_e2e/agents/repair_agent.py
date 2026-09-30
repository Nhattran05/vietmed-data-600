# -*- coding: utf-8 -*-
"""
src/agents/repair_agent.py
Repair Agent: Tự động điều chỉnh và khắc phục cục bộ các trường dữ liệu bị lỗi nhất quán
theo phản hồi từ Validator mà không làm xáo trộn các trường đã hợp lệ.
"""

from typing import Dict, Any, List, Tuple
from vietmed_e2e.agents.llm_client import call_llm_json

SYSTEM_PROMPT = """Bạn là Chuyên viên Sửa lỗi Hồ sơ Y khoa (Medical Profile Repair Agent).
Nhiệm vụ của bạn là nhận danh sách các lỗi không nhất quán (Validation Errors) và khắc phục CHÍNH XÁC những trường thông tin bị lỗi trong Hồ sơ Bệnh nhân hoặc Bác sĩ.

QUY TẮC BẮT BUỘC:
1. Tuyệt đối bám sát Tri thức Chuẩn (Knowledge Base) của bệnh được cung cấp.
2. KHÔNG thêm bất kỳ biểu tượng cảm xúc (emoji/icon) nào trong bất kỳ trường văn bản nào.
3. Chỉ chỉnh sửa những trường bị báo lỗi hoặc chịu ảnh hưởng trực tiếp từ lỗi. Giữ nguyên tính nhất quán của các trường hợp lệ khác.
4. Đảm bảo năm xảy ra phẫu thuật/chấn thương phải nhỏ hơn hoặc bằng năm hiện tại và phù hợp với tuổi bệnh nhân.
5. Lý do khám (chief_complaint) PHẢI LÀ câu mô tả ngắn gọn cảm giác thực thể/giác quan (ví dụ: 'Ngón chân cái sưng vù, đỏ, cảm giác nóng rát và đau khi chạm vào'), TUYỆT ĐỐI KHÔNG dùng văn nói hội thoại ('Trời ơi', 'bác sĩ ơi', 'thưa bác sĩ').

ĐỊNH DẠNG TRẢ VỀ: Trả về duy nhất 1 JSON object chứa 2 object chính đã được khắc phục lỗi:
{
  "repaired_patient": {
    "name": "...",
    "gender": "...",
    "age": 0,
    "occupation": "...",
    "chief_complaint": "...",
    "onset_duration": "...",
    "medical_history": {
      "chronic_conditions": [...],
      "current_medications": [...],
      "prior_pain_treatments": [...],
      "past_surgeries_trauma": [...],
      "allergies_intolerances": [...],
      "lifestyle_risk_factors": {...},
      "source_reference": "..."
    },
    "speaking_style": "...",
    "edge_case": "..."
  },
  "repaired_doctor": {
    "name": "...",
    "gender": "...",
    "age": 0,
    "seniority_level": "...",
    "speciality": "...",
    "communication_tone": "..."
  }
}"""

def repair_profiles(
    kb_entry: Dict[str, Any],
    patient_data: Dict[str, Any],
    doctor_data: Dict[str, Any],
    validation_errors: List[str],
    **kwargs
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Gọi LLM để sửa lỗi profile dựa trên danh sách validation_errors.
    Trả về: (repaired_patient, repaired_doctor)
    """
    error_list_str = "\n".join([f"- {err}" for err in validation_errors])

    user_prompt = f"""[TRI THỨC CHUẨN KB (Bệnh: {kb_entry.get('name')})]
- Nhóm: {kb_entry.get('category')}
- Triệu chứng chuẩn: {kb_entry.get('symptoms')}
- Nguyên nhân chuẩn: {kb_entry.get('causes')}
- Xử trí ban đầu chuẩn: {kb_entry.get('initial_care')}
- Điều trị y tế chuẩn: {kb_entry.get('treatment')}

[DANH SÁCH LỖI CẦN KHẮC PHỤC]
{error_list_str}

[HỒ SƠ BỆNH NHÂN HIỆN TẠI]
{patient_data}

[HỒ SƠ BÁC SĨ HIỆN TẠI]
{doctor_data}

Hãy sửa lại các thông tin sai lệch để hồ sơ hoàn toàn nhất quán với KB và khắc phục triệt để các lỗi trên."""

    res = call_llm_json(SYSTEM_PROMPT, user_prompt, temperature=0.3)

    repaired_patient = res.get("repaired_patient", patient_data)
    repaired_doctor = res.get("repaired_doctor", doctor_data)

    if not repaired_patient:
        repaired_patient = patient_data
    if not repaired_doctor:
        repaired_doctor = doctor_data

    return repaired_patient, repaired_doctor
