# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/polish_node.py
Module 4: LLM Polish Agent Node (Table 13 Polish prompt ACL 2024)
Tiếp nhận toàn bộ hội thoại thô, làm mượt, tự nhiên hóa và đảm bảo nhịp điệu giao tiếp đời thường.
Tích hợp 5 quy tắc NoteChat & Ràng buộc độ dài lý tưởng tối đa 20 từ/lượt.
"""

import re
import json
from typing import Dict, Any, List

from vietmed_e2e.schemas.state import E2EState, DialogueTurn
from vietmed_e2e.agents.llm_client import call_llm
from vietmed_e2e.sanitizer.dialogue_sanitizer import sanitize_spoken_text

def polish_node(state: E2EState) -> Dict[str, Any]:
    """
    Tinh chỉnh toàn bộ hội thoại qua LLM Polish Agent.
    """
    clinical_note = state["clinical_note"]
    checklist = state.get("completed_checklist", []) or state.get("checklist", [])
    keywords = ", ".join(checklist) if checklist else state["disease_name"]
    doc = state.get("doctor_profile", {}) or state.get("final_doctor", {})
    pat = state.get("patient_profile", {}) or state.get("final_patient", {})
    doc_name = doc.get("name", "Bác sĩ")
    doc_display = doc.get("display_name") or doc_name
    pat_name = pat.get("name", "Bệnh nhân")
    pat_display = pat.get("display_name") or pat_name
    raw_turns = state.get("turns", [])

    # Định dạng hội thoại thô cho prompt
    raw_lines = []
    for t in raw_turns:
        role = "physician" if t.get("speaker") in ["physician", "doctor"] else "Patient"
        raw_lines.append(f"{role}: {t.get('text', '')}")
    history_conversation = "\n".join(raw_lines)

    prompt = f"""Mở rộng và làm mượt cuộc trò chuyện khám bệnh giữa Bác sĩ và Bệnh nhân:
Cuộc trò chuyện đối với các phần của bệnh nhân mang tính thông tục đời thường, dùng từ ngữ giác quan thuần Việt.
Tất cả các con số và khái niệm y khoa xuất hiện trong bệnh án phải do bác sĩ giải thích.
Bác sĩ có thể mô tả và giải thích phán đoán chuyên môn cho bệnh nhân và hướng dẫn bệnh nhân về các yêu cầu theo dõi tái khám, nhưng không được hỏi những câu hỏi đòi hỏi kiến thức y khoa chuyên môn để trả lời.
Tất cả thông tin về tiền sử bệnh, triệu chứng và tiền sử dùng thuốc phải do bệnh nhân nói ra.

Hồ sơ Y khoa Ground Truth:
{clinical_note}
Các Từ khóa Cốt lõi (Checklist): {keywords}
Lịch sử Hội thoại Thô:
{history_conversation}

=== QUY TẮC ĐẦU RA BỔ SUNG & NOTECHAT 5 RULES ===
1. QUY TẮC LIỀU LƯỢNG:
   - Rà soát toàn bộ lời thoại của Bệnh nhân: Xóa bỏ hoàn toàn các thông số liều lượng kỹ thuật mg/mcg do Bệnh nhân nói ra. Bệnh nhân chỉ được phép nói tên bệnh hoặc tên thông thường của thuốc đang dùng. Mọi liều lượng chính xác chỉ xuất hiện trong lời Bác sĩ đọc đơn thuốc.
2. BỆNH NHÂN KHÔNG PHÁT NGÔN CHUYÊN MÔN & CẤM TÊN VỊ TRÍ GIẢI PHẪU:
   - Rà soát toàn bộ lời thoại của Bệnh nhân: XÓA BỎ / THAY THẾ toàn bộ các từ chỉ vị trí đau chuyên môn, tên giải phẫu học (CẤM: "mỏm cùng vai", "cơ trên gai", "gân trên gai", "chóp xoay", "cơ liền vai", "liên sườn", "bao hoạt dịch", "L4-L5", "đĩa đệm"...). Thay thế bằng từ ngữ dân dã đời thường: "ở đầu vai", "đỉnh vai này", "khúc này này bác sĩ", "ngang bả vai", "dọc mạn sườn", "ngang thắt lưng".
   - Bệnh nhân không được tự mô tả các thông số MRI/X-quang. Thể hiện tự nhiên: Bệnh nhân đưa phim/sổ khám cho Bác sĩ, và Bác sĩ trực tiếp đọc và giải thích.
3. THU THẬP THÔNG TIN QUA NHIỀU LƯỢT:
   - Không dồn dập liệt kê nhiều bệnh án/triệu chứng trong 1 câu dài. Tách thành nhiều lượt đối thoại hỏi - đáp ngắn gọn, tuần tự giữa bác sĩ và bệnh nhân.
4. MỞ ĐẦU VÀ KẾT THÚC TỰ NHIÊN:
   - Bác sĩ chào hỏi ân cần, hỏi lý do đến khám, hỏi mượn hồ sơ cũ. Phần cuối dặn dò ân cần, bệnh nhân cảm ơn chào ra về.
5. RÀ SOÁT ĐỘ DÀI & ĐỘ TỰ NHIÊN CHO CẢ HAI PHÍA (BẮT BUỘC):
   - Cả Bác sĩ và Bệnh nhân đều phải nói ngắn gọn, tự nhiên, nhịp nhàng (độ dài lý tưởng TỐI ĐA 20 TỪ/LƯỢT, dao động từ 8 đến 20 từ, tối đa không quá 2 câu ngắn).
   - Tuyệt đối không để bất kỳ bên nào độc thoại tràng giang đại hải vượt quá 20 từ.
6. RÀ SOÁT XƯNG HÔ BÁC SĨ (CẤM TỰ XƯNG 'BÁC SĨ' LẶP LẠI TRONG THOẠI):
   - Rà soát toàn bộ lời thoại của Bác sĩ: KHÔNG để bác sĩ tự xưng ngôi thứ ba là "bác sĩ" liên tục trong câu (ví dụ thay thế ngay: "Bác sĩ sẽ chạm nhẹ..." -> "Để tôi chạm nhẹ...", "Bác sĩ sẽ xem kết quả..." -> "Giờ để tôi xem kết quả...", "Bác sĩ nâng cánh tay em..." -> "Để tôi nâng cánh tay em...").
   - Bác sĩ xưng "tôi" - gọi "bác/anh/chị/em" hoặc lược bỏ chủ ngữ tự nhiên khi trao đổi với bệnh nhân.
7. RÀ SOÁT ĐỘ LỊCH THIỆP & XÓA BỎ RÀO ĐÓN KHẲNG ĐỊNH MÁY MÓC CỦA BÁC SĨ (BẮT BUỘC):
   - Rà soát lời thoại Bác sĩ: XÓA BỎ HOÀN TOÀN các câu mở đầu rào đón khẳng định, giải thích mục đích thủ tục máy móc (ví dụ: "Để tôi kê đơn cho chuẩn...", "Để tôi chẩn đoán chính xác...", "Để tôi kiểm tra kỹ...", "Để việc điều trị đạt hiệu quả cao...").
   - Viết lại thành câu hỏi lâm sàng ân cần, nhã nhặn, tôn trọng người bệnh (ví dụ thay "Để tôi kê đơn cho chuẩn, anh có dị ứng thuốc gì không?" thành "Cho tôi hỏi thêm là trước giờ anh có từng bị dị ứng với loại thuốc nào không?").
8. ĐỊNH DẠNG ĐẦU RA YÊU CẦU:
   Trả về DUY NHẤT một mảng JSON hợp lệ chứa danh sách từ 24 đến 36 lượt thoại hoàn chỉnh:
   [
     {{"speaker": "physician", "speaker_name": "{doc_display}", "text": "..."}},
     {{"speaker": "patient", "speaker_name": "{pat_display}", "text": "..."}}
   ]"""

    print(f"\n[Polish Node] Tiếp nhận {len(raw_turns)} lượt thoại thô. Đang gửi sang LLM Polish...", flush=True)
    raw = call_llm(prompt)

    polished_turns: List[DialogueTurn] = []
    # 1. Thử parse mảng JSON
    try:
        m = re.search(r"\[\s*\{.*\}\s*\]", raw, re.DOTALL)
        if m:
            items = json.loads(m.group(0))
            for idx, it in enumerate(items, 1):
                role = "physician" if it.get("speaker", "").lower() in ["physician", "doctor", "bác sĩ"] else "patient"
                s_name = doc_display if role == "physician" else pat_display
                clean_text = sanitize_spoken_text(str(it.get("text", "")).strip())
                if clean_text:
                    polished_turns.append({
                        "turn_id": idx,
                        "speaker": role,
                        "speaker_name": s_name,
                        "text": clean_text,
                        "covered_item": it.get("covered_item"),
                        "timestamp": None,
                        "is_parsed": True
                    })
    except Exception as ex:
        print(f"[Polish Node] JSON parse lỗi: {ex}. Thử regex line fallback...", flush=True)

    # 2. Nếu parse JSON thất bại hoặc ít hơn 10 lượt, thử fallback qua regex từng dòng
    if len(polished_turns) < 10:
        lines = raw.strip().split("\n")
        idx = 1
        for l in lines:
            l_str = l.strip()
            if not l_str:
                continue
            match = re.match(r"^(?:-\s*\*\*)?(physician|bác sĩ|doctor|patient|bệnh nhân)[\*\:]*\s*(.*)$", l_str, re.IGNORECASE)
            if match:
                tag = match.group(1).lower()
                role = "physician" if tag in ["physician", "doctor", "bác sĩ"] else "patient"
                s_name = doc_display if role == "physician" else pat_display
                clean_text = sanitize_spoken_text(match.group(2).strip())
                if clean_text:
                    polished_turns.append({
                        "turn_id": idx,
                        "speaker": role,
                        "speaker_name": s_name,
                        "text": clean_text,
                        "covered_item": None,
                        "timestamp": None,
                        "is_parsed": True
                    })
                    idx += 1

    # 3. Nếu vẫn không parse được, fallback an toàn về raw_turns
    if len(polished_turns) < 10:
        print(f"[Polish Node Warning] Không parse được đủ lượt thoại ({len(polished_turns)}). Sử dụng raw_turns.", flush=True)
        polished_turns = list(raw_turns)
    else:
        print(f"[Polish Node] Tinh chỉnh thành công: {len(polished_turns)} lượt thoại tự nhiên.", flush=True)

    return {
        "polished_turns": polished_turns
    }
