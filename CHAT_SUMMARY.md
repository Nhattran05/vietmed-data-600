# Báo Cáo & Tóm Tắt Toàn Diện Dự Án Sinh Kịch Bản Hội Thoại Y Khoa (NoteChat)

## 1. Giới thiệu và Mục tiêu Dự án
Dự án **VietMed-Data-600** tập trung xây dựng hệ thống tự động sinh dữ liệu hội thoại y khoa Bác sĩ - Bệnh nhân chất lượng cao bằng kiến trúc Multi-Agent (sử dụng LangGraph) phục vụ huấn luyện và đánh giá các mô hình AI trong y tế (ASR, TTS, tóm tắt bệnh án, chẩn đoán sơ bộ).

### Mục tiêu cốt lõi:
- **Chuẩn hóa kiến thức y khoa**: Xây dựng kho dữ liệu 47 bệnh lý phổ biến trong khám chữa bệnh ngoại trú dựa trên phác đồ của Bộ Y tế (QĐ 361) và các cơ sở y tế uy tín.
- **Tạo hội thoại thực tế & tự nhiên**: Mô phỏng tương tác thời gian thực giữa Bác sĩ và Bệnh nhân với đầy đủ các giai đoạn lâm sàng.
- **Tối ưu hóa độ dài & chất lượng**: Kịch bản 12 phút chuẩn (~28–34 lượt khám lâm sàng, tương đương ~40–55 phân đoạn thoại sau xử lý cắt câu và chèn từ đệm).
- **Xuất dữ liệu kép**:
  - `*.md`: Định dạng tài liệu chi tiết có mốc thời gian `[mm:ss - mm:ss]`.
  - `*_docs.txt`: Định dạng dữ liệu văn bản sạch phục vụ training/finetuning mô hình ngôn ngữ và giọng nói.

---

## 2. Kiến trúc Hệ thống Multi-Agent (LangGraph)

Quy trình sinh hội thoại được xây dựng dựa trên mô hình đồ thị trạng thái (`StateGraph`) trong `langgraph_notechat.py`:

```
[Khởi tạo Bệnh án & Persona]
             │
             ▼
      [Planning Node] ─── (Trích xuất 12-14 mục Checklist lâm sàng)
             │
             ▼
     ┌──> [Physician Node] ─── (Tạo câu hỏi/dặn dò ≤ 30 từ, xác định is_parsed)
     │       │
     │       ▼
     │   [Checklist Update Node] ─── (Đánh dấu tiến độ, kích hoạt Dynamic Expansion)
     │       │
     │       ▼
     │   [Patient Node] ─── (Tạo câu trả lời tự nhiên theo Persona, xác định is_parsed)
     │       │
     │       ▼
     └── [Condition Check] ─── (Kiểm tra điều kiện: đủ lượt + đủ checklist + đã kê đơn?)
             │
      (Đạt yêu cầu)
             ▼
       [Closing Node] ─── (Lời chào kết thúc & hẹn tái khám)
             │
             ▼
   [Post-processing Pipeline] ─── (Chèn Backchannel 80% + Tính Timestamp + Xuất File)
```

### Các Node chính trong Pipeline:
1. **Planning Node**: Phân tích `clinical_note` đầu vào và lập dàn ý gồm 12–14 bước lâm sàng tuần tự:
   - Lý do khám & Triệu chứng khởi phát.
   - Vị trí, cường độ, tính chất đau/tê.
   - Yếu tố tăng/giảm triệu chứng.
   - Ảnh hưởng sinh hoạt, công việc, giấc ngủ.
   - Tiền sử bệnh, thói quen và yếu tố nguy cơ.
   - Thao tác khám thực thể (ít nhất 2–3 nghiệm pháp chuyên khoa).
   - Giải thích kết quả Cận lâm sàng (X-quang, MRI, Siêu âm, xét nghiệm).
   - Chẩn đoán xác định & giải thích cơ chế bệnh sinh.
   - Kê đơn thuốc chi tiết (Tên hoạt chất, liều lượng, cách uống, thuốc bảo vệ dạ dày).
   - Giải đáp thắc mắc của bệnh nhân.
   - Hướng dẫn phục hồi chức năng, tập luyện, kiêng cữ.
   - Lịch hẹn tái khám và dặn dò.

2. **Physician Node**:
   - Tuân thủ nghiêm ngặt ràng buộc: tối đa 3 câu/lượt, không quá 30 từ/lượt.
   - Tuyệt đối không dùng thuật ngữ kỹ thuật khó hiểu (không nói "nghiệm pháp Neer dương tính" mà hướng dẫn hành động thực tế).
   - Gán cờ `is_parsed: true/false` biểu thị câu nói có thể chèn lời đệm hay không.

3. **Checklist Update Node & Dynamic Expansion**:
   - Theo dõi từng mục trong checklist đã được trao đổi.
   - Ngăn chặn kết thúc sớm nếu chưa qua đủ các bước quan trọng (đặc biệt là bước khám thực thể và kê đơn thuốc).

4. **Patient Node**:
   - Phản hồi dựa trên ngữ cảnh và đặc trưng tính cách (tuổi tác, nghề nghiệp, mức độ lo âu).
   - Không được thấy checklist của bác sĩ; tự động hỏi về tác dụng phụ của thuốc lên dạ dày khi được kê đơn.

5. **Closing Node**:
   - Hoàn tất ca khám với lời dặn dò cuối cùng và lời chào ra về.

---

## 3. Cơ chế Xử lý Ngôn ngữ & Tối ưu hóa (Dialogue Sanitizer)

### 3.1. Quy tắc Cắt câu 1 lần (1-Cut Split Rule)
- Thay vì cắt vụn vặt ở mọi dấu câu, hệ thống chỉ cắt **tối đa 1 lần ở giữa câu/đoạn** đối với các lượt thoại dài được gắn cờ `is_parsed == true`.
- Tỷ lệ kích hoạt cắt và chèn từ đệm: **80%** (theo cấu hình mới nhất).

### 3.2. Caching Lời đệm & Tiết kiệm Token (Prompt Caching / Local Injection)
- Các câu đệm như *"Vâng ạ", "Dạ", "Tôi hiểu rồi", "Vâng, bác cứ nói tiếp đi"* được lấy từ kho từ điển nội bộ (Memory Cache) phù hợp với độ tuổi và vai trò.
- **Không tốn token gọi LLM** cho các từ đệm này.
- Trước khi chuyển lịch sử hội thoại cho LLM ở lượt kế tiếp, hàm `format_history_for_prompt` tự động lọc sạch các câu đệm và ghép nối lại các câu bị cắt thành câu nguyên bản, giúp tránh bùng nổ độ dài context và chống suy thoái chất lượng sinh văn bản.

### 3.3. Quy tắc Đếm lượt (Turn Counting) & Định dạng Markdown
- Các câu đệm và nửa câu sau khi cắt mang thuộc tính `is_counted_turn = False`.
- Tiêu đề kịch bản hiển thị phân định rõ ràng:
  `X lượt khám lâm sàng (Y phân đoạn thoại) | Thời lượng giả định: ~12 phút`
- **100% Không có biểu tượng cảm xúc (No Emojis)**: Loại bỏ toàn bộ `🩺`, `👤` để đảm bảo văn bản chuẩn hóa.
- Mỗi câu thoại được gắn mốc thời gian tuyến tính `[mm:ss - mm:ss]` dựa trên số lượng từ và tốc độ nói tự nhiên (~3.5 - 4 từ/giây).

---

## 4. Tích hợp Mô hình Ngôn ngữ (LLM Provider)

- **Mô hình chính**: `google/gemma-4-31b-it` thông qua OpenRouter API.
- **Khả năng dự phòng (Fallback)**: Tự động chuyển đổi sang Google Gemini (`gemini-2.5-flash-lite`, `gemini-3-flash-preview`...) nếu kết nối mạng hoặc API gặp sự cố.
- **Tối ưu hóa nhiệt độ (Temperature)**: Đặt ở mức `0.7` nhằm đảm bảo tính tự nhiên, sinh động trong lời thoại của bệnh nhân nhưng vẫn bám sát thông tin y khoa của bác sĩ.

---

## 5. Tổng hợp 10 Kịch bản Khám bệnh Đầu tiên (Nhóm I: Cơ Xương Khớp)

| STT | Mã ICD-10 | Tên bệnh lý | Bác sĩ | Bệnh nhân | Đặc điểm lâm sàng chính |
|:---:|:---:|:---|:---|:---|:---|
| **01** | `M75.1` | Viêm quanh khớp vai (rách gân chóp xoay) | BS. Minh | Bác Thành (58t, thợ điện nước) | Đau đêm, hạn chế giơ tay, nghiệm pháp Neer/Hawkins (+), MRI rách gân 5mm. Đơn: Celecoxib, Eperisone, Esomeprazole. |
| **02** | `M75.0` | Viêm quanh khớp vai thể đông cứng | BS. Hạnh | Bác Lan (60t, nội trợ) | Khớp vai cứng đơ đa hướng, Shrug sign (+), dày bao khớp. Đơn: Meloxicam, Tolperisone, Pantoprazole + tập leo tường. |
| **03** | `M53.1` | Hội chứng cổ – vai – cánh tay | BS. Trí | Anh Tuấn (45t, kỹ sư IT) | Đau lan từ cổ xuống tay, tê ngón 1-2-3, Spurling (+), Distraction (+), MRI lồi đĩa đệm C5-C7. Đơn: Celecoxib, Gabapentin. |
| **04** | `M77.1` | Viêm lồi cầu ngoài (Tennis Elbow) | BS. Quân | Chị Mai (42t, đầu bếp) | Đau chói mặt ngoài khuỷu, Cozen (+), Mill (+), siêu âm dày gân ECRB. Đơn: Meloxicam, gel Diclofenac, đai cẳng tay. |
| **05** | `M77.0` | Viêm lồi cầu trong (Golfer's Elbow) | BS. Minh | Bác Dũng (52t, thợ gò hàn) | Đau mặt trong khuỷu, yếu lực nắm, Reverse Cozen (+), Tinel (-). Đơn: Celecoxib, Eperisone, chườm lạnh. |
| **06** | `M65.4` | Viêm bao gân De Quervain | BS. Hạnh | Chị Hoa (34t, mẹ bỉm sữa) | Đau mỏm trâm quay khi bế con, Finkelstein (+), siêu âm Halo sign (+). Nẹp Spica ngón cái, Celecoxib, gel bôi. |
| **07** | `G56.0` | Hội chứng ống cổ tay | BS. Trí | Cô Nga (55t, thợ may) | Tê rát 3 ngón giữa về đêm, Tinel (+), Phalen (+), điện cơ chậm dẫn truyền. Đeo nẹp đêm, Meloxicam, Gabapentin, Vit B. |
| **08** | `M65.3` | Ngón tay lò xo (Viêm gân gấp) | BS.剪 | Bác Bình (63t, làm vườn) | Kẹt ngón trỏ, bật nảy 'khục', sờ nốt gân A1. Ngâm nước ấm, nẹp ngón, Celecoxib, cân nhắc tiêm/tiểu phẫu. |
| **09** | `M47.8` | Thoái hóa cột sống cổ | BS. Minh | Bác Hùng (62t, hưu trí) | Đau mỏi gáy 6 tháng, tiếng lạo xạo, X-quang hẹp C4-C6, mọc gai. Meloxicam, Eperisone, Glucosamine, gối thấp 8-10cm. |
| **10** | `M47.8` | Thoái hóa cột sống thắt lưng | BS. Trí | Bác Lâm (65t, lao động tự do) | Đau âm ỉ L3-S1 khi cúi/đứng lâu, Schober giảm, X-quang hẹp đĩa đệm. Celecoxib, Eperisone, bài tập Cat-Cow, bơi lội. |

---

## 6. Cấu trúc và Vị trí File Trong Dự án

```text
d:\test STT\
├── .env                                       # Chứa OPENROUTER_API_KEY & GOOGLE_API_KEY
├── .gitignore                                 # Cấu hình Git chỉ theo dõi Output, output-600, *.md
├── merged.md                                  # Danh mục 47 bệnh chuẩn hóa đầy đủ nguồn y khoa
├── danh-sach-60-benh-khong-cap-cuu.md         # Bảng 60 bệnh phân loại theo vùng giải phẫu
├── CHAT_SUMMARY.md                            # Bản tóm tắt dự án và toàn bộ phiên làm việc này
├── langgraph_notechat.py                      # Core engine: StateGraph, Nodes, LLM connector
├── dialogue_sanitizer.py                      # Bộ lọc từ đệm, cắt câu 1 lần (tỷ lệ 80%), tính timestamp
├── output-600/                                # Thư mục chứa kịch bản xuất ra (10 kịch bản x 2 định dạng)
│   ├── KB_01_viem_quanh_khop_vai_rach_chop_xoay_markdown.md
│   ├── KB_01_viem_quanh_khop_vai_rach_chop_xoay_docs.txt
│   ├── KB_02_viem_quanh_khop_vai_dong_cung_markdown.md
│   ├── ...
│   ├── KB_10_thoai_hoa_cot_song_that_lung_markdown.md
│   └── KB_10_thoai_hoa_cot_song_that_lung_docs.txt
```

---

## 7. Hướng dẫn Mở rộng & Tái sử dụng

1. **Sinh tiếp các bệnh từ STT 11 - 47**:
   - Thêm thông tin bệnh vào danh sách trong script `batch_generate_top10_12min.py` (hoặc mở rộng sang toàn bộ 47 bệnh).
   - Chạy lệnh: `python -u batch_generate_all.py`
2. **Thay đổi tham số**:
   - `duration_minutes`: Tuỳ chỉnh 8, 10, 12, 15 phút.
   - `backchannel_rate`: Mặc định 0.80 (80% số câu thỏa mãn điều kiện sẽ được chèn câu đệm).
   - `model_name`: Có thể đổi sang bất kỳ model nào hỗ trợ trên OpenRouter hoặc chuyển sang `llm_provider="gemini"`.
3. **Đồng bộ mã nguồn**:
   - Chạy `git add .` -> `git commit -m "..."` -> `git push origin main`.
