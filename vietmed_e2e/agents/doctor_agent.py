# -*- coding: utf-8 -*-
"""
src/agents/doctor_agent.py
Sub-Agent phụ trách tạo Doctor Profile (Đúng 6 trường chuẩn + Display Name).
Tự động ánh xạ:
- Disease / Category -> Speciality
- Seniority Level -> Communication Tone
- Sinh Full Name Bác sĩ (Bác sĩ Nguyễn Văn Minh, Bác sĩ Trần Thị Thu Hà...) và Display Name ngắn gọn.
"""

import random
from typing import Dict, Any, Optional

DOCTOR_LAST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Phan", "Đặng", "Bùi", "Đỗ"]
DOCTOR_MALE_MIDDLE = ["Văn", "Đức", "Minh", "Quang", "Thành", "Đình", "Quốc", "Hữu"]
DOCTOR_FEMALE_MIDDLE = ["Thị", "Thu", "Thanh", "Ngọc", "Phương", "Mai", "Kim", "Thùy"]

DOCTOR_MALE_NAMES = ["Minh", "Hoàng", "Tuấn", "Dũng", "Trung", "Hải", "Khánh", "Thành", "Bách", "Đức", "Cường", "Trí"]
DOCTOR_FEMALE_NAMES = ["Linh", "Thảo", "Hương", "Trang", "Mai", "Anh", "Quỳnh", "Thanh", "Phương", "Hà", "Yến", "Ngọc"]

SPECIALTY_MAPPING = {
    "I. Vai – Cánh tay – Khuỷu – Cổ tay – Bàn tay": "Cơ Xương Khớp / Bàn tay & Chi trên",
    "II. Cột sống cổ – Lưng": "Cơ Xương Khớp / Cột Sống",
    "III. Hông – Gối – Cổ chân – Bàn chân": "Cơ Xương Khớp / Chi dưới",
    "IV. Toàn thân – Chuyển hóa – Tự miễn": "Cơ Xương Khớp / Miễn dịch & Chuyển hóa",
    "V. Đầu – Mặt – Thần kinh": "Nội Thần Kinh",
    "VI. Bụng – Nội tạng": "Nội Tiêu Hóa",
    "VII. U/bệnh lý xương gây đau": "Cơ Xương Khớp / Ung bướu Chỉnh hình"
}

TONES_BY_SENIORITY = {
    "senior": [
        "Điềm đạm, giải thích rõ ràng cơ chế mòn/viêm bằng hình ảnh đời thường, kiên nhẫn lắng nghe",
        "Dứt khoát, giàu kinh nghiệm, nghiêm khắc chấn chỉnh việc tự ý dùng thuốc quá liều",
        "Ân cần, thấu cảm, giải thích cặn kẽ tầm quan trọng sống còn của việc tuân thủ phác đồ"
    ],
    "specialist": [
        "Nghiêm cẩn, sắc sảo, kiên nhẫn gặng hỏi thói quen sinh hoạt và việc dùng thuốc không rõ nguồn gốc",
        "Đĩnh đạc, ân cần, giải thích nguyên nhân bằng hình ảnh đời thường, kiên nhẫn gặng hỏi từng động tác đau",
        "Thực tế, logic chặt chẽ, chú trọng hướng dẫn thay đổi thói quen sinh hoạt và bài tập phục hồi tại nhà"
    ],
    "resident": [
        "Nhẹ nhàng, cẩn trọng, từ tốn, tạo cảm giác an tâm và thoải mái khi trao đổi triệu chứng nhạy cảm",
        "Tế nhị, thấu cảm, không phán xét thói quen xấu của bệnh nhân, hướng dẫn phòng ngừa tái phát tỉ mỉ"
    ]
}

def generate_doctor_profile(
    kb_entry: Dict[str, Any],
    patient_data: Optional[Dict[str, Any]] = None,
    doctor_name: Optional[str] = None,
    gender: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Sinh hồ sơ Bác sĩ chuẩn theo chuyên khoa với Full Name và Display Name."""
    if gender is None:
        if doctor_name:
            name_clean = doctor_name.replace("Bác sĩ", "").strip()
            if any(name_clean in m for m in DOCTOR_MALE_NAMES):
                gender = "Nam"
            elif any(name_clean in f for f in DOCTOR_FEMALE_NAMES):
                gender = "Nữ"
            else:
                # Phân phối thực tế y tế VN: ~55% Nam, ~45% Nữ
                gender = random.choices(["Nam", "Nữ"], weights=[55, 45], k=1)[0]
        else:
            gender = random.choices(["Nam", "Nữ"], weights=[55, 45], k=1)[0]

    last_name = random.choice(DOCTOR_LAST_NAMES)
    if gender == "Nam":
        first_name = random.choice(DOCTOR_MALE_NAMES)
        middle_name = random.choice(DOCTOR_MALE_MIDDLE)
    else:
        first_name = random.choice(DOCTOR_FEMALE_NAMES)
        middle_name = random.choice(DOCTOR_FEMALE_MIDDLE)

    full_name_generated = f"Bác sĩ {last_name} {middle_name} {first_name}"
    display_name_generated = f"Bác sĩ {first_name}"

    if doctor_name is not None:
        clean_parts = doctor_name.replace("Bác sĩ", "").strip().split()
        if len(clean_parts) >= 2:
            full_doctor_name = doctor_name if doctor_name.startswith("Bác sĩ") else f"Bác sĩ {doctor_name}"
            display_doctor_name = f"Bác sĩ {clean_parts[-1]}"
        elif len(clean_parts) == 1 and clean_parts[0]:
            first_name = clean_parts[0]
            full_doctor_name = f"Bác sĩ {last_name} {middle_name} {first_name}"
            display_doctor_name = f"Bác sĩ {first_name}"
        else:
            full_doctor_name = full_name_generated
            display_doctor_name = display_name_generated
    else:
        full_doctor_name = full_name_generated
        display_doctor_name = display_name_generated

    # Phân phối tuổi bác sĩ đều hơn qua 3 tầng: trẻ (35-42), trung (43-49), cao niên (50-56)
    age_tier = random.choices(
        [(35, 42), (43, 49), (50, 56)],
        weights=[35, 40, 25],  # 35% trẻ, 40% trung niên, 25% cao niên
        k=1
    )[0]
    age = random.randint(age_tier[0], age_tier[1])
    exp = age - 26

    if age >= 48:
        seniority = f"Bác sĩ Chuyên khoa II / Trưởng khoa ({exp} năm kinh nghiệm)"
        tone = random.choice(TONES_BY_SENIORITY["senior"])
    elif age >= 40:
        seniority = f"Bác sĩ Chuyên khoa I ({exp} năm kinh nghiệm)"
        tone = random.choice(TONES_BY_SENIORITY["specialist"])
    else:
        seniority = f"Bác sĩ điều trị ({exp} năm kinh nghiệm)"
        tone = random.choice(TONES_BY_SENIORITY["resident"])

    category = kb_entry.get("category", "")
    specialty = SPECIALTY_MAPPING.get(category, category if category else "Cơ Xương Khớp")

    return {
        "name": full_doctor_name,            # Họ tên đầy đủ: "Bác sĩ Trần Thị Thu Hà"
        "display_name": display_doctor_name, # Tên xưng hô kịch bản: "Bác sĩ Hà"
        "gender": gender,
        "age": age,
        "seniority_level": seniority,
        "speciality": specialty,
        "communication_tone": tone
    }
