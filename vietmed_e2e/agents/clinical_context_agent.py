# -*- coding: utf-8 -*-
"""
src/agents/clinical_context_agent.py
Sub-Agent phụ trách chuyển đổi triệu chứng y khoa từ KB thành:
1. chief_complaint: Lý do khám / Mô tả cảm giác thực thể ngắn gọn, chuẩn xác, KHÔNG DÙNG VĂN NÓI KHẨU NGỮ.
2. onset_duration: Thời gian khởi phát & diễn biến thời gian phù hợp với tính chất cấp/mạn tính.
"""

from typing import Dict, Any
from vietmed_e2e.agents.llm_client import call_llm, extract_json

def generate_clinical_context(
    kb_entry: Dict[str, Any],
    demographics: Dict[str, Any]
) -> Dict[str, Any]:
    """Sinh chief_complaint và onset_duration từ KB symptoms."""
    disease = kb_entry["name"]
    symptoms_kb = kb_entry["symptoms"]
    name = demographics.get("name", "Bệnh nhân")
    age = demographics.get("age", 40)
    occupation = demographics.get("occupation", "Lao động tự do")

    system_prompt = (
        "Bạn là Chuyên gia Lâm sàng & Ngôn ngữ Y tế. Nhiệm vụ của bạn là chuyển đổi triệu chứng y khoa từ tài liệu chuẩn "
        "thành Lý do khám (chief_complaint) và Thời gian khởi phát (onset_duration) của bệnh nhân."
    )

    prompt = f"""DỰA VÀO DỮ LIỆU TRIỆU CHỨNG CHUẨN TỪ TÀI LIỆU:
- Bệnh: {disease}
- Triệu chứng y khoa chuẩn: {symptoms_kb}
- Bệnh nhân: {name}, {age} tuổi, nghề nghiệp: {occupation}

YÊU CẦU SINH:
1. chief_complaint:
   - Mô tả ngắn gọn (1 câu), trực diện vào vị trí tổn thương và cảm giác thực thể giác quan đời thường.
   - VÍ DỤ CHUẨN: "Ngón chân cái sưng vù, đỏ, cảm giác nóng rát và đau khi chạm vào." hoặc "Khớp vai cứng đơ, đau nhức tăng về đêm và không với tay ra sau được."
   - QUY TẮC CẤM NGHIÊM NGẶT:
     + TUYỆT ĐỐI KHÔNG viết theo lối văn nói hội thoại hay khẩu ngữ kịch tính.
     + KHÔNG dùng từ cảm thán ("Trời ơi", "chết mất", "ối giời", "than ôi").
     + KHÔNG dùng lời xưng hô, chào hỏi bác sĩ ("bác sĩ ơi", "thưa bác sĩ", "ạ", "tôi đến khám vì...").
     + KHÔNG cần đóng mở dấu ngoặc kép kịch bản.
   - Phản ánh chính xác các vị trí và triệu chứng thực thể đã ghi trong tài liệu: {symptoms_kb}.

2. onset_duration:
   - Mô tả ngắn gọn thời gian khởi phát và diễn biến (ví dụ: "Đau âm ỉ 2 tuần nay, 2 ngày gần đây cơn đau tăng nặng đột ngột").
   - Phù hợp với tính chất cấp hay mạn tính của bệnh {disease}.

Trả về DUY NHẤT chuỗi JSON hợp lệ:
{{
  "chief_complaint": "...",
  "onset_duration": "..."
}}"""

    raw = call_llm(prompt, system_prompt=system_prompt, temperature=0.3)
    data = extract_json(raw)

    complaint = data.get("chief_complaint", symptoms_kb).strip().strip('"').strip("'")
    onset = data.get("onset_duration", "Kéo dài vài tuần nay, gần đây đau tăng").strip()

    return {
        "chief_complaint": complaint,
        "onset_duration": onset
    }
