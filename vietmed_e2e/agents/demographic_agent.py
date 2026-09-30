# -*- coding: utf-8 -*-
"""
src/agents/demographic_agent.py
Sub-Agent phụ trách suy luận Nhân khẩu học (Full Name, Display Name, Gender, Age, Occupation, Address, Confirm Identity)
bám sát dịch tễ học và nguyên nhân từ file 60 bệnh chuẩn.
"""

import random
from typing import Dict, Any, Optional

VIETNAMESE_LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"
]

MALE_MIDDLE_NAMES = ["Văn", "Hữu", "Đức", "Quang", "Minh", "Đình", "Xuân", "Thành", "Tuấn", "Quốc"]
FEMALE_MIDDLE_NAMES = ["Thị", "Thu", "Thanh", "Ngọc", "Phương", "Hải", "Mai", "Kim", "Thùy", "Ánh"]

MALE_FIRST_NAMES = [
    "Hùng", "Tuấn", "Dũng", "Nam", "Hải", "Đức", "Cường", "Trí",
    "Thành", "Bách", "Bình", "Long", "Phong", "Trung", "Kiên"
]
FEMALE_FIRST_NAMES = [
    "Lan", "Hoa", "Mai", "Phương", "Thảo", "Hương", "Trang", "Anh",
    "Linh", "Yến", "Hà", "Ngọc", "Hạnh", "Dung", "Thúy"
]

HANOI_COMMUNES = [
    "Xã Tiền Phong, Mê Linh, Hà Nội",
    "Xã Kim Chung, Đông Anh, Hà Nội",
    "Xã An Khánh, Hoài Đức, Hà Nội",
    "Xã Tân Triều, Thanh Trì, Hà Nội",
    "Xã Bát Tràng, Gia Lâm, Hà Nội",
    "Xã Phù Đổng, Gia Lâm, Hà Nội",
    "Xã Ninh Hiệp, Gia Lâm, Hà Nội",
    "Xã Vân Canh, Hoài Đức, Hà Nội",
    "Xã Cổ Bi, Gia Lâm, Hà Nội",
    "Xã Tam Hiệp, Thanh Trì, Hà Nội",
    "Xã Hải Bối, Đông Anh, Hà Nội",
    "Xã Thạch Hòa, Thạch Thất, Hà Nội",
    "Xã Phú Cát, Quốc Oai, Hà Nội",
    "Xã Thanh Liệt, Thanh Trì, Hà Nội",
    "Xã Đông Hội, Đông Anh, Hà Nội"
]

def generate_demographics(
    kb_entry: Dict[str, Any],
    age: Optional[int] = None,
    gender: Optional[str] = None,
    occupation: Optional[str] = None,
    patient_name: Optional[str] = None,
    address: Optional[str] = None,
    force_confirm_identity: Optional[bool] = None
) -> Dict[str, Any]:
    """Suy luận nhân khẩu học có căn cứ dịch tễ từ KB và tạo Full Name + Địa chỉ."""
    causes_lower = kb_entry.get("causes", "").lower()
    disease_name_lower = kb_entry.get("name", "").lower()

    # 1. Xác định Giới tính nếu chưa chỉ định
    if gender is None:
        if any(kw in causes_lower or kw in disease_name_lower for kw in ["phụ nữ sau sinh", "mang thai", "kỳ kinh", "lạc nội mạc tử cung", "thống kinh", "mãn kinh"]):
            gender = "Nữ"
        elif any(kw in causes_lower or kw in disease_name_lower for kw in ["tiền liệt tuyến", "gút"]):
            gender = "Nam"
        else:
            gender = random.choice(["Nam", "Nữ"])

    # 2. Xác định Độ tuổi nếu chưa chỉ định
    if age is None:
        if "40-60 tuổi" in causes_lower:
            age = random.randint(45, 58)
        elif "sau sinh" in causes_lower:
            age = random.randint(26, 34)
        elif any(kw in causes_lower for kw in ["thoái hóa theo tuổi", "tuổi tác", "lão hóa", "mãn kinh", "hưu"]):
            age = random.randint(58, 68)
        elif "trẻ" in causes_lower or "thể thao" in causes_lower:
            age = random.randint(22, 35)
        else:
            age = random.randint(35, 58)

    # 3. Tạo Full Name và Display Name
    if gender == "Nam":
        first_name = random.choice(MALE_FIRST_NAMES)
        middle_name = random.choice(MALE_MIDDLE_NAMES)
        honorific = "Bác" if age >= 60 else ("Chú" if age >= 40 else "Anh")
    else:
        first_name = random.choice(FEMALE_FIRST_NAMES)
        middle_name = random.choice(FEMALE_MIDDLE_NAMES)
        honorific = "Bác" if age >= 60 else ("Cô" if age >= 40 else "Chị")

    last_name = random.choice(VIETNAMESE_LAST_NAMES)
    full_name_generated = f"{last_name} {middle_name} {first_name}"
    display_name_generated = f"{honorific} {first_name}"

    if patient_name is not None:
        parts = patient_name.strip().split()
        if len(parts) >= 3:
            full_name = patient_name
            first_name = parts[-1]
            display_name = f"{honorific} {first_name}"
        elif len(parts) == 2:
            honorific = parts[0]
            first_name = parts[1]
            full_name = f"{last_name} {middle_name} {first_name}"
            display_name = f"{honorific} {first_name}"
        elif len(parts) == 1 and parts[0]:
            first_name = parts[0]
            full_name = f"{last_name} {middle_name} {first_name}"
            display_name = f"{honorific} {first_name}"
        else:
            full_name = full_name_generated
            display_name = display_name_generated
    else:
        full_name = full_name_generated
        display_name = display_name_generated

    # 4. Xác định Địa chỉ ngắn gọn: tên xã / Hà Nội
    if address is None:
        address = random.choice(HANOI_COMMUNES)

    # 5. Roll tỉ lệ 70/30 xác nhận danh tính bệnh nhân
    if force_confirm_identity is not None:
        confirm_identity = bool(force_confirm_identity)
    else:
        confirm_identity = random.random() < 0.7  # 70% sẽ hỏi xác nhận

    # 6. Xác định Nghề nghiệp nếu chưa có
    if occupation is None:
        if "tay qua đầu" in causes_lower:
            occupation = "Thợ sơn nhà" if gender == "Nam" else "Thợ may mặc gia công"
        elif "bế trẻ" in causes_lower:
            occupation = "Nhân viên văn phòng đang nuôi con nhỏ"
        elif any(kw in causes_lower for kw in ["đánh máy", "ngồi lâu", "stress"]):
            occupation = "Chuyên viên phân tích tài chính" if gender == "Nữ" else "Lập trình viên (IT)"
        elif any(kw in causes_lower for kw in ["đứng lâu", "mang vác"]):
            occupation = "Tiểu thương bán hàng vải tại chợ" if gender == "Nữ" else "Thợ bốc xếp kho hàng"
        elif "chạy" in causes_lower:
            occupation = "Nhân viên kinh doanh kiêm vận động viên chạy phong trào"
        else:
            occupation = "Lao động tự do"

    return {
        "name": full_name,                # Họ và tên đầy đủ: "Nguyễn Văn Long"
        "display_name": display_name,    # Tên xưng hô kịch bản: "Anh Long"
        "gender": gender,
        "age": age,
        "occupation": occupation,
        "address": address,              # Địa chỉ: "Xã Tiền Phong, Mê Linh, Hà Nội"
        "confirm_identity": confirm_identity # 70% True, 30% False
    }
