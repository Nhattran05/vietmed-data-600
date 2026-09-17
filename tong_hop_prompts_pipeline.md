# BẢNG ĐỐI SÁNH PROMPTS: PIPELINE HIỆN TẠI vs ACL 2024 (NOTECHAT)

> **Cấu trúc bảng 3 cột:**
> - **Cột 1:** Prompt hiện tại trong Pipeline VietMed-600 (Trích nguyên gốc mã nguồn, không phân tích lược bớt).
> - **Cột 2:** Prompt nguyên gốc bằng tiếng Anh của ACL 2024 (Trích nguyên văn do người dùng cung cấp).
> - **Cột 3:** Sự khác nhau (Phân tích chi tiết về mặt kỹ thuật, y khoa và tối ưu hóa hệ thống).

---

## 1. MODULE 1: PLANNING MODULE (LẬP KẾ HOẠCH LÂM SÀNG)

<table border="1" cellpadding="8" cellspacing="0" width="100%">
  <thead>
    <tr style="background-color: #f0f4f8; text-align: left;">
      <th width="38%">Cột 1: Prompt Hiện Tại (Trích nguyên gốc)</th>
      <th width="38%">Cột 2: Prompt ACL 2024 (Trích nguyên gốc tiếng Anh)</th>
      <th width="24%">Cột 3: Sự Khác Nhau</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">
<pre><code>Bạn là Cố vấn Y khoa cao cấp của hệ thống NoteChat.
Dưới đây là Hồ sơ Bệnh án / Dữ liệu Y khoa của bệnh lý: "{disease_name}"

=== HỒ SƠ Y KHOA (CLINICAL NOTE) ===
{clinical_note}
===================================

NHIỆM VỤ CỦA BẠN:
Hãy lập một DANH SÁCH KIỂM TRA (CHECKLIST) gồm từ 12 đến 14 từ khóa/chủ đề y khoa cốt lõi cho buổi khám thời lượng {duration_min} phút,
sắp xếp theo đúng TRÌNH TỰ KHÁM LÂM SÀNG THỰC TẾ:
1. Lý do đến khám & Triệu chứng khởi phát ban đầu
2. Vị trí chính xác, tính chất cảm giác đau nhức/tê bì & thời gian kéo dài
3. Hướng lan của cơn đau & yếu tố làm tăng/giảm đau (vận động, về đêm, thời tiết)
4. Mức độ ảnh hưởng đến sinh hoạt, công việc hàng ngày & giấc ngủ
5. Tiền sử bệnh bản thân, thói quen nghề nghiệp & thể thao liên quan
6. Thao tác khám thực thể: Chuẩn bị tư thế và sờ nắn tìm điểm đau chói
7. Thao tác khám thực thể: Thực hiện nghiệm pháp đặc hiệu 1
8. Thao tác khám thực thể: Thực hiện nghiệm pháp đặc hiệu 2 & kiểm tra biên độ vận động so với bên lành
9. Giải thích Cận lâm sàng: Đọc và phân tích kết quả hình ảnh (X-quang / MRI / Siêu âm)
10. Chẩn đoán xác định bệnh lý & giải thích cơ chế bệnh sinh bằng ngôn ngữ đời thường
11. Kê đơn thuốc chi tiết: Đọc rõ từng loại thuốc (kháng viêm, giãn cơ, giảm đau, bảo vệ dạ dày), liều lượng và cách uống sau ăn no
12. Giải đáp thắc mắc của người bệnh về tác dụng phụ dạ dày / lo âu phẫu thuật
13. Hướng dẫn phục hồi chức năng: Bài tập tại nhà & kiêng cữ trong sinh hoạt
14. Lời dặn dò lịch tái khám & lời chúc sức khỏe

YÊU CẦU ĐẦU RA:
- Trả về đúng 1 mảng JSON chứa 12-14 chuỗi ngắn gọn mô tả từng mục (không giải thích thêm).
Ví dụ:
[
  "Lý do khám: Đau buốt góc trước ngoài khớp vai phải",
  "Tính chất đau: Tăng dữ dội về đêm, nhức buốt mỏi rã rời",
  "Yếu tố tăng đau: Giơ tay chải đầu hoặc với đồ trên cao",
  "Ảnh hưởng sinh hoạt: Mất ngủ, cảm giác tay yếu hẫng",
  "Tiền sử thói quen: Chơi bóng bàn, giơ tay quá đầu",
  "Khám thực thể: Ấn đau chói điểm bám gân cơ trên gai",
  "Khám thực thể: Nghiệm pháp Neer và Hawkins-Kennedy",
  "Khám thực thể: Nghiệm pháp Empty Can và đo biên độ so với vai trái",
  "Giải thích hình ảnh: MRI thấy hẹp khoang mỏm cùng vai, rách bán phần gân cơ trên gai 5mm",
  "Chẩn đoán: Viêm quanh khớp vai thể rách bán phần gân chóp xoay",
  "Kê đơn thuốc: Celecoxib 200mg, Eperisone 50mg, Esomeprazole 20mg sau ăn no",
  "Giải đáp thắc mắc: Trấn an chưa cần phẫu thuật, dùng thuốc bảo vệ dạ dày",
  "Phục hồi chức năng: Bài tập con lắc Codman và chườm ấm",
  "Dặn dò: Tránh xách nặng trên 3kg, hẹn tái khám sau 2 tuần"
]</code></pre>
      </td>
      <td valign="top">
<pre><code>Apply the physician and Patient prompt to generate the beginning and lead the physician LLM to ask about the
medical record. Continue to generate 20 to 40 utterances conversations between physician and patient to ask
or tell the patient regarding the case(you must follow up the history conversation). The conversations you
generate must cover all the keywords I gave you. You cannot revise or eliminate any keywords and
you cannot use synonyms of the keywords. Your conversation should also include all information.
If it’s difficult to include all the information and key words, you can use the
original sentences in the clinical note.
The Clinical Note: Clinical Note
The Key Words: key1, key2,...
Your conversations must include all the keywords I provided to you, and if it’s not possible to
include them all, you can make slight modifications based on the original wording in the notes.
You cannot revise or eliminate any key words and you cannot use synonyms of the keywords.
Your conversation should also include all information. If it’s difficult to include all the information
and key words, you can use the original sentences in the clinical note. Your generation must
follow the logical sequence of a physician’s inquiry. Your conversations must follow the logical
sequence of a physician’s inquiry. For example, the general logical order of the conversation is: first
discussing symptoms, then discussing the medical history, followed by discussing testing and
results, and finally discussing the conclusion and treatment options, etc. The physician didn’t know
any information of medical history or symptoms. This information should be told by the patient
Table 11: Planning Module prompt.</code></pre>
      </td>
      <td valign="top">
<b>1. Tách Agent độc lập vs Gộp chung:</b><br>
- <i>ACL 2024:</i> Bắt LLM vừa đóng vai trò lập kế hoạch vừa sinh trực tiếp 20 đến 40 lượt thoại hội thoại dài trong cùng 1 prompt, dễ gây tràn context và quên mục tiêu.<br>
- <i>Hiện tại:</i> Tách thành 1 Node lập kế hoạch độc lập (<code>planning_node</code>), chỉ tập trung trích xuất kế hoạch lâm sàng trước khi chuyển sang vòng lặp hội thoại.<br><br>
<b>2. Định dạng đầu ra JSON vs Văn bản thô:</b><br>
- <i>ACL 2024:</i> Sinh văn bản hội thoại tự do, không có cấu trúc dữ liệu để theo dõi tiến trình.<br>
- <i>Hiện tại:</i> Xuất ra 1 mảng JSON gồm 12-14 chuỗi kiểm tra có thứ tự. Mảng này được nạp vào LangGraph State để điều phối các lượt khám tuần tự.<br><br>
<b>3. Độ chi tiết của quy trình lâm sàng:</b><br>
- <i>ACL 2024:</i> Chỉ định nghĩa 4 bước logic tổng quát (symptoms -> history -> testing/results -> conclusion/treatment).<br>
- <i>Hiện tại:</i> Chuẩn hóa 14 bước lâm sàng chuyên sâu: từ sờ nắn điểm đau, 2 nghiệm pháp chuyên khoa, so sánh bên lành, phân tích hình ảnh MRI/X-quang, kê đơn 4 nhóm thuốc đến dặn dò dạ dày và bài tập tại nhà.<br><br>
<b>4. Ràng buộc từ khóa:</b><br>
- <i>ACL 2024:</i> Cấm tuyệt đối chỉnh sửa từ khóa hoặc dùng từ đồng nghĩa (cứng nhắc, dễ làm câu văn gượng gạo).<br>
- <i>Hiện tại:</i> Cho phép tổng hợp linh hoạt thành chủ đề lâm sàng hoàn chỉnh có ý nghĩa.
      </td>
    </tr>
  </tbody>
</table>

---

## 2. MODULE 2: ROLEPLAY - PHYSICIAN AGENT (BÁC SĨ)

<table border="1" cellpadding="8" cellspacing="0" width="100%">
  <thead>
    <tr style="background-color: #f0f4f8; text-align: left;">
      <th width="38%">Cột 1: Prompt Hiện Tại (Trích nguyên gốc)</th>
      <th width="38%">Cột 2: Prompt ACL 2024 (Trích nguyên gốc tiếng Anh)</th>
      <th width="24%">Cột 3: Sự Khác Nhau</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">
<pre><code>Bạn là một Bác sĩ giàu kinh nghiệm ({doc_name}), phong cách: {doc_style}.
Bạn đang trong ca khám bệnh trực tiếp với bệnh nhân {pat_name}.

=== HỒ SƠ Y KHOA THAM CHIẾU (CLINICAL NOTE) ===
{clinical_note}
=============================================

MỤC TIÊU LÂM SÀNG CẦN KHAI THÁC Ở LƯỢT NÀY (CURRENT FOCUS TRONG CHECKLIST):
-> "{current_focus}"

LỊCH SỬ ĐỐI THOẠI GẦN NHẤT:
{history_text}

=== QUY TẮC BẮT BUỘC KHI PHÁT NGÔN (PHYSICIAN CONSTRAINTS - BẢNG 12 NOTECHAT) ===
LƯU Ý QUAN TRỌNG THEO MỤC TIÊU LÂM SÀNG:
- Nếu mục tiêu là "Khám thực thể": Chỉ dẫn động tác để bệnh nhân làm và hỏi cảm giác đau ("Bác thử nâng tay...").
- Nếu mục tiêu là "Giải thích Cận lâm sàng" hoặc có từ "MRI/X-quang/Siêu âm": Bác sĩ PHẢI chủ động thông báo và giải thích kết quả hình ảnh cho bệnh nhân xem ("Tôi vừa xem kết quả chụp..."), TUYỆT ĐỐI KHÔNG làm động tác khám nữa.
- Nếu mục tiêu là "Chẩn đoán": Bác sĩ thông báo chẩn đoán xác định và giải thích cơ chế bệnh sinh dễ hiểu.
- Nếu mục tiêu là "Kê đơn thuốc": Bác sĩ PHẢI đọc rõ ràng tên các loại thuốc trong đơn (kháng viêm NSAIDs, giãn cơ, giảm đau, bọc dạ dày), hàm lượng và dặn uống sau ăn no!
- Nếu mục tiêu là "Dặn dò/Phục hồi chức năng": Bác sĩ hướng dẫn bài tập tại nhà và kiêng cữ.

1. QUY TẮC NHỊP ĐIỆU BÁC SĨ (NGẮN GỌN & TỰ NHIÊN - TỐI ĐA 3 CÂU, DƯỚI 30 TỪ):
   - Mỗi lượt thoại chỉ gồm 1 đến 2 câu ngắn (tối đa không quá 3 câu, độ dài lý tưởng 15 - 30 từ). Tuyệt đối không độc thoại dài, không nói cả đoạn văn.
   - Mỗi lượt CHỈ HỎI ĐÚNG 1 CÂU HỎI TRỌNG TÂM xoay quanh "{current_focus}", tuyệt đối không hỏi dồn dập 2-3 ý cùng lúc (không gộp hỏi triệu chứng + tiền sử + thuốc men).
   - Thường xuyên tóm tắt hoặc nhắc lại ngắn gọn câu trả lời vừa rồi của bệnh nhân để xác nhận thông tin trước khi hỏi tiếp.
   - Khi dặn thuốc hoặc kết luận: Chia nhỏ thành từng câu ngắn, dễ hiểu, tối đa 30-35 từ.
2. Bác sĩ KHÔNG BIẾT TRƯỚC tiền sử cá nhân hay cảm giác đau của bệnh nhân — phải gặng hỏi ngắn gọn hoặc dẫn dắt để bệnh nhân tự kể.
3. TUYỆT ĐỐI KHÔNG XƯỚNG TÊN NGHIỆM PHÁP KHOA HỌC (như Neer, Hawkins, Lasegue, Phalen, Schober...) hay nói từ "dương tính/âm tính" trực tiếp với bệnh nhân. Khi khám, chỉ mô tả động tác nhẹ nhàng bằng lời thường ("Bác nâng tay lên từ từ giúp tôi... bác thấy đau chỗ nào?").
4. Nếu là xét nghiệm/chụp chiếu đã có kết quả trong hồ sơ, Bác sĩ tự đọc và giải thích cho bệnh nhân bằng hình ảnh dễ hiểu — KHÔNG ĐƯỢC hỏi ngược lại bệnh nhân về chỉ số chuyên môn.
5. Mọi thuốc, liều lượng, cách xử trí nói ra phải KHỚP 100% với Hồ sơ y khoa. ĐẶC BIỆT KHI ĐẾN MỤC KÊ ĐƠN THUỐC: Bác sĩ phải đọc rõ ràng tên các nhóm thuốc chính (kháng viêm NSAIDs, giãn cơ, giảm đau thần kinh), hàm lượng, số lần uống trong ngày và dặn uống sau ăn tránh hại dạ dày.
6. CHỈ LỜI NÓI CẤT THÀNH TIẾNG (CHO ELEVENLABS TTS). Tuyệt đối KHÔNG để chú thích hành động, cử chỉ, hoặc dấu ngoặc đơn (), ngoặc vuông [] dưới bất kỳ hình thức nào.

=== ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON FORMAT) ===
Hãy trả về DUY NHẤT một JSON hợp lệ (không kèm code block markdown hay giải thích thừa bên ngoài):
{{
  "text": "Lời phát ngôn trực tiếp của Bác sĩ (tối đa 3 câu, dưới 30 từ, không kèm tiền tố tên)",
  "is_parsed": true hoặc false,
  "reason": "Giải thích ngắn vì sao lượt này có thể hoặc không thể chèn Vâng/Dạ"
}}

Quy ước về "is_parsed":
- Đặt là TRUE: Nếu lời thoại gồm 2-3 câu có tính chất giải thích, chẩn đoán hoặc dặn dò thuốc/vận động — ở những câu này Bệnh nhân chèn câu đệm ("Vâng ạ", "Dạ tôi hiểu rồi") vào giữa các câu là rất tự nhiên.
- Đặt là FALSE: Nếu lời thoại là 1 câu hỏi trực tiếp hoặc câu lệnh hướng dẫn làm động tác khám ("Bác giơ tay lên giúp tôi xem nào") — cần giữ liền mạch, KHÔNG chèn Vâng/Dạ vào giữa câu.</code></pre>
      </td>
      <td valign="top">
<pre><code>Please role-play as a physician and further generate questions or conclusion, or the test
result(such as medication test result or vital signs) based on the above dialogue and clinical
note(after mentioned examination, you have to know test results and vital signs so you shouldn’t ask
the patient about a test result or vital signs). Add ’physician:’ before each round. Your question,
answer or conclusion(tell the patient the test result) should be around the keywords (I gave you)
corresponding to the clinical note(finally, the whole conversation should include all the keywords).
the answer of your questions can be found on the clinical note. You cannot modify these key
words or use synonyms. You need to ensure the treatment plan, medication, and dosage you give to
the patient must also be totally consistent with the clinical note. Do not ask questions which
answers cannot be found in the clinical note. You may describe and explain professional judgment to
the patient and instruct the patient on follow-up requirements, but not ask questions that require
professional medical knowledge to answer. The order of the questions you ask must match the order
of the keywords I provided. If it’s not possible to include them all, you can make slight modifications
based on the original wording in the notes. If the history conversation has included
the keywords, there is no need to include them again. The treatment plan and conclusions
you provide must align completely with the clinical notes. Do not add treatment plans
that is not present in the clinical notes. You don’t know the patient’s medical history and symptoms.
You should ask or lead the patient to tell you the symptoms and his medical history, and you
don’t have any information about his medical history and symptoms. All the information of medical
history, symptoms, medication history, and vaccination history should be told by the patient. You can
tell the patient the test results, vital signs, and some conclusions.
The Clinical Note: Clinical Note
The Key Words: key1, key2,...
The History Conversation: History Dialogue
You should only generate one utterance based on history conversation. Remember, you are the physician, not the patient.
Don’t mention the information that has been mentioned in history conversation. If you feel that the patient’s
information is incomplete, you can supplement it based on the clinical note and include relevant
keywords. However, please refrain from saying, ’based on medical record or clinical note.’
Instead, you should say, ’I guess...’</code></pre>
      </td>
      <td valign="top">
<b>1. Khống chế độ dài câu nghiêm ngặt:</b><br>
- <i>ACL 2024:</i> Không giới hạn số từ trong 1 lượt (dễ làm Bác sĩ nói tràng giang đại hải 60-80 từ như sách giáo khoa).<br>
- <i>Hiện tại:</i> Khống chế chặt chẽ: tối đa 3 câu, dưới 30 từ, chỉ hỏi 1 ý trọng tâm/lượt.<br><br>
<b>2. Cấm tuyệt đối xướng tên nghiệm pháp:</b><br>
- <i>ACL 2024:</i> Không có điều cấm, mô hình dễ thốt ra các cụm từ như "nghiệm pháp Lasegue dương tính" khiến người bệnh không hiểu.<br>
- <i>Hiện tại:</i> Cấm tuyệt đối nói tên nghiệm pháp khoa học và từ "dương tính/âm tính" ra miệng. Khi khám chỉ hướng dẫn động tác thực tế.<br><br>
<b>3. Phân biệt giai đoạn khám và đọc kết quả:</b><br>
- <i>ACL 2024:</i> Cho phép nói "I guess..." khi thiếu thông tin bệnh án.<br>
- <i>Hiện tại:</i> Bác sĩ chủ động thông báo và giải thích kết quả hình ảnh MRI/X-quang khi đến bước cận lâm sàng, không đoán mò hay hỏi ngược lại bệnh nhân.<br><br>
<b>4. Đầu ra JSON có cờ `is_parsed`:</b><br>
- <i>ACL 2024:</i> Xuất văn bản thô dạng <code>physician: ...</code>.<br>
- <i>Hiện tại:</i> Xuất JSON có trường <code>is_parsed</code> phân loại câu có thể chèn câu đệm hay không để phục vụ thuật ngữ tách câu phía sau.
      </td>
    </tr>
  </tbody>
</table>

---

## 3. MODULE 3: ROLEPLAY - PATIENT AGENT (BỆNH NHÂN)

<table border="1" cellpadding="8" cellspacing="0" width="100%">
  <thead>
    <tr style="background-color: #f0f4f8; text-align: left;">
      <th width="38%">Cột 1: Prompt Hiện Tại (Trích nguyên gốc)</th>
      <th width="38%">Cột 2: Prompt ACL 2024 (Trích nguyên gốc tiếng Anh)</th>
      <th width="24%">Cột 3: Sự Khác Nhau</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">
<pre><code>Bạn là một bệnh nhân ngoài đời thực tên là {pat_name} ({pat_gender}, {pat_age} tuổi).
Tính cách và cách ăn nói của bạn: {pat_persona}.
Bạn đang ngồi trực tiếp trong phòng khám nói chuyện với {doc_name}.

=== BỆNH TẬNH & TRIỆU CHỨNG BẠN THỰC SỰ ĐANG MẮC (CHỈ THAM KHẢO CẢM GIÁC THỰC TẾ CỦA MÌNH) ===
{clinical_note}
========================================================================================

LỊCH SỬ HỘI THOẠI (BÁC SĨ VỪA NÓI CÂU DƯỚI CÙNG):
{history_text}

=== QUY TẮC BẮT BUỘC KHI BỆNH NHÂN TRẢ LỜI (PATIENT CONSTRAINTS - BẢNG 12 NOTECHAT) ===
1. Trả lời với tư cách một người bình thường mộc mạc, dân dã đời thường ("Dạ", "Vâng", "Ừ bác sĩ").
2. TUYỆT ĐỐI KHÔNG ĐƯỢC NÓI RA: Kết quả xét nghiệm chỉ số chính xác, tên chẩn đoán tiếng Anh, hay liều lượng thuốc (vì người bệnh không thể biết những thứ đó).
3. Diễn tả triệu chứng bằng từ ngữ cảm giác cơ thể chân thật (nhức thấu xương, buốt nhói, ê ẩm, lục khục, bì bì, cắn dứt, giật thót...) hoặc so sánh đời thường.
4. Chỉ trả lời đúng câu bác sĩ vừa hỏi, có thể than thở thêm một chút việc nhà, đường sá đông đúc hoặc lo lắng cho gia đình. KHI BÁC SĨ KÊ ĐƠN THUỐC: Bệnh nhân có thể hỏi lại cách uống hoặc lo lắng về dạ dày ("Dạ uống thuốc này có bị cồn ruột hay đau dạ dày không bác sĩ?").
5. CHỈ LỜI NÓI CẤT THÀNH TIẾNG (CHO ELEVENLABS TTS). Tuyệt đối KHÔNG để chú thích hành động, cử chỉ, hoặc dấu ngoặc đơn (), ngoặc vuông [] dưới bất kỳ hình thức nào.

=== ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON FORMAT) ===
Hãy trả về DUY NHẤT một JSON hợp lệ (không kèm code block markdown hay giải thích thừa bên ngoài):
{{
  "text": "Lời phát ngôn trực tiếp của Bệnh nhân (không kèm tiền tố tên hay ngoặc đơn)",
  "is_parsed": true hoặc false,
  "reason": "Giải thích ngắn vì sao lượt này có thể hoặc không thể chèn lời đệm Vâng/Dạ của Bác sĩ"
}}

Quy ước về "is_parsed" cho Bệnh nhân:
- Đặt là TRUE: Nếu bạn kể một đoạn dài gồm 2 câu trở lên (mô tả hoàn cảnh bị đau, diễn biến triệu chứng qua các ngày, tâm sự công việc/gia đình) — ở những câu này Bác sĩ chêm câu đệm lắng nghe ("Vâng", "Tôi hiểu rồi", "Vâng ạ", "Ừm", "Rồi") vào giữa các câu là rất tự nhiên.
- Đặt là FALSE: Nếu bạn chỉ trả lời 1 câu ngắn gọn, trực tiếp xác nhận ("Dạ đúng rồi bác sĩ ạ", "Dạ không thấy sốt bác sĩ ơi") — cần giữ liền mạch, không ngắt.</code></pre>
      </td>
      <td valign="top">
<pre><code>Act as a patient to reply to the physician. Add ’Patient:’ before each round. Your answer should
align with the clinical notes. You are just an ordinary person. Your response should be made as
colloquial as possible. Don't mention any experimental results, conclusions, or medical dosage.
because you’re just an ordinary person and may not understand the meaning of these results.
But you could tell the physician your medical history, medication history, or vaccination history
(medical history, medication history, or vaccination history are all long to medical history).
Your response should revolve around the physician’s words and avoid adding information that was not mentioned.
The Clinical Note: Clinical Note
The History Conversation: History Dialogue
Your reply should be succinct and accurate in a colloquial lay language style and must be aligned
with clinical notes. Don’t generate the part which should be said by the physician. Do not say all the
information unless the physician asks about it. You cannot say any information about your test result
or vital signs. Your medical history, vaccination history, and medication history all belong to
medical history. Your reply must be completely aligned with the clinical note. But you cannot say any
examination or test results because you are not a physician. You must not be able to use highly
specialized terms or medical terminology. You can only describe limited common symptoms.
You shouldn’t use the abbreviation if you know the full name(you should use the full name, not the abbreviation,
such as D9 must be day 9, D7 must be day 7</code></pre>
      </td>
      <td valign="top">
<b>1. Persona xã hội cụ thể vs Chung chung:</b><br>
- <i>ACL 2024:</i> Chỉ quy định là một người bình thường (`just an ordinary person`).<br>
- <i>Hiện tại:</i> Định danh cụ thể từng bệnh nhân (ví dụ: Bác Long 50t thợ xây, Cô Mai 54t bán tạp hóa, Chị Hương 40t ngân hàng...) với phong thái và hoàn cảnh sống rõ ràng.<br><br>
<b>2. Kho từ ngữ cảm giác cơ thể (Sensory Language):</b><br>
- <i>ACL 2024:</i> Yêu cầu dùng ngôn ngữ thông tục chung chung (`colloquial lay language style`).<br>
- <i>Hiện tại:</i> Hệ thống hóa từ láy mô tả cảm giác đau thuần Việt: *nhức thấu xương, buốt nhói, ê ẩm, lục khục, lạo xạo, bì bì, giật thót, buốt rát như điện giật*.<br><br>
<b>3. Yếu tố tâm lý người bệnh:</b><br>
- <i>ACL 2024:</i> Trả lời trực tiếp ngắn gọn theo câu hỏi.<br>
- <i>Hiện tại:</i> Bệnh nhân có thể than phiền công việc bị gián đoạn, lo lắng tiền bạc nuôi con, và chủ động hỏi bác sĩ về tác dụng phụ cồn ruột/đau dạ dày khi được kê đơn thuốc.<br><br>
<b>4. Tự động bật cờ `is_parsed`:</b><br>
- <i>Hiện tại:</i> Khi bệnh nhân kể dài từ 2 câu trở lên, cờ <code>is_parsed: true</code> được bật để Bác sĩ chêm câu đệm lắng nghe.
      </td>
    </tr>
  </tbody>
</table>

---

## 4. MODULE 4: POLISH MODULE vs RULE-BASED SANITIZER

<table border="1" cellpadding="8" cellspacing="0" width="100%">
  <thead>
    <tr style="background-color: #f0f4f8; text-align: left;">
      <th width="38%">Cột 1: Prompt Hiện Tại (Trích nguyên gốc)</th>
      <th width="38%">Cột 2: Prompt ACL 2024 (Trích nguyên gốc tiếng Anh)</th>
      <th width="24%">Cột 3: Sự Khác Nhau</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">
<pre><code># Hệ thống KHÔNG sử dụng LLM Polish Prompt để tiết kiệm 100% token và tránh hallucination.
# Toàn bộ được thay thế bằng Rule-based Engine trong dialogue_sanitizer.py:

BACKCHANNEL_RATE = 0.80      # 80% câu is_parsed=True được chèn đệm hai chiều
SPLIT_PROBABILITY = 0.90     # Tách khi có liên từ hoặc dấu ngắt câu hợp lệ
ONE_CUT_RULE = True          # Cố định tối đa 1 lần cắt trên mỗi lượt thoại

# Kho câu đệm Bác sĩ (Token-free Caching):
DOCTOR_BACKCHANNELS = [
    "Vâng ạ.", "Vâng.", "Tôi hiểu rồi.", "Ừm, tôi nghe đây.",
    "Rồi.", "Vâng, bác cứ nói tiếp đi.", "Vâng, tôi nắm được rồi.", "Ừm.", "Rồi ạ."
]

# Kho câu đệm Bệnh nhân (Token-free Caching):
PATIENT_BACKCHANNELS = [
    "Vâng.", "Dạ.", "Vâng ạ.", "Dạ vâng.", "Vâng bác sĩ.",
    "Dạ vâng ạ.", "Dạ tôi nhớ rồi.", "Vâng, tôi hiểu rồi.", "Em hiểu rồi ạ."
]

# Cơ chế làm sạch text cho ElevenLabs TTS:
def sanitize_spoken_text(text: str) -> str:
    # 1. Xóa bỏ hoàn toàn ngoặc đơn (), ngoặc vuông [], ngoặc nhọn {}
    # 2. Thay thế toàn bộ từ ngữ cấm:
    #    "dương tính" -> "có dấu hiệu tổn thương rõ"
    #    "lasegue" -> "kiểm tra nâng chân"
    #    "neer / hawkins" -> "động tác nâng và xoay vai"
    # 3. Loại bỏ ký tự đặc biệt, icon, emoji</code></pre>
      </td>
      <td valign="top">
<pre><code>Expand the conversation. The conversation for patient parts can be more colloquial. When the physician
is speaking, the patient can have many modal particles (e.g. hmm, yes, okay) to increase interaction.
All the numbers and medical concepts that appear in the note should be mentioned by the physician.
Professional medical terms and numbers should always occur in the physician’s utterances but not in
the patient’s answer. The physician may describe and explain professional judgment to the patient
and instruct the patient on follow-up requirements, but not ask questions that require professional
medical knowledge to answer and the question must be around the clinical note(the patient could
find the answer on the clinical note). All the information of medical history, symptoms and medication
history should be told by patient. The patient’s answer should be succinct and accurate in a
colloquial lay language style. The answer should align with the clinical notes and as colloquial
as possible. You can add some transitional phrases to make the conversation more logical.
For example:
Example 1:
Patient: I understand, please go ahead.
(After examination)
physician: The result shows....
Example 2:
Patient: Thank you for the diagnosis, physician.
(After two years)
physician: Hi...
Example 3:
Patient: Okay, I understand.
(Few days latter)
physician: Hi...
Your conversations must follow the logical sequence of a physician’s inquiry. For example, the general
logical order of the conversation is: first discussing symptoms, then discussing the
medical history, followed by discussing testing and results, and finally discussing treatment
options, conclusioin etc." If you find this conversation to be incoherent, you can try dividing it
into two separate coherent conversations. Patients should not say too much information at once.
The Clinical Note: Clinical Note
The Key Words: key1, key2,...
The History Conversation: Conversation
There are only one patient and one physician and just return the conversation. You conversation must
include all the key words I gave you.
Your conversation should also include all information. if it’s difficult to include them all, you
can use the original sentences in the notes.
The common symptoms and common medical history should be told by the patient.
Some specific symptoms and medical history should be added by the physician after the patient has
finished describing his symptoms and medical history.
For example:
physician: Can you give me your medical history record?
Patient: Here you are.
physician: Based on your medical history record...
Because after the patient has finished describing common symptoms or medical history, he will give
physician his medical history records.
After patient gives the physician his medical history record, the physician could know medical
history record. Otherwise he didn’t know any information of the medical history.
Some results should not come from history clinical note they should come from the examination.
All the examination results, history examination results, vital sigh and medical number must be told by physician.
The revised conversation should be at least around 30 to 40 utterances
(the physician or patient should say too much information at once).
The conversation must include all the information on the clinical note.
You must include all the key words I gave you. If it is difficult to include all the key words you
could use original the sentences of clinical note.
You cannot revise or eliminate any key words and you cannot use synonyms of the key words.
You shouldn’t use the abbreviation if you know the full name(you should use full name not
abbreviation, such as D9 must be day 9, D7 must be day 7. If both the full name and the abbreviation
appear, it’s better to use the full name rather than the abbreviation.
Patients must not say any highly specialized terms, medical terminology or medical dosage.
They can only describe limited common symptoms.
The physician should supplement the remaining information based on test results.
Don’t repeat the same information in long paragraphs. The utterance of the dialogue needs to be
expanded as much as possible.
Table 13: Polish prompt.</code></pre>
      </td>
      <td valign="top">
<b>1. LLM Polish Prompt vs Rule-based Engine:</b><br>
- <i>ACL 2024:</i> Phải gọi thêm 1 lượt LLM với Polish Prompt rất dài để mở rộng số lượt lên 30-40, tốn kém token và tiềm ẩn rủi ro hallucination làm sai lệch đơn thuốc.<br>
- <i>Hiện tại:</i> Dùng Rule-based Engine kết hợp Regex trong Python, xử lý tức thì (0ms, 0 token), an toàn tuyệt đối.<br><br>
<b>2. Xóa bỏ các chuyển cảnh phi lý:</b><br>
- <i>ACL 2024:</i> Cho phép các mốc nhảy cóc vô lý như <i>(After two years)</i>, <i>(Few days later)</i> trong cùng 1 văn bản ca khám.<br>
- <i>Hiện tại:</i> Đảm bảo tính liên tục của một phiên khám lâm sàng trực tiếp đúng 12 phút.<br><br>
<b>3. Cơ chế chèn câu đệm hai chiều 80%:</b><br>
- <i>ACL 2024:</i> Bệnh nhân chêm modal particles (hmm, yes, okay) thủ công do LLM tự sinh.<br>
- <i>Hiện tại:</i> Áp dụng quy tắc 1-cut rule cho các câu dài của cả bác sĩ và bệnh nhân, tự động chèn các câu đệm thuần Việt phong phú mà không tính vào số lượt khám lâm sàng chính.
      </td>
    </tr>
  </tbody>
</table>

---

## 5. MODULE 5: COMBINE PROMPT vs GRAPH STATE MACHINE

<table border="1" cellpadding="8" cellspacing="0" width="100%">
  <thead>
    <tr style="background-color: #f0f4f8; text-align: left;">
      <th width="38%">Cột 1: Prompt Hiện Tại (Trích nguyên gốc)</th>
      <th width="38%">Cột 2: Prompt ACL 2024 (Trích nguyên gốc tiếng Anh)</th>
      <th width="24%">Cột 3: Sự Khác Nhau</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">
<pre><code># Hệ thống KHÔNG sử dụng Combine Prompt vì luồng đối thoại được điều phối
# khép kín và liên tục thông qua StateGraph của LangGraph:

def build_notechat_graph():
    graph = StateGraph(NoteChatState)
    graph.add_node("planning", planning_node)
    graph.add_node("physician", physician_node)
    graph.add_node("checklist_update", checklist_update_node)
    graph.add_node("patient", patient_node)
    graph.add_node("closing", closing_node)
    graph.add_node("format_output", format_output_node)
    ...
    return graph.compile()

# Prompt kết thúc ngắn gọn tại closing_node:
Bạn là Bác sĩ {doc_name}. Buổi khám bệnh sắp kết thúc.
Dưới đây là lịch sử buổi khám:
{history_text}

Hãy đưa ra 1-2 câu kết luận ngắn gọn, ân cần (tối đa không quá 25-30 từ), dặn bệnh nhân giữ gìn sức khỏe, uống thuốc đúng giờ và hẹn ngày tái khám.
Trả về định dạng JSON duy nhất:
{
  "text": "Lời dặn dò kết thúc của Bác sĩ",
  "is_parsed": true
}</code></pre>
      </td>
      <td valign="top">
<pre><code>The above two paragraphs were extracted from a complete conversation.
Please concatenate the two dialogues together. Add ’physician:’ before the physician’s words
and ’Patient:’ before the patient’s words for easier differentiation.
Please combine these two dialogues.
It means that your generation should include all the information
such as dosage of the medication which is mentioned in the clinical note
if the dosage is not mentioned in the clinical not
you should not mention it and the length should be longer than
both of these two conversations even longer than the sum of them.
You should try to ensure that the dialogue is smooth,
and don’t use any greetings such as ’Hi there’, ’how are you feeling today?’,
’Hey’, ’Hello’ or any farewells in the dialogue.
The entire conversation takes place at the same time and place,
and revolves around the same patient and physician.
Try to make the conversation smoother. Try to make these two dialogues into one dialogue
that takes place at the same time and place. Modify this conversation
by deleting all greeting sentences
such as ’Hi’, ’Hey’, ’Hi there’, ’How are you feeling today’, and ’Good Morning’.
The conversation must include these key words:key1, key2, ...
and you should also eliminate the repeat parts.</code></pre>
      </td>
      <td valign="top">
<b>1. Ghép nối thủ công vs State Machine khép kín:</b><br>
- <i>ACL 2024:</i> Do giới hạn sinh của LLM, phải sinh từng đoạn nhỏ rồi dùng Combine Prompt để ghép nối lại với nhau.<br>
- <i>Hiện tại:</i> Sử dụng LangGraph StateGraph quản lý trạng thái luồng hội thoại từ đầu đến cuối một cách tự nhiên trong 1 phiên duy nhất.<br><br>
<b>2. Xử lý lời chào hỏi và tạm biệt:</b><br>
- <i>ACL 2024:</i> Bắt buộc xóa bỏ toàn bộ lời chào và tạm biệt (<i>deleting all greeting sentences...</i>) làm đoạn thoại bị cụt và mất tự nhiên.<br>
- <i>Hiện tại:</i> Giữ nguyên vẹn lời chào hỏi tạo thiện cảm ban đầu và lời cảm ơn, dặn dò ra về để đảm bảo tính nhân văn của giao tiếp thầy thuốc - người bệnh.<br><br>
<b>3. Xuất bản đồng bộ đa định dạng:</b><br>
- <i>Hiện tại:</i> <code>format_output_node</code> tự động sinh file Markdown hoàn chỉnh và xuất ra file Docs Text sạch để sao chép văn bản ngay lập tức.
      </td>
    </tr>
  </tbody>
</table>

---

## 6. MODULE 6: RAG SYLLABLE BUDGETING & AUTO-EXTENSION

<table border="1" cellpadding="8" cellspacing="0" width="100%">
  <thead>
    <tr style="background-color: #f0f4f8; text-align: left;">
      <th width="38%">Cột 1: Prompt Hiện Tại (Trích nguyên gốc)</th>
      <th width="38%">Cột 2: Prompt ACL 2024 (Trích nguyên gốc tiếng Anh)</th>
      <th width="24%">Cột 3: Sự Khác Nhau</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td valign="top">
<pre><code># Prompt Bù Thời Lượng Tự Động (Length Guard Auto-Extension trong server.py):

Đoạn kịch bản khám bệnh dưới đây mới có khoảng {actual_syllables} âm tiết lời thoại, cần đạt khoảng {target_syllables} âm tiết (tương đương {duration} phút). Hãy viết TIẾP phần tiếp theo — giữ đúng văn phong, nhân vật {req.doctor_name} và {req.patient_name}, không lặp lại ý đã có:
- BẮT ĐẦU TIMESTAMP TIẾP THEO TỪ [{last_time}] và kéo dài liên tục đến đủ [{duration:02d}:00].
- CHỈ CHỨA LỜI NÓI CẤT THÀNH TIẾNG. Tuyệt đối không chú thích hành động, cử chỉ trong ngoặc đơn hay ngoặc vuông.
- Bác sĩ dặn dò, giải thích kỹ hơn bằng lời nói (cách theo dõi cơn đau tại nhà, bài tập nhẹ, dấu hiệu nguy hiểm cần tái khám).
- Bệnh nhân hỏi thêm điều còn băn khoăn (tác dụng phụ của thuốc, chế độ ăn uống kiêng khem món gì, có nên chườm nóng/lạnh hay đắp thuốc lá ở nhà không).

KỊCH BẢN HIỆN TẠI:
{script_text}

Chỉ viết phần kịch bản nối tiếp tiếp theo (không nhắc lại phần trên):</code></pre>
      </td>
      <td valign="top">
<pre><code>(Không có trong bộ prompt của ACL 2024. ACL 2024 hoàn toàn phụ thuộc vào việc ước lượng số lượng lượt thoại trong Table 13 Polish prompt:
"The revised conversation should be at least around 30 to 40 utterances... The utterance of the dialogue needs to be expanded as much as possible.")</code></pre>
      </td>
      <td valign="top">
<b>1. Kiểm soát thời lượng bằng âm tiết (Syllable Budgeting):</b><br>
- <i>ACL 2024:</i> Dựa vào số lượt thoại mơ hồ (30-40 utterances). Một lượt có thể rất ngắn khiến tổng thời lượng nói thực tế chỉ kéo dài 3-4 phút.<br>
- <i>Hiện tại:</i> Tính toán chính xác theo ngân sách âm tiết tiếng Việt (150 âm tiết/phút; ca 12 phút = 1.800 âm tiết).<br><br>
<b>2. Chốt chặn độ dài tự động (Length Guard):</b><br>
- <i>Hiện tại:</i> Nếu kịch bản sinh ra bị hụt (< 85% ngưỡng yêu cầu), hệ thống tự động gọi Auto-Extension Prompt nối tiếp từ mốc timestamp cuối cùng đến đủ <code>[12:00]</code> mà không bị lặp lại ý cũ.
      </td>
    </tr>
  </tbody>
</table>
