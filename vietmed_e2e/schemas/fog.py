# -*- coding: utf-8 -*-
"""
vietmed_e2e/schemas/fog.py
Định nghĩa Schemas cho cơ chế Fog of War (Sương mù thông tin):
Bệnh nhân chỉ được tiết lộ thông tin bệnh án khi Bác sĩ hỏi đúng chủ đề lâm sàng.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RevealItem(BaseModel):
    """
    Một quy tắc mở khóa thông tin trong reveal_sequence:
    Khi checklist_item tương ứng được bác sĩ tiếp cận hoặc hoàn thành,
    các reveal_keys sẽ được mở khóa để Patient-LLM nhìn thấy.
    """
    checklist_item: str = Field(..., description="Tên mục checklist lâm sàng tương ứng")
    reveal_keys: List[str] = Field(default_factory=list, description="Danh sách các trường medical_history được mở khóa")
    reveal_detail: Optional[str] = Field(None, description="Mô tả phạm vi hoặc lưu ý khi tiết lộ cho bệnh nhân")

class FogState(BaseModel):
    """Trạng thái hiện tại của cơ chế Fog of War."""
    revealed_keys: List[str] = Field(default_factory=list, description="Các khóa đã được mở khóa")
    patient_visible_context: str = Field("", description="Văn bản bối cảnh bệnh nhân được phép biết")
    hidden_topics_hint: str = Field("", description="Gợi ý những điều bệnh nhân KHÔNG ĐƯỢC tự ý tiết lộ")
