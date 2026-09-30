# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/physician_node.py
Roleplay Module 2a: Physician-LLM
Sinh đúng 1 lượt thoại tiếp theo của Bác sĩ dựa trên:
- Clinical Note (Ground Truth đầy đủ)
- Checklist còn lại (ưu tiên current_focus)
- Lịch sử hội thoại
"""

import sys
from typing import Dict, Any

from vietmed_e2e.schemas.state import E2EState, DialogueTurn
from vietmed_e2e.agents.llm_client import call_llm, extract_json_payload
from vietmed_e2e.sanitizer.dialogue_sanitizer import sanitize_spoken_text
from vietmed_e2e.dialogue.utils import format_history_for_prompt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def physician_node(state: E2EState) -> Dict[str, Any]:
    """
    Sinh 1 lượt thoại ngắn gọn, ân cần của Bác sĩ.
    """
    clinical_note = state["clinical_note"]
    disease_name = state["disease_name"]
    doc = state.get("doctor_profile", {})
    pat = state.get("patient_profile", {})
    checklist = state.get("checklist", [])
    current_focus = state.get("current_focus") or (checklist[0] if checklist else "Tổng kết và dặn dò")
    history_text = format_history_for_prompt(state.get("turns", []))
    turn_num = state.get("current_turn_count", 0) + 1

    doc_name = doc.get("name", "Bác sĩ")
    doc_display = doc.get("display_name") or doc_name
    doc_style = doc.get("style", "Đĩnh đạc, ân cần, giọng miền Bắc, gặng hỏi chi tiết và khám thực thể")
    pat_name = pat.get("name", "Bệnh nhân")
    pat_display = pat.get("display_name") or pat_name
    pat_age = pat.get("age", 45)

    prompt = f"""Hãy đóng vai một bác sĩ ({doc_name}, xưng hô: {doc_display}, phong cách: {doc_style}) và tiếp tục tạo các câu hỏi hoặc kết luận, hoặc kết quả xét nghiệm (chẳng hạn như kết quả xét nghiệm dùng thuốc hoặc các dấu hiệu sinh tồn) dựa trên đoạn hội thoại ở trên và bệnh án lâm sàng. Thêm 'physician:' trước mỗi lượt. Câu hỏi, câu trả lời hoặc kết luận của bạn phải xoay quanh các từ khóa tương ứng với bệnh án lâm sàng. Bạn cần đảm bảo kế hoạch điều trị, thuốc và liều lượng bạn đưa cho bệnh nhân hoàn toàn nhất quán với bệnh án lâm sàng. Không hỏi những câu hỏi mà câu trả lời không thể tìm thấy trong bệnh án lâm sàng. Bạn có thể mô tả và giải thích đánh giá chuyên môn cho bệnh nhân và hướng dẫn bệnh nhân về các yêu cầu theo dõi tái khám, nhưng không được hỏi những câu hỏi đòi hỏi kiến thức y khoa chuyên môn để trả lời. Thứ tự các câu hỏi bạn hỏi phải khớp với thứ tự các từ khóa tôi đã cung cấp.

Hồ sơ Y khoa (Clinical Note):
{clinical_note}
Các Từ khóa Cốt lõi (Checklist): {checklist} (Mục tiêu hiện tại: "{current_focus}")
Lịch sử Hội thoại Gần nhất:
{history_text}

=== QUY TẮC ĐẦU RA BỔ SUNG & QUY TẮC TỰ NHIÊN HÓA (NOTECHAT RULES) ===
0. QUY TẮC XÁC NHẬN DANH TÍNH BỆNH NHÂN (NẾU MỤC TIÊU LÀ XÁC NHẬN DANH TÍNH):
   - Khi mục tiêu hiện tại ("{current_focus}") liên quan đến "Xác nhận danh tính" hoặc "đối chiếu họ tên":
     Bác sĩ chào hỏi và đối chiếu thông tin hành chính (Họ tên + Tuổi) của bệnh nhân một cách lịch thiệp, tự nhiên:
     Ví dụ: "Chào {pat_display}, cho tôi xác nhận lại thông tin một chút, anh/chị là {pat_name}, {pat_age} tuổi đúng không?".
   - Tuyệt đối không hỏi gộp lý do khám ở ngay lượt này. Chỉ chào và xác nhận danh tính ngắn gọn (12-18 từ).
1. QUY TẮC XƯNG HÔ TỰ NHIÊN (CẤM TỰ XƯNG 'BÁC SĨ' LẶP LẠI):
   - Bác sĩ tuyệt đối KHÔNG tự xưng ngôi thứ ba là "bác sĩ" liên tục trong câu thoại (CẤM các cách nói như: "Bác sĩ sẽ chạm nhẹ...", "Bác sĩ sẽ xem...", "Bác sĩ nâng cánh tay...").
   - Hãy xưng hô đời thường, tự nhiên: xưng "tôi" - gọi "bác/anh/chị/em" (hoặc xưng "bác/chú" nếu bệnh nhân trẻ hơn nhiều), hoặc lược bỏ đại từ nhân xưng một cách tự nhiên (ví dụ: "Em ngồi thoải mái nhé, để tôi chạm nhẹ xem đau ở đâu", "Giờ để tôi xem qua kết quả phim chụp nhé", "Đưa tay lên từ từ giúp tôi nào...").
2. QUY TẮC NÓI NGẮN GỌN, TỰ NHIÊN, KHÔNG DÀI DÒNG (BẮT BUỘC):
   - Mỗi lượt thoại chỉ gồm 1 đến 2 câu ngắn (độ dài lý tưởng TỐI ĐA 20 TỪ, dao động 10 - 20 từ, tối đa không quá 3 câu).
   - Tuyệt đối không độc thoại dài dòng, không giải thích cả đoạn văn như sách giáo khoa. Mỗi lượt CHỈ HỎI ĐÚNG 1 Ý TRỌNG TÂM xoay quanh "{current_focus}", tuyệt đối không hỏi dồn dập 2-3 câu hỏi cùng lúc.
3. QUY TẮC GIAO TIẾP LỊCH THIỆP & CẤM CÂU RÀO ĐÓN KHẲNG ĐỊNH MÁY MÓC:
   - TUYỆT ĐỐI CẤM các câu tiền đề/rào đón mang tính tự khẳng định, giải thích mục đích thủ tục máy móc trước khi hỏi (ví dụ CẤM: "Để tôi kê đơn cho chuẩn...", "Để tôi chẩn đoán chính xác...", "Để tôi kiểm tra kỹ...", "Để việc điều trị hiệu quả...", "Tôi cần hỏi câu này để...").
   - Thể hiện thái độ ân cần, nhã nhặn tự nhiên của người thầy thuốc: dùng các cụm từ lịch thiệp, tôn trọng người bệnh như: "Cho tôi hỏi thêm là...", "Trước nay anh/chị có từng...".
   - Hỏi trực diện, nhẹ nhàng, tôn trọng (Ví dụ thay vì "Để tôi kê đơn cho chuẩn, anh có dị ứng thuốc gì không?", hãy hỏi: "Cho tôi hỏi thêm là trước nay anh có từng bị dị ứng với loại thuốc nào không?").
4. THU THẬP THÔNG TIN QUA NHIỀU LƯỢT:
   - Không liệt kê dồn dập nhiều bệnh án/triệu chứng. Tách thành nhiều câu hỏi ngắn gọn theo tiến trình.
5. PHÂN ĐỊNH RANH GIỚI VAI TRÒ:
   - Bác sĩ chủ động dẫn dắt, hỏi về bối cảnh khởi phát, sờ nắn điểm đau, tự đọc kết quả xét nghiệm/MRI cho bệnh nhân, KHÔNG ĐƯỢC hỏi ngược lại bệnh nhân về chỉ số chuyên môn.
6. KHAI THÁC TIỀN SỬ THĂM KHÁM & ĐIỀU TRỊ CŨ:
   - Chào hỏi ân cần, hỏi lý do đến khám.
   - Khi mục tiêu hiện tại ("{current_focus}") liên quan đến "thăm khám trước" hoặc "cơ sở y tế đã khám": Bác sĩ hãy hỏi trực tiếp và lịch thiệp: "Trước đây bác/anh/chị đã từng đi khám ở bệnh viện hay phòng khám nào về triệu chứng này chưa, khi đó bác sĩ chẩn đoán thế nào?".
   - Khi mục tiêu hiện tại ("{current_focus}") liên quan đến "đánh giá điều trị trước đây", "biện pháp điều trị" hoặc "phương pháp điều trị cũ": Bác sĩ bắt buộc hỏi follow-up gộp tự nhiên (ngắn gọn dưới 20 từ) đủ 3 ý: phương pháp điều trị khi đó là gì, có hiệu quả không và đã theo điều trị trong bao lâu (Ví dụ: "Đợt đó bác sĩ cho điều trị bằng cách nào, có đỡ không và anh/chị theo điều trị trong bao lâu?").
6b. HỎI THANG ĐIỂM ĐAU VAS & ĐẶC TÍNH ĐAU CHUYÊN SÂU (NẾU CÓ TRONG CHECKLIST):
   - Khi mục tiêu ("{current_focus}") liên quan đến "thang điểm VAS" hoặc "cường độ đau": Bác sĩ hỏi tự nhiên, dễ hiểu: "Nếu chấm thang điểm từ 0 đến 10, lúc này anh/chị thấy đau khoảng mấy điểm, và lúc đau nhất là mấy điểm?".
   - Khi mục tiêu ("{current_focus}") liên quan đến "đặc tính đau", "DN4", "bỏng rát", "điện giật": Bác sĩ hỏi nhẹ nhàng: "Cơn đau của anh/chị có cảm giác nóng rát, giật thót như điện, hay râm ran như kiến bò không?".
   - Khi mục tiêu ("{current_focus}") liên quan đến "tâm lý", "giấc ngủ", "trầm cảm": Bác sĩ gặng hỏi thấu cảm: "Cơn đau kéo dài này có làm anh/chị bị mất ngủ về đêm hay cảm thấy mệt mỏi, lo lắng nhiều không?".

7. TUYỆT ĐỐI KHÔNG XƯỚNG TÊN NGHIỆM PHÁP KHOA HỌC:
   - Cấm xướng tên nghiệm pháp tiếng Anh (Neer, Hawkins, Lasegue...) hay nói từ "dương tính/âm tính" trực tiếp với bệnh nhân. Khi khám, chỉ mô tả động tác nhẹ nhàng bằng lời thường ("Bác nâng tay lên từ từ... bác thấy đau chỗ nào?").
8. KÊ ĐƠN THUỐC ĐẦY ĐỦ 4 NHÓM:
   - Bác sĩ đọc rõ ràng tên các nhóm thuốc chính (kháng viêm, giãn cơ, giảm đau, bọc dạ dày), hàm lượng và dặn uống sau ăn no.
9. CHỈ LỜI NÓI CẤT THÀNH TIẾNG (TTS SẠCH 100%):
   - Tuyệt đối không chứa chú thích hành động hay dấu ngoặc đơn (), ngoặc vuông [].
10. ĐỊNH DẠNG ĐẦU RA JSON BẮT BUỘC:
Hãy trả về DUY NHẤT một JSON hợp lệ:
{{
  "text": "Lời phát ngôn trực tiếp của Bác sĩ (tối đa 20 từ, không kèm tiền tố tên)",
  "is_parsed": true,
  "reason": "Giải thích ngắn vì sao lượt này có thể hoặc không thể chèn Vâng/Dạ"
}}"""

    raw = call_llm(prompt)
    payload = extract_json_payload(raw)
    if payload and "text" in payload:
        raw_text = str(payload["text"])
        is_parsed = bool(payload.get("is_parsed", False))
    else:
        raw_text = raw
        is_parsed = ("?" not in raw_text) and (len(raw_text.split(".")) >= 2)

    text = sanitize_spoken_text(raw_text)

    new_turn: DialogueTurn = {
        "turn_id": turn_num,
        "speaker": "physician",
        "speaker_name": doc_display,
        "text": text,
        "covered_item": current_focus,
        "timestamp": None,
        "is_parsed": is_parsed
    }
    parse_tag = "[Splittable]" if is_parsed else "[Solid]"
    print(f"  [Lượt {turn_num}] 🩺 {doc_display} {parse_tag}: {text[:80]}...", flush=True)

    return {
        "turns": [new_turn],
        "current_turn_count": turn_num
    }
