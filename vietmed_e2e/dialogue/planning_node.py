# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/planning_node.py
Planning Module cho Dialogue Simulation tích hợp Fog of War:
1. Trích xuất Ordered Checklist gồm 12-14 mục lâm sàng theo đúng tiến trình khám chuẩn.
2. Sinh song song reveal_sequence để điều phối mở khóa thông tin tiền sử cho Patient-LLM.
"""

import re
import json
from typing import Dict, Any, List

from vietmed_e2e.schemas.state import E2EState
from vietmed_e2e.agents.llm_client import call_llm, extract_json

def _build_default_reveal_sequence(checklist: List[str]) -> List[Dict[str, Any]]:
    """Tự động xây dựng reveal_sequence từ danh sách checklist bằng quy tắc heuristic."""
    seq = []
    for item in checklist:
        it_lower = item.lower()
        keys = []
        detail = ""

        if any(w in it_lower for w in ["lý do", "triệu chứng", "khởi phát", "đau"]):
            keys.extend(["chief_complaint", "onset_duration"])
            detail = "Bệnh nhân mô tả cảm giác đau và thời gian bắt đầu bị"

        if any(w in it_lower for w in ["tiền sử", "bệnh nền", "mạn tính"]):
            keys.append("chronic_conditions")
            detail = "Bệnh nhân kể về các bệnh nền đang theo dõi"

        if any(w in it_lower for w in ["thói quen", "sinh hoạt", "nghề", "thể thao", "tư thế"]):
            keys.append("lifestyle_risk_factors")
            detail = "Bệnh nhân chia sẻ về công việc và tư thế gây tăng đau"

        if any(w in it_lower for w in ["tự điều trị", "ở nhà", "xoa bóp", "dầu", "cao", "giảm đau"]):
            keys.append("prior_pain_treatments")
            detail = "Bệnh nhân chia sẻ cách tự chữa tạm thời tại nhà"

        if any(w in it_lower for w in ["chấn thương", "ngã", "mổ", "tai nạn"]):
            keys.append("past_surgeries_trauma")
            detail = "Bệnh nhân kể lại phẫu thuật hoặc chấn thương cũ nếu có"

        if any(w in it_lower for w in ["kê đơn", "đơn thuốc", "thuốc", "dị ứng"]):
            keys.extend(["current_medications", "allergies_intolerances"])
            detail = "Bệnh nhân trao đổi về thuốc đang dùng và tiền sử dị ứng"

        if any(w in it_lower for w in ["danh tính", "đối chiếu họ tên", "họ tên, số tuổi", "xác nhận danh tính"]):
            keys.append("patient_identity")
            detail = "Bác sĩ và bệnh nhân đối chiếu xác nhận họ tên và số tuổi"

        if any(w in it_lower for w in ["thang điểm", "vas", "cường độ đau", "mấy điểm"]):
            keys.append("pain_intensity_vas")
            detail = "Bệnh nhân lượng hóa mức độ đau theo thang điểm số 0-10"

        if any(w in it_lower for w in ["đặc tính đau", "dn4", "likert", "bỏng rát", "điện giật", "tê bì", "kim châm", "râm ran"]):
            keys.append("pain_quality_dn4")
            detail = "Bệnh nhân mô tả các đặc tính cảm giác đau chuyên sâu"

        if any(w in it_lower for w in ["tâm lý", "trầm cảm", "giấc ngủ", "bdi", "lo âu", "tâm trạng"]):
            keys.append("mental_sleep_impact")
            detail = "Bệnh nhân chia sẻ về ảnh hưởng của cơn đau đến giấc ngủ và tâm trạng"

        seq.append({
            "checklist_item": item,
            "reveal_keys": list(set(keys)),
            "reveal_detail": detail or "Khám và phản hồi theo diễn tiến lâm sàng"
        })
    return seq


def planning_node(state: E2EState) -> Dict[str, Any]:
    """
    Planning Module:
    Trích xuất checklist lâm sàng (12-14 mục) và reveal_sequence (Fog of War mapping).
    """
    clinical_note = state["clinical_note"]
    disease_name = state["disease_name"]
    duration_min = state.get("duration_minutes", 12)
    med_history = state.get("medical_history_data", {})
    if not med_history:
        med_history = state.get("patient_profile", {}).get("medical_history", {})
    has_prior = med_history.get("has_prior_medical_visit", False)
    doctor_asks_prior_visit = med_history.get("doctor_asks_prior_visit")
    if doctor_asks_prior_visit is None:
        doctor_asks_prior_visit = True if has_prior else (random.random() < 0.6)

    pat = state.get("patient_profile", {}) or state.get("final_patient", {})
    confirm_identity = pat.get("confirm_identity", True)

    identity_rule = ""
    if confirm_identity:
        identity_rule = """(0) XÁC NHẬN DANH TÍNH BỆNH NHÂN: BẮT BUỘC MỤC ĐẦU TIÊN CỦA CHECKLIST PHẢI LÀ:
       "Xác nhận danh tính: Bác sĩ chào hỏi và đối chiếu họ tên, số tuổi của bệnh nhân" (reveal_keys: ["patient_identity"]). Sau đó mục tiếp theo mới là Lý do khám & khởi phát."""
    else:
        identity_rule = """(0) Bác sĩ vào thẳng chào hỏi và khai thác lý do đến khám (Mục 1: "Lý do khám: Chào hỏi, khai thác triệu chứng khó chịu chính và thời điểm khởi phát")."""

    prior_visit_rule = ""
    if has_prior:
        prior_visit_rule = """- BỆNH NHÂN ĐÃ TỪNG ĐI KHÁM TRƯỚC ĐÓ: BẮT BUỘC TRONG CHECKLIST PHẢI CÓ ĐỦ 2 MỤC LIÊN TIẾP Ở PHẦN TIỀN SỬ:
   (Mục A) "Tiền sử thăm khám trước đây: Hỏi cơ sở y tế đã khám và chẩn đoán khi đó" (reveal_keys: ["previous_medical_visits"])
   (Mục B) "Đánh giá điều trị trước đây: Hỏi biện pháp điều trị khi đó là gì, có hiệu quả không và bệnh nhân đã theo phác đồ bao lâu" (reveal_keys: ["previous_medical_visits"])"""
    elif doctor_asks_prior_visit:
        prior_visit_rule = """- BẮT BUỘC TRONG CHECKLIST: Phải có 1 mục: "Tiền sử thăm khám trước đây: Hỏi bệnh nhân đã từng đi khám ở bệnh viện hoặc phòng khám nào trước đây chưa" (reveal_keys: ["previous_medical_visits"])."""
    else:
        prior_visit_rule = "- Bác sĩ không cần hỏi về tiền sử đi khám bệnh viện trước đây trong ca này."
    target_turns = state.get("target_turns", 28)


    # Phân tầng quy mô Checklist theo độ dài kịch bản (target_turns)
    if target_turns >= 50:
        checklist_size_instruction = """1. Trích xuất một DANH SÁCH KIỂM TRA TOÀN DIỆN (COMPREHENSIVE CHECKLIST) gồm từ 20 đến 24 mục lâm sàng chuyên sâu (dành cho kịch bản dài 50-60 lượt khám toàn diện).
   Bao gồm đầy đủ các trục:
   {identity_rule}
   (1) Triệu chứng khởi phát đau & hoàn cảnh xuất hiện.
   (2) Đo lường cường độ đau theo thang điểm VAS 0-10: Bác sĩ hỏi điểm đau hiện tại (0-10) và điểm đau lúc dữ dội nhất trong 4 tuần qua.
   (3) Đánh giá đặc tính đau theo thang DN4/Likert 6 mức độ: Hỏi cụ thể về cảm giác bỏng rát, buốt lạnh, điện giật, râm ran kiến bò, đau khi chạm nhẹ đồ áo.
   (4) Đánh giá tác động tâm lý & giấc ngủ: Ảnh hưởng của cơn đau kéo dài đến giấc ngủ và tâm trạng (thang BDI / lo âu mạn tính).
   (5) Khai thác tiền sử thói quen, nghề nghiệp, tư thế làm việc và chấn thương cũ.
   (6) Khai thác tiền sử bệnh nền chuyển hóa/tim mạch: Tăng huyết áp, tiểu đường, tiền sử dùng thuốc chống đông máu.
   (7) {prior_visit_rule}
   (8) Khám thực thể toàn diện: Khám điểm đau chói, tầm vận động (ROM), nghiệm pháp chuyên khoa và kiểm tra cảm giác cục bộ.
   (9) Phân tích chi tiết kết quả Cận lâm sàng (X-quang / MRI / Xét nghiệm).
   (10) Kê đơn thuốc chi tiết 4 nhóm, dặn dò tác dụng phụ, bảo vệ dạ dày và kiểm tra kỹ dị ứng thuốc.
   (11) Kế hoạch điều trị đa mô thức chi tiết: Bài tập phục hồi chức năng từng giai đoạn và lịch hẹn tái khám định kỳ."""
    elif target_turns >= 38:
        checklist_size_instruction = """1. Trích xuất một DANH SÁCH KIỂM TRA MỞ RỘNG (EXTENDED CHECKLIST) gồm từ 16 đến 18 mục lâm sàng (dành cho kịch bản 38-48 lượt).
   Bao gồm:
   {identity_rule}
   (1) Triệu chứng khởi phát đau & hoàn cảnh xuất hiện.
   (2) Đo lường cường độ đau theo thang điểm VAS 0-10: Bác sĩ hỏi điểm đau hiện tại và điểm đau lúc dữ dội nhất trong 4 tuần qua.
   (3) Đánh giá đặc tính cơn đau (buốt, nhói, đau về đêm, yếu cơ).
   (4) Khai thác tiền sử bệnh nền tim mạch/chống đông, dị ứng, chấn thương cũ.
   (5) {prior_visit_rule}
   (6) Khám thực thể & nghiệm pháp vận động.
   (7) Giải thích kết quả Cận lâm sàng (X-quang / MRI).
   (8) Kê đơn thuốc chi tiết 4 nhóm, bảo vệ dạ dày, dặn dò vật lý trị liệu và lịch tái khám."""
    else:
        checklist_size_instruction = """1. Trích xuất một DANH SÁCH KIỂM TRA CỐT LÕI (CORE CHECKLIST) gồm từ 12 đến 14 mục lâm sàng (dành cho ca khám tiêu chuẩn ~28-36 lượt).
   Bao gồm:
   {identity_rule}
   (1) Triệu chứng khởi phát đau & hoàn cảnh xuất hiện.
   (2) Khai thác tiền sử thói quen, sinh hoạt, nghề nghiệp, chấn thương cũ.
   (3) {prior_visit_rule}
   (4) Khám thực thể & nghiệm pháp vận động.
   (5) Giải thích kết quả Cận lâm sàng (X-quang / MRI / Xét nghiệm).
   (6) Kê đơn thuốc chi tiết 4 nhóm (kháng viêm, giãn cơ, giảm đau, bọc dạ dày) và dặn dò phục hồi chức năng, tái khám."""

    checklist_size_instruction = checklist_size_instruction.format(
        identity_rule=identity_rule,
        prior_visit_rule=prior_visit_rule
    )

    prompt = f"""Áp dụng quy tắc khám bệnh lâm sàng để lập kế hoạch thăm khám và cơ chế Sương mù thông tin (Fog of War) cho ca bệnh:
Tên Bệnh lý (Disease Name): {disease_name}
Thời lượng dự kiến: {duration_min} phút (Số lượt thoại mục tiêu: {target_turns} lượt)

Hồ sơ Y khoa Ground Truth (Clinical Note):
{clinical_note}

=== QUY TẮC LẬP KẾ HOẠCH & FOG OF WAR (PLANNING RULES) ===
{checklist_size_instruction}
2. Xây dựng REVEAL_SEQUENCE:
   Với mỗi mục checklist, xác định những trường tiền sử của bệnh nhân được phép 'mở khóa' (reveal) cho bệnh nhân nói ra:
   Các trường có thể mở:
   - "chief_complaint", "onset_duration": Lý do khám, thời gian bị
   - "chronic_conditions": Bệnh mạn tính nền
   - "current_medications": Thuốc đang uống
   - "prior_pain_treatments": Cách tự chữa ở nhà
   - "past_surgeries_trauma": Mổ / chấn thương cũ
   - "allergies_intolerances": Dị ứng
   - "lifestyle_risk_factors": Thói quen sinh hoạt, tư thế làm việc
   - "previous_medical_visits": Lịch sử đi khám ở BV/PK trước đó
   - "pain_intensity_vas": Thang điểm đau VAS (0-10)
   - "pain_quality_dn4": Đặc tính cảm giác đau theo thang DN4/Likert
   - "mental_sleep_impact": Ảnh hưởng tâm lý & giấc ngủ

3. YÊU CẦU ĐỊNH DẠNG ĐẦU RA JSON BẮT BUỘC:

Trả về DUY NHẤT một JSON hợp lệ có dạng:
{{
  "checklist": [
    "Lý do khám: Đau nhức khớp vai phải khi vận động",
    "Tính chất đau: Tăng dữ dội về đêm, nhức buốt",
    "Yếu tố tăng giảm: Đau khi với tay lên cao",
    "Tiền sử thói quen: Chơi thể thao, tư thế làm việc",
    "Tiền sử thăm khám trước đây: Hỏi cơ sở y tế đã khám và chẩn đoán khi đó",
    "Đánh giá điều trị trước đây: Hỏi phương pháp điều trị đã áp dụng, mức độ hiệu quả và thời gian duy trì hoặc tái phát",
    "Tiền sử điều trị tại nhà: Xoa bóp, dán cao",
    "Khám thực thể: Kiểm tra điểm đau và biên độ khớp",
    "Giải thích hình ảnh: Kết quả siêu âm / MRI",
    "Chẩn đoán xác định: Viêm quanh khớp vai",
    "Kê đơn thuốc: Kháng viêm, giảm đau, giãn cơ, bảo vệ dạ dày",
    "Tư vấn kiêng cữ và hướng dẫn bài tập tại nhà",
    "Dặn dò tái khám và lưu ý dấu hiệu bất thường"
  ],
  "reveal_sequence": [
    {{
      "checklist_item": "Lý do khám: Đau nhức khớp vai phải khi vận động",
      "reveal_keys": ["chief_complaint", "onset_duration"],
      "reveal_detail": "Bệnh nhân mô tả đau và thời gian"
    }},
    {{
      "checklist_item": "Tiền sử thói quen: Chơi thể thao, tư thế làm việc",
      "reveal_keys": ["lifestyle_risk_factors", "chronic_conditions"],
      "reveal_detail": "Bệnh nhân chia sẻ công việc và bệnh nền"
    }},
    {{
      "checklist_item": "Tiền sử thăm khám trước đây: Hỏi cơ sở y tế đã khám và chẩn đoán khi đó",
      "reveal_keys": ["previous_medical_visits"],
      "reveal_detail": "Bệnh nhân chia sẻ về bệnh viện đã khám và chẩn đoán cũ"
    }},
    {{
      "checklist_item": "Đánh giá điều trị trước đây: Hỏi phương pháp điều trị đã áp dụng, mức độ hiệu quả và thời gian duy trì hoặc tái phát",
      "reveal_keys": ["previous_medical_visits"],
      "reveal_detail": "Bệnh nhân chia sẻ về phương pháp điều trị cũ, hiệu quả và thời gian theo phác đồ"
    }},
    {{
      "checklist_item": "Tiền sử điều trị tại nhà: Xoa bóp, dán cao",
      "reveal_keys": ["prior_pain_treatments"],
      "reveal_detail": "Bệnh nhân kể cách tự chữa"
    }},
    {{
      "checklist_item": "Kê đơn thuốc: Kháng viêm, giảm đau, giãn cơ, bảo vệ dạ dày",
      "reveal_keys": ["current_medications", "allergies_intolerances"],
      "reveal_detail": "Bệnh nhân trao đổi về thuốc đang dùng và dị ứng"
    }}
  ]
}}"""

    raw = call_llm(prompt)
    checklist: List[str] = []
    reveal_sequence: List[Dict[str, Any]] = []

    parsed = extract_json(raw)
    if isinstance(parsed, dict):
        checklist = parsed.get("checklist", [])
        reveal_sequence = parsed.get("reveal_sequence", [])
    elif isinstance(parsed, list):
        checklist = parsed

    # Fallback nếu JSON parse không ra checklist đầy đủ
    if not checklist or len(checklist) < 5:
        print(f"[PlanningNode] Thử regex line fallback cho checklist...", flush=True)
        lines = [l.strip().lstrip("-*0123456789. ") for l in raw.split("\n") if l.strip()]
        checklist = [l for l in lines if len(l) > 5 and not l.startswith("{") and not l.startswith("}")][:14]

    if not checklist:
        checklist = [
            f"Lý do khám: Triệu chứng khởi phát của {disease_name}",
            "Vị trí và tính chất cảm giác khó chịu",
            "Mức độ ảnh hưởng đến sinh hoạt hàng ngày",
            "Tiền sử bệnh và yếu tố nguy cơ liên quan",
            "Thao tác khám vận động và kiểm tra cảm giác đau",
            "Kết quả xét nghiệm và chẩn đoán hình ảnh",
            f"Chẩn đoán xác định: {disease_name}",
            "Kê đơn thuốc chi tiết: Tên thuốc, liều dùng và hướng dẫn uống sau ăn",
            "Dặn dò kiêng cữ tại nhà, phục hồi chức năng và lịch tái khám"
        ]

    # Bảo đảm mục thăm khám trước đây xuất hiện đầy đủ theo điều kiện
    if has_prior:
        has_item1 = any(any(kw in c.lower() for kw in ["tiền sử thăm khám", "đã từng đi khám", "đã khám ở đâu", "cơ sở y tế đã khám", "thăm khám trước"]) for c in checklist)
        has_item2 = any(any(kw in c.lower() for kw in ["đánh giá điều trị", "điều trị trước", "điều trị cũ", "phương pháp điều trị", "hiệu quả điều trị"]) for c in checklist)

        insert_idx = min(4, len(checklist))
        for i, c in enumerate(checklist):
            if any(w in c.lower() for w in ["khám thực thể", "kiểm tra", "nghiệm pháp", "quan sát", "sờ nắn", "tầm vận động"]):
                insert_idx = i
                break

        if not has_item1:
            item1_name = "Tiền sử thăm khám trước đây: Hỏi cơ sở y tế đã khám và chẩn đoán khi đó"
            checklist.insert(insert_idx, item1_name)
            insert_idx += 1
            reveal_sequence.append({
                "checklist_item": item1_name,
                "reveal_keys": ["previous_medical_visits"],
                "reveal_detail": "Bệnh nhân chia sẻ về cơ sở y tế đã khám và chẩn đoán trước đây"
            })

        if not has_item2:
            item2_name = "Đánh giá điều trị trước đây: Hỏi biện pháp điều trị khi đó là gì, có hiệu quả không và bệnh nhân đã theo phác đồ bao lâu"
            idx_after_item1 = insert_idx
            for i, c in enumerate(checklist):
                if any(kw in c.lower() for kw in ["tiền sử thăm khám", "đã từng đi khám", "đã khám ở đâu", "cơ sở y tế đã khám", "thăm khám trước"]):
                    idx_after_item1 = i + 1
                    break
            checklist.insert(idx_after_item1, item2_name)
            reveal_sequence.append({
                "checklist_item": item2_name,
                "reveal_keys": ["previous_medical_visits"],
                "reveal_detail": "Bệnh nhân chia sẻ về biện pháp điều trị cũ, mức độ hiệu quả và thời gian theo phác đồ"
            })
    elif doctor_asks_prior_visit:
        has_prior_item = any(any(kw in c.lower() for kw in ["thăm khám trước", "đã từng đi khám", "đã khám ở đâu", "từng đi khám", "khám trước đây"]) for c in checklist)
        if not has_prior_item:
            insert_idx = min(4, len(checklist))
            for i, c in enumerate(checklist):
                if any(w in c.lower() for w in ["khám thực thể", "kiểm tra", "nghiệm pháp", "quan sát", "sờ nắn", "tầm vận động"]):
                    insert_idx = i
                    break
            prior_item_name = "Tiền sử thăm khám trước đây: Hỏi bệnh nhân đã từng đi khám ở bệnh viện hoặc phòng khám nào trước đây chưa"
            checklist.insert(insert_idx, prior_item_name)
            reveal_sequence.append({
                "checklist_item": prior_item_name,
                "reveal_keys": ["previous_medical_visits"],
                "reveal_detail": "Bệnh nhân xác nhận lần đầu đi khám chuyên khoa"
            })

    # Bảo đảm mục xác nhận danh tính xuất hiện ở vị trí đầu tiên nếu confirm_identity == True
    if confirm_identity:
        has_identity_item = any(any(kw in c.lower() for kw in ["xác nhận danh tính", "đối chiếu họ tên", "họ tên, số tuổi", "thông tin hành chính"]) for c in checklist)
        if not has_identity_item:
            item_identity_name = "Xác nhận danh tính: Bác sĩ chào hỏi và đối chiếu họ tên, số tuổi của bệnh nhân"
            checklist.insert(0, item_identity_name)
            reveal_sequence.insert(0, {
                "checklist_item": item_identity_name,
                "reveal_keys": ["patient_identity"],
                "reveal_detail": "Bệnh nhân xác nhận họ tên và số tuổi"
            })

    # Nếu reveal_sequence trống, tự động xây dựng bằng heuristic
    if not reveal_sequence:
        reveal_sequence = _build_default_reveal_sequence(checklist)

    print(f"\n[Planning] Đã trích xuất {len(checklist)} mục checklist lâm sàng & {len(reveal_sequence)} quy tắc Fog of War:", flush=True)
    for idx, c in enumerate(checklist, 1):
        print(f"   {idx}. {c}", flush=True)

    first_focus = checklist[0] if checklist else None
    initial_revealed = ["patient_identity", "chief_complaint", "onset_duration", "occupation"]

    return {
        "checklist": checklist,
        "completed_checklist": [],
        "current_focus": first_focus,
        "reveal_sequence": reveal_sequence,
        "revealed_keys": initial_revealed,
        "turns": [],
        "current_turn_count": 0,
        "is_finished": False
    }
