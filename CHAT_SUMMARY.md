# TỔNG KẾT DỰ ÁN & TIẾN TRÌNH HỘI THOẠI (VIETMED-DATA-600)

> **Mục tiêu dự án:** Xây dựng bộ dữ liệu hội thoại y khoa lâm sàng tiếng Việt chất lượng cao (VietMed-600) phục vụ huấn luyện mô hình STT (Speech-to-Text), TTS (Text-to-Speech), và Agentic LLMs hỗ trợ chẩn đoán.
> **Thời lượng kịch bản:** Chuẩn 12 phút / ca khám (~30 lượt lâm sàng chính + ~50-60 phân đoạn thoại tự nhiên có chèn backchannel 80%).
> **Model LLM sử dụng:** `google/gemma-4-31b-it` qua OpenRouter API.

---

## 1. TỔNG QUAN HỆ THỐNG & KIẾN TRÚC PIPELINE

### 1.1. Luồng sinh hội thoại NoteChat ACL
Pipeline mô phỏng phiên khám bệnh lâm sàng chân thực dựa trên kiến trúc Multi-Agent & Rule-based Caching:

1. **Medical Knowledge Base (RAG & Guideline):**
   - Nguồn tài liệu chuẩn hóa: Hướng dẫn chẩn đoán và điều trị bệnh cơ xương khớp - Bộ Y tế (QĐ 361), Vinmec, MSD Manuals, AAOS.
   - Trích xuất đầy đủ 4 trục thông tin: Triệu chứng khởi phát đau, Khám thực thể (nghiệm pháp chuyên khoa), Cận lâm sàng (X-quang, MRI, Xét nghiệm), Phác đồ điều trị 12 phút (thuốc, liều dùng, tập phục hồi, phòng ngừa).

2. **Dual-Agent Dialogue Generation (Doctor & Patient):**
   - **Doctor Agent:** Khai thác bệnh sử theo thứ tự chuẩn y khoa (Hỏi triệu chứng -> Khám thực thể -> Đọc kết quả cận lâm sàng -> Kê đơn & Hướng dẫn).
   - **Patient Agent:** Đóng vai theo persona cụ thể (nghề nghiệp, thói quen, mức độ lo lắng, cách diễn đạt dân dã).

3. **Rule-based Dialogue Sanitizer & Caching (Tối ưu Token & Tự nhiên hóa):**
   - **Tỉ lệ chèn câu đệm (Backchannel Rate):** Đạt mức **80%** đối với các câu phức có mệnh đề ghép (`is_parsed == True`).
   - **Logic Caching không qua LLM:** Các câu đệm ngắn (*"Dạ vâng ạ"*, *"Vâng bác sĩ"*, *"Tôi hiểu rồi ạ"*, *"Ừm..."*) được chèn tự động theo ngữ cảnh mà không gửi lại vào context của LLM, giúp tiết kiệm triệt để token và tăng tốc độ sinh.
   - **Quy tắc 1-cut rule:** Mỗi lượt thoại chính của bác sĩ/bệnh nhân nếu câu dài chỉ được cắt ngang tối đa 1 lần để đảm bảo nhịp thở tự nhiên của đàm thoại người thật, không bị vụn nát.
   - **Không tính lượt thừa:** Các câu chèn đệm không làm tăng số đếm lượt khám lâm sàng (Clinical Turn Count giữ chuẩn 30 lượt).

4. **Timestamp & Audio Synchronization:**
   - Phân bổ mốc thời gian tăng dần từ `[00:00]` đến `[12:00]`.
   - Mỗi phân đoạn thoại được gán timestamp chuẩn xác phục vụ trực tiếp cho việc căn chỉnh audio STT/TTS.

---

## 2. CHÍNH SÁCH QUẢN LÝ MÃ NGUỒN & DỮ LIỆU (GIT)

- **Nguyên tắc cốt lõi:** Chỉ lưu trữ và push **Data & Documentation** lên GitHub repository (`Nhattran05/vietmed-data-600`).
- **Không push mã nguồn logic:** Toàn bộ file `.py`, `.bat`, `.sh` và cache môi trường đều được đưa vào `.gitignore`.
- **Định dạng dữ liệu đầu ra:**
  - `KB_XX_[slug]_markdown.md`: Dạng kịch bản chi tiết có timestamp, phân vai, hành động và ghi chú lâm sàng.
  - `KB_XX_[slug]_docs.txt`: Dạng trích xuất text phục vụ tổng hợp dữ liệu huấn luyện nhanh.

---

## 3. DANH MỤC 60 BỆNH LÝ KHỞI PHÁT VỚI TRIỆU CHỨNG ĐAU

Bảng tổng hợp từ tài liệu `tong_hop_60_benh_khoi_phat_dau.md` chia làm 6 nhóm chuyên khoa:

| Nhóm | Chuyên khoa | Số lượng bệnh | Dải STT |
|:---:|:---|:---:|:---:|
| **I** | Cơ Xương Khớp – Cột Sống – Dây Chằng | 30 | 01 – 30 |
| **II** | Thần Kinh | 8 | 31 – 38 |
| **III** | Tiêu Hóa – Gan Mật | 7 | 39 – 45 |
| **IV** | Tim Mạch – Hô Hấp | 6 | 46 – 51 |
| **V** | Tiết Niệu – Phụ Khoa | 5 | 52 – 56 |
| **VI** | Tai Mũi Họng – Mắt – Răng Hàm Mặt | 4 | 57 – 60 |

---

## 4. TIẾN ĐỘ THỰC HIỆN CÁC KỊCH BẢN (STT 01 - 15)

### Đợt 1: STT 01 đến 10 (Đã hoàn thành & Đẩy lên GitHub)
1. **KB_01:** Viêm quanh khớp vai (Rách gân chóp xoay) - Bác sĩ Nam & Bệnh nhân Tuấn (48t, thợ điện lạnh).
2. **KB_02:** Viêm quanh khớp vai thể đông cứng - Bác sĩ Phương & Cô Lan (52t, tiểu đường type 2).
3. **KB_03:** Hội chứng cổ - vai - cánh tay - Bác sĩ Minh & Anh Hùng (35t, lập trình viên).
4. **KB_04:** Viêm lồi cầu ngoài xương cánh tay (Tennis Elbow) - Bác sĩ Quang & Anh Dũng (42t, chơi tennis phong trào).
5. **KB_05:** Viêm lồi cầu trong xương cánh tay (Golfer's Elbow) - Bác sĩ Hà & Anh Lâm (45t, giám đốc).
6. **KB_06:** Viêm bao gân De Quervain - Bác sĩ Trang & Chị Ngọc (30t, mẹ bỉm sữa).
7. **KB_07:** Hội chứng ống cổ tay - Bác sĩ Tuấn & Chị Nga (46t, kế toán trưởng).
8. **KB_08:** Ngón tay lò xo (Trigger Finger) - Bác sĩ Hoàng & Cô Thu (58t, thợ may gia công).
9. **KB_09:** Thoái hóa cột sống cổ - Bác sĩ Lan & Thầy Bình (55t, giáo viên).
10. **KB_10:** Thoái hóa cột sống thắt lưng - Bác sĩ Đức & Bác Sáu (62t, làm vườn).

### Đợt 2: STT 11 đến 15 (Đang thực thi với Gemma-4-31B-IT)
11. **KB_11:** Hội chứng đau thắt lưng (cấp/mạn) - ICD-10: M54.5 | Đau co cứng cơ cạnh sống sau bê vật nặng.
12. **KB_12:** Đau thần kinh tọa - ICD-10: M54.3 | Đau lan dọc rễ L5-S1, Lasegue (+), bấm chuông (+).
13. **KB_13:** Thoát vị đĩa đệm thắt lưng - ICD-10: M51.2 | Đau buốt lan chân, giảm phản xạ gân gót.
14. **KB_14:** Trượt đốt sống thắt lưng - ICD-10: M43.1 | Dấu hiệu bậc thang (Step-off), đau tăng khi ưỡn.
15. **KB_15:** Hẹp ống sống thắt lưng - ICD-10: M48.0 | Đi khập khiễng cách hồi thần kinh, Shopping Cart Sign (+).

---

## 5. HƯỚNG DẪN MỞ RỘNG TIẾP THEO

- Tiếp tục chạy hàng loạt từ STT 16 đến 30 (nhóm Cơ Xương Khớp còn lại: Viêm cột sống dính khớp, Thoái hóa gối, Hoại tử vô mạch chỏm xương đùi, Viêm cân gan chân, Viêm gân Achilles,...).
- Tiến hành chạy các nhóm chuyên khoa Thần Kinh, Tiêu Hóa, Tim Mạch, Tiết Niệu và Tai Mũi Họng.
- Tự động kiểm tra chất lượng đầu ra: đúng 12 phút `[00:00 - 12:00]`, tỷ lệ backchannel 80%, không chứa emoji/ký hiệu thừa, đơn thuốc có hoạt chất và liều lượng rõ ràng.
