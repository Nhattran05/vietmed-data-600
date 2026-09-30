# -*- coding: utf-8 -*-
"""
vietmed_e2e/dialogue/checklist_update_node.py
Roleplay Module 2b: Checklist Update Node (Dynamic Planning) & Condition Check
Kiểm tra tiến độ hoàn thành các mục checklist lâm sàng và điều hướng lượt thoại tiếp theo.
"""

from typing import Dict, Any, Literal
from vietmed_e2e.schemas.state import E2EState

def checklist_update_node(state: E2EState) -> Dict[str, Any]:
    """
    Kiểm tra xem câu hỏi vừa rồi của Bác sĩ đã bao hàm mục tiêu current_focus chưa.
    Nếu đã bao hàm, chuyển current_focus sang completed_checklist và chọn mục kế tiếp.
    """
    checklist = list(state.get("checklist", []))
    completed = list(state.get("completed_checklist", []))
    current_focus = state.get("current_focus")
    turns = state.get("turns", [])

    # Đếm số lượt bác sĩ đã tập trung vào current_focus
    turns_on_focus = sum(
        1 for t in turns
        if t.get("speaker") == "physician" and t.get("covered_item") == current_focus
    )

    # Mỗi mục lâm sàng Bác sĩ chỉ cần 1 lượt hỏi/khám/kê đơn trọng tâm để tiến sang mục kế tiếp
    if turns_on_focus >= 1 and checklist:
        if checklist[0] == current_focus:
            completed.append(checklist.pop(0))
        elif current_focus in checklist:
            checklist.remove(current_focus)
            completed.append(current_focus)

    if checklist:
        next_focus = checklist[0]
    else:
        next_focus = "Dặn dò chi tiết, giải tỏa lo âu và hướng dẫn theo dõi hồi phục"

    return {
        "checklist": checklist,
        "completed_checklist": completed,
        "current_focus": next_focus
    }

def condition_check(state: E2EState) -> Literal["continue_roleplay", "finish_roleplay"]:
    """
    Điều kiện dừng vòng lặp Roleplay linh hoạt (Checklist-Driven Dynamic Expansion):
    - target_turns là Soft Target (mục tiêu mong muốn).
    - max_hard_limit là trần an toàn tuyệt đối.
    - Vòng lặp dừng khi checklist đã hoàn tất hoặc chạm trần an toàn.
    """
    turns_count = state.get("current_turn_count", 0)
    target = state.get("target_turns", 24)
    max_limit = state.get("max_hard_limit", target + 10)
    checklist = state.get("checklist", [])

    # 1. Chạm trần an toàn tuyệt đối -> Buộc phải kết luận
    if turns_count >= max_limit:
        print(f"\n[Loop Condition] Đã chạm trần an toàn ({turns_count}/{max_limit} lượt). Chuyển sang kết luận.", flush=True)
        return "finish_roleplay"

    # 2. Checklist ĐÃ HOÀN TẤT 100% VÀ đã đạt tối thiểu 70% soft target -> Kết thúc tự nhiên
    has_prescribed = any(
        "đơn thuốc" in c.lower() or "kê đơn" in c.lower() or "thuốc" in c.lower()
        for c in state.get("completed_checklist", [])
    )
    if len(checklist) == 0 and turns_count >= int(target * 0.70):
        if not has_prescribed and turns_count < max_limit:
            print(f"  [Dynamic Expansion] Chưa kê đơn thuốc. Nới rộng vòng lặp để kê đơn thuốc...", flush=True)
            checklist.append("Kê đơn thuốc chi tiết: Đọc rõ từng loại thuốc (kháng viêm, giãn cơ, giảm đau, bảo vệ dạ dày), liều lượng và cách uống sau ăn no")
            return "continue_roleplay"
        print(f"\n[Loop Condition] Đã hoàn tất 100% checklist lâm sàng ({turns_count} lượt). Chuyển sang kết luận.", flush=True)
        return "finish_roleplay"

    # 3. Nếu số lượt đã tiệm cận hoặc vượt target nhưng checklist vẫn còn -> Tự động nới rộng
    if turns_count >= target:
        focus_info = checklist[0] if checklist else "Tổng kết"
        print(f"  [Dynamic Expansion] Đã đạt {turns_count} lượt nhưng checklist còn {len(checklist)} mục ({focus_info}). Tiếp tục...", flush=True)

    return "continue_roleplay"
