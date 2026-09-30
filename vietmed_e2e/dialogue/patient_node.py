# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/patient_node.py
Roleplay Module 2c: Patient-LLM (Fog-Aware)
Sinh đúng 1 lượt thoại của Bệnh nhân.
ĐẶC BIỆT: Bệnh nhân KHÔNG ĐƯỢC NHẬN BỆNH ÁN ĐẦY ĐỦ VÀ CHECKLIST!
Chỉ nhận patient_visible_context (các phần đã mở khóa qua Fog Gate) và câu hỏi vừa rồi của Bác sĩ.
"""

import sys
from typing import Dict, Any

from vietmed_e2e.schemas.state import E2EState, DialogueTurn
from vietmed_e2e.agents.llm_client import call_llm, extract_json_payload
from vietmed_e2e.sanitizer.dialogue_sanitizer import sanitize_spoken_text
from vietmed_e2e.dialogue.utils import format_history_for_prompt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def patient_node(state: E2EState) -> Dict[str, Any]:
    """
    Sinh 1 lượt thoại chân thực, mộc mạc của Bệnh nhân dưới cơ chế Fog of War.
    """
    disease_name = state["disease_name"]
    pat = state.get("patient_profile", {}) or state.get("final_patient", {})
    doc = state.get("doctor_profile", {}) or state.get("final_doctor", {})
    history_text = format_history_for_prompt(state.get("turns", []))
    turn_num = state.get("current_turn_count", 0) + 1

    pat_name = pat.get("name", "Bệnh nhân")
    pat_display = pat.get("display_name") or pat_name
    pat_age = pat.get("age", 45)
    pat_gender = pat.get("gender", "Nam")
    pat_persona = pat.get("persona") or pat.get("speaking_style", "Mộc mạc, lễ phép, dùng từ ngữ giác quan dân dã")
    doc_name = doc.get("name", "Bác sĩ")
    doc_display = doc.get("display_name") or doc_name

    # Fog of War context
    patient_visible_context = state.get("patient_visible_context", "")
    hidden_topics_hint = state.get("hidden_topics_hint", "")

    prompt = f"""Hãy đóng vai một bệnh nhân ({pat_name}, xưng hô: {pat_display}, {pat_gender}, {pat_age} tuổi, tính cách: {pat_persona}) để trả lời bác sĩ ({doc_name}, xưng hô: {doc_display}). Thêm 'Patient:' trước mỗi lượt. Bạn chỉ là một người bệnh bình thường, đến khám vì thấy khó chịu trong người. Phản hồi của bạn nên thông tục nhất có thể. Đừng đề cập đến bất kỳ kết quả xét nghiệm, chẩn đoán, hoặc liều lượng y tế nào, vì bạn không hiểu những điều này.

=== THÔNG TIN BẠN BIẾT RÕ VỀ BẢN THÂN (PATIENT VISIBLE CONTEXT) ===
{patient_visible_context}

=== NHỮNG ĐIỀU BẠN TUYỆT ĐỐI CHƯA BIẾT HOẶC KHÔNG ĐƯỢC TỰ Ý NÓI RA ===
{hidden_topics_hint}

Lịch sử Hội thoại Gần nhất:
{history_text}

=== QUY TẮC ĐẦU RA BỔ SUNG & QUY TẮC TỰ NHIÊN HÓA (NOTECHAT RULES) ===
1. QUY TẮC NÓI NGẮN GỌN, TỰ NHIÊN, KHÔNG DÀI DÒNG (BẮT BUỘC):
   - Mỗi lượt thoại chỉ nói từ 1 đến 2 câu ngắn gọn, dân dã đời thường (độ dài lý tưởng TỐI ĐA 20 TỪ, dao động 8 - 20 từ).
   - Trả lời đúng trọng tâm câu hỏi của bác sĩ; tuyệt đối không tuôn ra một đoạn văn dài, không tự giác liệt kê một danh sách triệu chứng cùng một lúc.
2. LƯỢC BỎ LIỀU LƯỢNG KỸ THUẬT & TRẢ LỜI TIỀN SỬ KHÁM:
   - Khi bác sĩ chào và hỏi xác nhận thông tin (họ tên, tuổi): Lễ phép xác nhận ngắn gọn (ví dụ: "Dạ đúng rồi bác sĩ ạ." hoặc "Dạ vâng, tôi là {pat_name}, {pat_age} tuổi đây ạ.").
   - TUYỆT ĐỐI KHÔNG đọc hàm lượng mg, mcg, số lần uống chi tiết (ví dụ: cấm nói "Celecoxib 200mg"). Chỉ nói tên bệnh và tên thuốc dân dã ("Tôi bị đau khớp, đợt trước uống viên thuốc màu vàng...").
   - Khi bác sĩ hỏi đã đi khám ở đâu chưa: Dựa vào mục tiền sử đi khám trong thông tin bạn biết, kể tên bệnh viện đã khám và bác sĩ trước bảo bị sao (hoặc nói thật là chưa từng đi khám ở đâu, đây là lần đầu).
   - Khi bác sĩ hỏi tiếp về điều trị cũ (cách điều trị, hiệu quả, thời gian theo): Bệnh nhân trả lời đầy đủ 3 ý bằng ngôn từ mộc mạc: (1) biện pháp điều trị, (2) thời gian theo phác đồ và (3) mức độ hiệu quả.
   - Khi bác sĩ hỏi thang điểm đau từ 0 đến 10: Trả lời tự nhiên theo thông tin bạn biết (ví dụ: "Lúc này thì khoảng 5-6 điểm bác sĩ ạ, nhưng lúc đêm đau nhức dữ dội thì phải 8-9 điểm.").
   - Khi bác sĩ hỏi về cảm giác đau (bỏng rát, điện giật, kiến bò): Trả lời mộc mạc (ví dụ: "Nó cứ nhức buốt thấu xương thôi bác sĩ, chứ không rát bỏng hay giật giật gì cả ạ.").
   - Khi bác sĩ hỏi về giấc ngủ và tâm trạng: Trả lời thật thà (ví dụ: "Dạ dạo này tôi hay bị mất ngủ về đêm vì đau, người lúc nào cũng mệt mỏi, lo lắm bác sĩ ạ.").

3. BỆNH NHÂN KHÔNG PHÁT NGÔN CHUYÊN MÔN & CẤM TÊN GIẢI PHẪU:
   - TUYỆT ĐỐI KHÔNG tự đọc kết quả MRI, X-quang, góc độ, hay tên tổn thương giải phẫu. Khi bác sĩ hỏi về chụp chiếu hay mổ cũ, chỉ nói đưa kết quả/phim chụp cho bác sĩ xem.
   - TUYỆT ĐỐI KHÔNG nói chính xác các vị trí đau bằng thuật ngữ y khoa/giải phẫu (CẤM NÓI: "mỏm cùng vai", "cơ trên gai", "gân trên gai", "chóp xoay", "cơ liền vai", "liên sườn", "bao hoạt dịch", "L4-L5", "đĩa đệm",...). Người bệnh chỉ được mô tả vị trí đau bằng ngôn từ dân dã đời thường (ví dụ: "chỗ đầu vai", "đỉnh vai này", "khúc này này bác sĩ", "ngang bả vai", "dọc bên mạn sườn", "ngang thắt lưng", "dọc xuống mông", "chỗ khớp này").
4. KHO TỪ NGỮ CẢM GIÁC CƠ THỂ & BỐI CẢNH:
   - Diễn tả triệu chứng bằng từ ngữ cảm giác thuần Việt (nhức thấu xương, buốt nhói, ê ẩm, lạo xạo, bì bì, cắn dứt, giật thót...) và bối cảnh sinh hoạt khi khởi phát đau.
5. CHỈ LỜI NÓI CẤT THÀNH TIẾNG (TTS SẠCH 100%):
   - Tuyệt đối không chứa chú thích hành động hay dấu ngoặc đơn (), ngoặc vuông [].
6. ĐỊNH DẠNG ĐẦU RA JSON BẮT BUỘC:
Hãy trả về DUY NHẤT một JSON hợp lệ:
{{
  "text": "Lời phát ngôn trực tiếp của Bệnh nhân (tối đa 20 từ, không kèm tiền tố tên)",
  "is_parsed": true,
  "reason": "Giải thích ngắn vì sao lượt này có thể hoặc không thể chèn câu đệm"
}}"""

    raw = call_llm(prompt)
    payload = extract_json_payload(raw)
    if payload and "text" in payload:
        raw_text = str(payload["text"])
        is_parsed = bool(payload.get("is_parsed", False))
    else:
        raw_text = raw
        is_parsed = ("." in raw_text and len(raw_text.split(".")) >= 2) or len(raw_text.split()) > 25

    text = sanitize_spoken_text(raw_text)

    new_turn: DialogueTurn = {
        "turn_id": turn_num,
        "speaker": "patient",
        "speaker_name": pat_display,
        "text": text,
        "covered_item": None,
        "timestamp": None,
        "is_parsed": is_parsed
    }
    parse_tag = "[Splittable]" if is_parsed else "[Solid]"
    print(f"  [Lượt {turn_num}] 👤 {pat_display} {parse_tag}: {text[:80]}...", flush=True)

    return {
        "turns": [new_turn],
        "current_turn_count": turn_num
    }
