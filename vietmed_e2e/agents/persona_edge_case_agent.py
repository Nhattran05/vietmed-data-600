# -*- coding: utf-8 -*-
"""
src/agents/persona_edge_case_agent.py
Sub-Agent phụ trách tạo:
1. speaking_style: Phong cách ăn nói theo nhóm tâm lý (Positive vs Negative).
2. edge_case: Kịch bản ngoại lệ / Tình huống biên gắn liền với các thuốc, bệnh nền và biện pháp từ KB.
(Lưu ý: Không sinh đối thoại mẫu, phần đối thoại do notechat đảm nhiệm).
"""

import json
from typing import Dict, Any, Optional
from vietmed_e2e.agents.llm_client import call_llm, extract_json

def generate_persona_and_edge_case(
    kb_entry: Dict[str, Any],
    demographics: Optional[Dict[str, Any]] = None,
    medical_history: Optional[Dict[str, Any]] = None,
    sentiment: str = "Positive",
    doctor_name: str = "Bác sĩ",
    demographic_data: Optional[Dict[str, Any]] = None,
    clinical_context_data: Optional[Dict[str, Any]] = None,
    medical_history_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Sinh phong cách nói và tình huống biên theo SPIT framework."""
    if demographics is None:
        demographics = demographic_data or {}
    if medical_history is None:
        medical_history = medical_history_data or {}

    disease = kb_entry["name"]
    initial_care_kb = kb_entry["initial_care"]
    treatment_kb = kb_entry["treatment"]

    name = demographics.get("name", "Bệnh nhân")
    age = demographics.get("age", 40)
    occupation = demographics.get("occupation", "Lao động tự do")

    system_prompt = (
        "BẠN LÀ CHUYÊN GIA TÂM LÝ LÂM SÀNG (THEO MÔ HÌNH SPIT).\n"
        "Nhiệm vụ của bạn là xây dựng phong cách nói chân thực và tình huống biên sâu sắc "
        "bám chặt vào các thuốc, bệnh nền và biện pháp tự điều trị đã được trích xuất từ tài liệu chuẩn."
    )

    prompt = f"""HỒ SƠ BỆNH NHÂN:
- Tên: {name} ({age} tuổi, {occupation})
- Bệnh chính: {disease} (STT: #{kb_entry['stt']})
- Nhóm tâm lý chỉ định: {sentiment}
- Giải pháp ban đầu theo tài liệu: {initial_care_kb}
- Phương pháp điều trị theo tài liệu: {treatment_kb}
- Thuốc/biện pháp đã tự dùng: {json.dumps(medical_history.get('prior_pain_treatments', []), ensure_ascii=False)}
- Thuốc định kỳ đang dùng: {json.dumps(medical_history.get('current_medications', []), ensure_ascii=False)}
- Bệnh nền mạn tính: {json.dumps(medical_history.get('chronic_conditions', []), ensure_ascii=False)}

YÊU CẦU SINH:
1. speaking_style:
   - Nếu nhóm '{sentiment}' là 'Positive': Điềm tĩnh, thật thà, xưng hô lễ phép, mô tả triệu chứng mạch lạc, lắng nghe bác sĩ.
   - Nếu nhóm '{sentiment}' là 'Negative': Hay than thở, sốt ruột, giọng cáu kỉnh vì đau kéo dài, ngắt lời bác sĩ hoặc ấp úng vì sợ hãi.
2. edge_case (Tình huống biên ngắn gọn 1-2 câu, gắn chặt với các thuốc/biện pháp trong tài liệu):
   - Nếu 'Positive': Mang theo hộp thực phẩm chức năng / thảo dược hoặc sổ nhật ký đau nhờ bác sĩ xem xét tương tác; hoặc chủ động hỏi bài tập tại nhà.
   - Nếu 'Negative': Không nhớ tên thuốc chỉ nhớ màu viên thuốc; HOẶC tự ý bỏ thuốc huyết áp/mỡ máu vì sợ hại gan; HOẶC giấu chuyện tự uống thuốc bột gia truyền không rõ nguồn gốc; HOẶC tự uống quá liều thuốc giảm đau; HOẶC nôn nóng đòi tiêm thuốc mạnh nhất bất chấp cảnh báo.

Trả về DUY NHẤT một chuỗi JSON hợp lệ:
{{
  "speaking_style": "...",
  "edge_case": "..."
}}"""

    raw = call_llm(prompt, system_prompt=system_prompt, temperature=0.5)
    data = extract_json(raw)

    return {
        "speaking_style": data.get("speaking_style", "Điềm tĩnh, thật thà, xưng hô lễ phép."),
        "edge_case": data.get("edge_case", "Bệnh nhân tuân thủ và trao đổi kỹ với bác sĩ về thuốc điều trị.")
    }

generate_persona_edge_case = generate_persona_and_edge_case
