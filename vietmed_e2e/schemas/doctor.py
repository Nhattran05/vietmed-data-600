# -*- coding: utf-8 -*-
"""
src/schemas/doctor.py
Pydantic Schema cho Doctor Profile (Đúng 6 trường chuẩn).
"""

from typing import Optional
from pydantic import BaseModel, Field

class DoctorProfile(BaseModel):
    name: str = Field(..., description="Họ và tên bác sĩ (kèm danh xưng, ví dụ: 'Bác sĩ Dũng')")
    gender: str = Field(..., description="Giới tính ('Nam' hoặc 'Nữ')")
    age: int = Field(..., description="Độ tuổi của bác sĩ")
    seniority_level: str = Field(..., description="Cấp bậc / Thâm niên (ví dụ: 'Bác sĩ Chuyên khoa II / Trưởng khoa (26 năm kinh nghiệm)')")
    speciality: str = Field(..., description="Chuyên khoa điều trị chính")
    communication_tone: str = Field(..., description="Giọng điệu giao tiếp đặc thù của bác sĩ")
    display_name: Optional[str] = Field(None, description="Tên xưng hô ngắn gọn trong kịch bản (ví dụ: 'Bác sĩ Hà')")
