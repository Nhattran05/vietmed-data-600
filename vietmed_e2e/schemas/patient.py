# -*- coding: utf-8 -*-
"""
src/schemas/patient.py
Pydantic Schemas cho Patient Profile (9 trường chuẩn + Medical History 6 trường con).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChronicCondition(BaseModel):
    condition: str = Field(..., description="Tên bệnh mạn tính / bệnh nền")
    duration: str = Field(..., description="Thời gian mắc bệnh (ví dụ: '5 năm')")
    control_status: str = Field(..., description="Tình trạng kiểm soát (ví dụ: 'Ổn định', 'Chưa kiểm soát')")
    treated_at: Optional[str] = Field("Trạm y tế / Phòng khám", description="Nơi theo dõi điều trị")

class MedicationItem(BaseModel):
    name: str = Field(..., description="Tên hoạt chất / biệt dược chuẩn")
    dosage: str = Field(..., description="Hàm lượng / liều dùng (ví dụ: '5mg', '500mg')")
    frequency: str = Field(..., description="Tần suất & thời điểm uống")
    adherence: str = Field("Tuân thủ tốt", description="Mức độ tuân thủ (uống đều / hay quên)")
    appearance: Optional[str] = Field(None, description="Đặc điểm nhận diện ngoại quan (màu sắc, hình dạng)")

class PriorTreatmentItem(BaseModel):
    treatment: str = Field(..., description="Phương pháp / thuốc tự giảm đau đã dùng ở nhà")
    frequency: Optional[str] = Field("Khi đau", description="Tần suất áp dụng")
    outcome: str = Field(..., description="Kết quả đáp ứng (đỡ tạm thời, không đỡ, tác dụng phụ)")
    warning_flags: Optional[str] = Field(None, description="Cảnh báo nguy cơ lâm sàng nếu có (ví dụ: đau rát thượng vị)")

class SurgeryTraumaItem(BaseModel):
    event: str = Field(..., description="Tên phẫu thuật hoặc chấn thương cũ")
    year: Optional[int] = Field(None, description="Năm xảy ra")
    sequelae: Optional[str] = Field("Hồi phục tốt", description="Di chứng để lại nếu có")

class AllergyItem(BaseModel):
    allergen: str = Field(..., description="Tác nhân dị ứng (thuốc, thức ăn)")
    reaction: str = Field(..., description="Biểu hiện phản ứng dị ứng")
    severity: str = Field("Nhẹ", description="Mức độ nghiêm trọng (Nhẹ / Vừa / Nặng)")

class LifestyleRiskFactors(BaseModel):
    tobacco: str = Field("Không hút thuốc", description="Tiền sử và tần suất hút thuốc lá")
    alcohol: str = Field("Không uống rượu bia", description="Tần suất và mức độ sử dụng rượu bia")
    occupational_posture: str = Field(..., description="Tư thế lao động đặc thù nghề nghiệp")
    daily_water_intake: str = Field("1.5 - 2 lít/ngày", description="Lượng nước uống hàng ngày")

class MedicalHistory(BaseModel):
    source_reference: Optional[str] = Field(None, description="Nguồn trích xuất từ 60 bệnh chuẩn")
    chronic_conditions: List[ChronicCondition] = Field(default_factory=list)
    current_medications: List[MedicationItem] = Field(default_factory=list)
    prior_pain_treatments: List[PriorTreatmentItem] = Field(default_factory=list)
    past_surgeries_trauma: List[SurgeryTraumaItem] = Field(default_factory=list)
    allergies_intolerances: List[AllergyItem] = Field(default_factory=list)
    lifestyle_risk_factors: LifestyleRiskFactors

class PatientProfile(BaseModel):
    name: str = Field(..., description="Tên xưng hô đời thường Việt Nam (kèm danh xưng)")
    gender: str = Field(..., description="Giới tính ('Nam' hoặc 'Nữ')")
    age: int = Field(..., description="Độ tuổi phù hợp dịch tễ bệnh")
    occupation: str = Field(..., description="Nghề nghiệp cụ thể")
    chief_complaint: str = Field(..., description="Lý do khám / Mô tả cảm giác thực thể giác quan ngắn gọn, không dùng văn nói")

    onset_duration: str = Field(..., description="Thời gian khởi phát và diễn biến")
    address: Optional[str] = Field(None, description="Địa chỉ nơi ở ngắn gọn (xã / Hà Nội)")
    confirm_identity: Optional[bool] = Field(True, description="Cờ xác nhận thông tin hành chính")
    display_name: Optional[str] = Field(None, description="Tên xưng hô đời thường (ví dụ: 'Anh Long')")
    medical_history: MedicalHistory = Field(..., description="Tiền sử y khoa chuẩn 6 trường con")
    speaking_style: str = Field(..., description="Phong cách nói theo nhóm tâm lý")
    edge_case: str = Field(..., description="Kịch bản ngoại lệ / Góc nhìn tâm lý theo SPIT")
