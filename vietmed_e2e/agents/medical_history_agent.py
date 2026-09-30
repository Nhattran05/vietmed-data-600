# -*- coding: utf-8 -*-
"""
src/agents/medical_history_agent.py
Sub-Agent phụ trách tạo 7 trường con của Mục #10: Medical History
bám sát 100% dữ liệu chuẩn từ 'danh-sach-60-benh-khong-cap-cuu.md':
1. chronic_conditions (từ Nguyên nhân & Dịch tễ)
2. current_medications (từ Phương pháp điều trị)
3. prior_pain_treatments (từ Giải pháp ban đầu)
4. past_surgeries_trauma
5. allergies_intolerances
6. lifestyle_risk_factors
7. previous_medical_visits (Roll 60/40: 60% chưa từng khám, 40% đã khám)
"""

import json
import random
from typing import Dict, Any, Optional
from vietmed_e2e.agents.llm_client import call_llm, extract_json

def generate_medical_history(
    kb_entry: Dict[str, Any],
    demographics: Dict[str, Any],
    clinical_context: Dict[str, Any],
    force_prior_visit: Optional[bool] = None
) -> Dict[str, Any]:
    """Sinh toàn bộ 7 trường con của mục Medical History bám sát tài liệu chuẩn."""
    disease = kb_entry["name"]
    causes_kb = kb_entry["causes"]
    initial_care_kb = kb_entry["initial_care"]
    treatment_kb = kb_entry["treatment"]

    name = demographics["name"]
    age = demographics["age"]
    gender = demographics["gender"]
    occupation = demographics["occupation"]
    complaint = clinical_context["chief_complaint"]

    system_prompt = (
        "BẠN LÀ BÁC SĨ CHUYÊN KHOA NỘI & DƯỢC LÝ LÂM SÀNG TẠI VIỆT NAM.\n"
        "QUY TẮC BẮT BUỘC: Toàn bộ thông tin về Bệnh nền mạn tính, Thuốc điều trị và Biện pháp tự chăm sóc "
        "PHẢI DỰA TRÊN các cột 'Nguyên nhân', 'Giải pháp ban đầu' và 'Phương pháp điều trị' của tài liệu chuẩn dưới đây. "
        "TUYỆT ĐỐI KHÔNG TỰ BỊA ĐẶT DỊCH TỄ HAY THUỐC ĐIỀU TRỊ NGOÀI TÀI LIỆU NÀY."
    )

    # Roll 60/40: 60% chưa từng đi khám, 40% đã đi khám trước đó (hoặc ép buộc qua cờ force_prior_visit)
    if force_prior_visit is not None:
        has_prior_visit = bool(force_prior_visit)
    else:
        has_prior_visit = random.random() >= 0.6  # True = 40% đã đi khám

    # Quy tắc Bác sĩ hỏi tiền sử khám trước đó:
    # - Nếu có đi khám (has_prior_visit == True): 100% luôn luôn hỏi để reveal thông tin.
    # - Nếu chưa đi khám (has_prior_visit == False): Roll 60% hỏi (để bệnh nhân trả lời là lần đầu đi khám), 40% không hỏi.
    if has_prior_visit:
        doctor_asks_prior_visit = True
    else:
        doctor_asks_prior_visit = random.random() < 0.6
    if has_prior_visit:
        previous_visits_instruction = (
            "Bệnh nhân ĐÃ TỪNG đi khám tại một bệnh viện/phòng khám trước đây vì triệu chứng tương tự. "
            "Hãy sinh thông tin chi tiết gồm:\n"
            "   - hospital: Tên bệnh viện/phòng khám thực tế tại Việt Nam (ví dụ: BV Đại học Y Dược, PK Đa khoa Hòa Hảo...).\n"
            "   - specialty: Chuyên khoa đã khám (ví dụ: Cơ Xương Khớp, Nội Thần Kinh...).\n"
            "   - diagnosis: Chẩn đoán tại thời điểm đó (có thể đúng hoặc chưa chính xác hoàn toàn).\n"
            "   - treatment_given: Phương pháp điều trị đã được đưa ra (thuốc, vật lý trị liệu, tiêm...).\n"
            "   - treatment_duration: Thời gian bệnh nhân theo phương pháp điều trị đó (ví dụ: 'uống thuốc liên tục 2 tuần', 'tập vật lý trị liệu 1 tháng', 'chỉ uống được 5 ngày rồi ngưng do đau dạ dày'...). \n"
            "   - effectiveness: Mức độ hiệu quả (Không cải thiện / Cải thiện một phần / Hết triệu chứng tạm thời rồi tái phát).\n"
            "   - visit_time: Khoảng thời gian bao lâu trước đây (ví dụ: '6 tháng trước', '1 năm trước')."
        )
        previous_visits_json_template = """[
    {{
      "hospital": "...",
      "specialty": "...",
      "diagnosis": "...",
      "treatment_given": "...",
      "treatment_duration": "...",
      "effectiveness": "...",
      "visit_time": "..."
    }}
  ]"""
    else:
        previous_visits_instruction = (
            "Bệnh nhân CHƯA TỪNG đi khám bác sĩ hoặc đến bệnh viện nào trước lần này. "
            "Đây là lần đầu tiên bệnh nhân đi khám chuyên khoa. Trả về giá trị null cho trường này."
        )
        previous_visits_json_template = "null"

    prompt = f"""DỮ LIỆU GỐC TRÍCH XUẤT TỪ 'danh-sach-60-benh-khong-cap-cuu.md':
- Bệnh chính: {disease} (STT: {kb_entry['stt']}, Nhóm: {kb_entry['category']})
- Nguyên nhân & Dịch tễ: {causes_kb}
- Giải pháp ban đầu (Tự chăm sóc): {initial_care_kb}
- Phương pháp điều trị (Y khoa chuẩn): {treatment_kb}

THÔNG TIN BỆNH NHÂN:
- Tên: {name} | Tuổi: {age} | Giới tính: {gender} | Nghề nghiệp: {occupation}
- Lý do khám: {complaint}

YÊU CẦU THIẾT LẬP 7 TRƯỜNG CON CỦA MEDICAL HISTORY:
1. chronic_conditions:
   - BẮT BUỘC lấy bệnh nền từ cột 'Nguyên nhân & Dịch tễ' nếu có (ví dụ: tiểu đường, tăng acid uric, viêm dạ dày/nhiễm HP, thoái hóa...).
   - Nếu bệnh nhân trẻ tuổi và nguyên nhân chỉ do vận động/chấn thương cơ học, có thể ghi nhận tình trạng chấn thương hoặc không có bệnh mạn tính nặng.
   - Gồm: condition, duration (phải nhỏ hơn {age} tuổi), control_status, treated_at.
2. current_medications:
   - BẮT BUỘC lấy các thuốc điều trị từ cột 'Phương pháp điều trị' (ví dụ NSAID, Colchicine, allopurinol, PPI, tiêm corticoid, vật lý trị liệu...).
   - Mỗi thuốc gồm: name, dosage (chuẩn y khoa), frequency, adherence, và ĐẶC BIỆT là 'appearance' (hình dáng, màu sắc viên thuốc để bệnh nhân nhận diện).
3. prior_pain_treatments:
   - BẮT BUỘC lấy các biện pháp bệnh nhân đã tự làm ở nhà từ cột 'Giải pháp ban đầu' (ví dụ: chườm lạnh, chườm ấm, đai nẹp, ngâm chân, nghỉ ngơi, hoặc tự mua giảm đau tương ứng).
   - Gồm: treatment, frequency, outcome, warning_flags.
4. past_surgeries_trauma:
   - 1 sự kiện mổ xẻ hoặc chấn thương trong quá khứ phù hợp với lứa tuổi và nghề nghiệp {occupation}. Gồm: event, year, sequelae.
5. allergies_intolerances:
   - 1 tiền sử dị ứng thuốc thực tế liên quan đến nhóm thuốc của bệnh (ví dụ dị ứng NSAID, Aspirin, Penicillin hoặc không có). Gồm: allergen, reaction, severity.
6. lifestyle_risk_factors:
   - Thói quen sinh hoạt và tư thế nghề nghiệp gắn liền với {occupation} và nguyên nhân trong tài liệu. Gồm: tobacco, alcohol, occupational_posture, daily_water_intake.
7. previous_medical_visits:
   {previous_visits_instruction}

Trả về DUY NHẤT một chuỗi JSON hợp lệ không markdown với định dạng:
{{
  "chronic_conditions": [
    {{
      "condition": "...",
      "duration": "... năm",
      "control_status": "...",
      "treated_at": "..."
    }}
  ],
  "current_medications": [
    {{
      "name": "...",
      "dosage": "...",
      "frequency": "...",
      "adherence": "...",
      "appearance": "..."
    }}
  ],
  "prior_pain_treatments": [
    {{
      "treatment": "...",
      "frequency": "...",
      "outcome": "...",
      "warning_flags": "..."
    }}
  ],
  "past_surgeries_trauma": [
    {{
      "event": "...",
      "year": 2018,
      "sequelae": "..."
    }}
  ],
  "allergies_intolerances": [
    {{
      "allergen": "...",
      "reaction": "...",
      "severity": "..."
    }}
  ],
  "lifestyle_risk_factors": {{
    "tobacco": "...",
    "alcohol": "...",
    "occupational_posture": "...",
    "daily_water_intake": "..."
  }},
  "previous_medical_visits": {previous_visits_json_template}
}}"""

    raw = call_llm(prompt, system_prompt=system_prompt, temperature=0.4)
    data = extract_json(raw)

    # Đảm bảo trường source_reference và has_prior_visit flag
    data["source_reference"] = f"STT {kb_entry['stt']} - {disease} (danh-sach-60-benh-khong-cap-cuu.md)"
    data["has_prior_medical_visit"] = has_prior_visit
    data["doctor_asks_prior_visit"] = doctor_asks_prior_visit
    return data
