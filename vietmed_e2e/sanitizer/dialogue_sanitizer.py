"""
Module: dialogue_sanitizer.py
Chức năng:
1. Chuẩn hóa text 100% sạch cho ElevenLabs TTS:
   - Xóa bỏ toàn bộ dấu ngoặc đơn (), ngoặc vuông [], ngoặc nhọn {} và nội dung giải thích bên trong.
   - Xóa bỏ mọi từ ngữ mô tả hành động, cử chỉ, nhãn sân khấu.
   - Cấm tuyệt đối rò rỉ tên nghiệm pháp chuyên môn (Lasegue, Neer, Hawkins, Phalen...) và từ 'dương tính/âm tính'.
2. Thuật toán phân tách câu Bác sĩ và chèn tự nhiên lượt đệm của Bệnh nhân ("Vâng", "Dạ", "Dạ vâng").
3. Tái phân bổ mốc thời gian Timestamp [mm:ss - mm:ss] chuẩn xác cho mô hình ElevenLabs Audio.
"""

import re
import random
from typing import List, Dict, Any, Optional, Tuple

# Danh mục nghiệm pháp và thuật ngữ cấm xuất hiện trong lời thoại phát ra miệng
MANEUVER_REPLACEMENTS = [
    # Thần kinh tọa & Cột sống
    (r"(?i)\bnghiệm\s+pháp\s+lasegue\b", "kiểm tra chân và vùng thắt lưng"),
    (r"(?i)\blasegue\b", "kiểm tra nâng chân"),
    (r"(?i)\bnghiệm\s+pháp\s+schober\b", "kiểm tra độ giãn cột sống"),
    (r"(?i)\bschober\b", "kiểm tra cột sống"),
    (r"(?i)\bnghiệm\s+pháp\s+neri\b", "kiểm tra cúi gập lưng"),
    (r"(?i)\bnghiệm\s+pháp\s+valleix\b", "kiểm tra các điểm đau dọc dây thần kinh"),
    (r"(?i)\bđiểm\s+valleix\b", "điểm đau dọc đường đi dây thần kinh"),
    
    # Khớp vai
    (r"(?i)\bnghiệm\s+pháp\s+neer\b", "kiểm tra nâng khớp vai lên cao"),
    (r"(?i)\bneer\b", "động tác giơ tay"),
    (r"(?i)\bnghiệm\s+pháp\s+hawkins(?:-kennedy)?\b", "kiểm tra xoay vai trong"),
    (r"(?i)\bhawkins(?:-kennedy)?\b", "động tác xoay vai"),
    (r"(?i)\bnghiệm\s+pháp\s+jobe\b", "kiểm tra sức nâng gân vai"),
    (r"(?i)\bjobe\b", "kiểm tra sức cơ vai"),
    (r"(?i)\bempty\s+can(?:\s+test)?\b", "kiểm tra nâng tay chéo"),
    (r"(?i)\bdrop\s+arm(?:\s+sign|\s+test)?\b", "kiểm tra dấu hiệu rơi tay"),
    (r"(?i)\byergason(?:\s+test)?\b", "kiểm tra gân nhị đầu"),
    (r"(?i)\bspeed(?:\s+test)?\b", "kiểm tra gân cơ cánh tay"),
    
    # Khớp gối
    (r"(?i)\bngăn\s+kéo\s+trước\b", "kiểm tra dây chằng khớp gối"),
    (r"(?i)\bngăn\s+kéo\s+sau\b", "kiểm tra độ vững khớp gối"),
    (r"(?i)\blachman(?:\s+test)?\b", "kiểm tra độ lỏng khớp gối"),
    (r"(?i)\bmcmurray(?:\s+test)?\b", "kiểm tra sụn chêm khớp gối"),
    (r"(?i)\bbập\s+bềnh\s+xương\s+bánh\s+chè\b", "kiểm tra dịch trong bao khớp gối"),
    (r"(?i)\bdấu\s+hiệu\s+bào\s+bánh\s+chè\b", "kiểm tra tiếng lạo xạo dưới xương bánh chè"),
    
    # Bàn tay & Cổ tay
    (r"(?i)\bnghiệm\s+pháp\s+phalen\b", "kiểm tra gập cổ tay"),
    (r"(?i)\bphalen\b", "động tác gập cổ tay"),
    (r"(?i)\bdấu\s+hiệu\s+tinel\b", "gõ nhẹ kiểm tra cảm giác tê bì"),
    (r"(?i)\btinel\b", "kiểm tra cảm giác tê tay"),
    (r"(?i)\bfinkelstein(?:\s+test)?\b", "kiểm tra gân ngón tay cái"),
    
    # Từ ngữ chuyên môn cấm nói ra miệng
    (r"(?i)\bdương\s+tính\b", "có dấu hiệu tổn thương rõ"),
    (r"(?i)\bâm\s+tính\b", "ở mức bình thường"),
    (r"(?i)\bnghiệm\s+pháp\b", "động tác kiểm tra"),
]

# Kho từ đệm của Bệnh nhân theo độ tuổi / phong cách (Vâng, Vâng ạ, Dạ, Dạ vâng...)
ELDER_BACKCHANNELS = [
    "Vâng.",
    "Dạ.",
    "Vâng ạ.",
    "Dạ vâng.",
    "Vâng bác sĩ.",
    "Dạ vâng ạ.",
    "Dạ tôi nhớ rồi.",
    "Vâng, tôi hiểu rồi.",
    "Vâng, tôi nghe đây bác sĩ.",
    "Dạ, thế hả bác sĩ?",
    "Vâng, đúng thế bác ạ."
]

YOUNG_BACKCHANNELS = [
    "Dạ.",
    "Vâng ạ.",
    "Dạ vâng.",
    "Vâng bác sĩ.",
    "Dạ vâng ạ.",
    "Em hiểu rồi ạ.",
    "Vâng ạ."
]

# Kho từ đệm của Bác sĩ khi lắng nghe người bệnh kể bệnh (Vâng, Vâng ạ, Tôi hiểu rồi, Ừm, Rồi...)
DOCTOR_BACKCHANNELS = [
    "Vâng ạ.",
    "Vâng.",
    "Tôi hiểu rồi.",
    "Ừm, tôi nghe đây.",
    "Rồi.",
    "Vâng, bác cứ nói tiếp đi.",
    "Vâng, tôi nắm được rồi.",
    "Ừm.",
    "Vâng, tôi hiểu.",
    "Rồi ạ."
]

def get_doctor_backchannel(index: int = 0) -> str:
    """Trả về từ đệm phong phú cho Bác sĩ khi lắng nghe bệnh nhân kể bệnh."""
    return DOCTOR_BACKCHANNELS[index % len(DOCTOR_BACKCHANNELS)]

def sanitize_spoken_text(text: str) -> str:
    """
    Làm sạch 100% lời nói để đưa vào mô hình ElevenLabs Text-to-Speech:
    1. Xóa bỏ hoàn toàn mọi nội dung trong ngoặc đơn (...), ngoặc vuông [...], ngoặc nhọn {...}.
    2. Xóa bỏ mọi ký tự ngoặc lẻ thừa.
    3. Xóa các tiền tố vai thoại (Bác sĩ:, Bệnh nhân:, - **...**:).
    4. Thay thế triệt để các tên nghiệm pháp khoa học và từ 'dương tính/âm tính'.
    5. Chuẩn hóa khoảng trắng và dấu câu.
    """
    if not text:
        return ""
        
    s = text.strip()
    
    # 1. Xóa các prefix vai thoại thừa nếu có
    s = re.sub(r"^-\s*\*\*[^*]+\*\*\:?\s*", "", s)
    s = re.sub(r"^(?:Bác sĩ|Bác sĩ [^:]+|Bệnh nhân|Physician|Doctor|Patient)\:?\s*", "", s, flags=re.IGNORECASE)
    
    # 2. Xóa sạch mọi cặp ngoặc và toàn bộ chữ bên trong (mô tả hành động, stage directions)
    s = re.sub(r"\([^\)]*\)", " ", s)  # (bác sĩ cười, nhăn mặt, làm nghiệm pháp...)
    s = re.sub(r"\[[^\]]*\]", " ", s)  # [hành động...]
    s = re.sub(r"\{[^\}]*\}", " ", s)  # {giải thích...}
    
    # 3. Xóa các ký tự ngoặc còn sót lại nếu unclosed
    s = re.sub(r"[\(\)\[\]\{\}]", " ", s)
    
    # 4. Xóa bỏ các ký tự định dạng markdown thừa
    s = re.sub(r"[\*_~`]", "", s)
    
    # 5. Rà soát & thay thế tên nghiệm pháp bị leak
    for pattern, replacement in MANEUVER_REPLACEMENTS:
        s = re.sub(pattern, replacement, s)
        
    # 6. Chuẩn hóa khoảng trắng và dấu câu
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*([.,?!;:])", r"\1", s)
    s = re.sub(r"([.,?!;:])\1+", r"\1", s)
    
    # Viết hoa chữ cái đầu nếu chưa viết hoa
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
        
    return s

def split_into_sentences(text: str) -> List[str]:
    """
    Phân tách một đoạn văn dài thành danh sách các câu hoàn chỉnh,
    bảo vệ các chữ viết tắt thường gặp trong y tế (TP.HCM, BS., mg., ml.,...).
    """
    if not text:
        return []
        
    # Đánh dấu tạm các viết tắt
    safe_text = text
    abbreviations = [
        ("TP.HCM", "TP_HCM"),
        ("TP. HCM", "TP_HCM"),
        ("BS.", "BS_DOT"),
        ("Bs.", "BS_DOT"),
        ("ThS.", "THS_DOT"),
        ("TS.", "TS_DOT"),
        ("GS.", "GS_DOT"),
        ("mg.", "MG_DOT"),
        ("ml.", "ML_DOT"),
        ("độ.", "DO_DOT"),
    ]
    for orig, rep in abbreviations:
        safe_text = safe_text.replace(orig, rep)
        
    # Tách câu theo dấu chấm, chấm than, hỏi chấm, hoặc xuống dòng
    raw_sentences = re.split(r"(?<=[.!?\n])\s+", safe_text)
    
    clean_sentences = []
    for s in raw_sentences:
        # Khôi phục viết tắt
        for orig, rep in abbreviations:
            s = s.replace(rep, orig)
        s = s.strip()
        if len(s) > 0:
            clean_sentences.append(s)
            
    # Gộp các câu quá ngắn (< 15 ký tự) vào câu kế tiếp để tránh vụn vặt
    merged = []
    buffer = ""
    for s in clean_sentences:
        if buffer:
            buffer += " " + s
            if len(buffer) >= 20:
                merged.append(buffer.strip())
                buffer = ""
        else:
            if len(s) < 20 and len(clean_sentences) > 1:
                buffer = s
            else:
                merged.append(s)
    if buffer:
        if merged:
            merged[-1] += " " + buffer
        else:
            merged.append(buffer)
            
    return merged if merged else [text]

def split_long_sentence_by_clauses(sentence: str, max_words: int = 25) -> List[str]:
    """Tách câu đơn quá dài (> 25-30 từ) tại các dấu phẩy, chấm phẩy hoặc liên từ để đảm bảo không bị dài bất thường."""
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence]
        
    # Thử tách theo dấu phẩy hoặc chấm phẩy
    parts = re.split(r'(?<=[,;])\s+', sentence)
    if len(parts) > 1:
        merged = []
        current = ""
        for p in parts:
            if not current:
                current = p
            elif len((current + " " + p).split()) <= max_words:
                current += " " + p
            else:
                merged.append(current.strip())
                current = p
        if current:
            merged.append(current.strip())
        if len(merged) > 1:
            return merged
            
    # Nếu không có dấu phẩy, tách theo liên từ
    conjunctions = [r'\bvà\b', r'\bnhưng\b', r'\bđồng thời\b', r'\bsau đó\b']
    for conj in conjunctions:
        splits = re.split(f'(?<={conj})\\s+', sentence, flags=re.IGNORECASE)
        if len(splits) > 1:
            return [s.strip() for s in splits if s.strip()]
            
    return [sentence]

def get_backchannel(persona: str = "", age: int = 60, index: int = 0) -> str:
    """Trả về từ đệm phong phú cho Bệnh nhân."""
    pool = ELDER_BACKCHANNELS if age >= 45 else YOUNG_BACKCHANNELS
    # Xoay vòng và chọn ngẫu nhiên có trọng số nhẹ
    choice = pool[index % len(pool)]
    return choice

def split_turn_into_two_halves(clean_text: str) -> Optional[Tuple[str, str]]:
    """
    Chia 1 lượt thoại thành đúng 2 nửa cân đối tại ranh giới câu hoặc mệnh đề chính giữa.
    Trả về (part1, part2) hoặc None nếu không đủ điều kiện chia đôi.
    """
    raw_sentences = split_into_sentences(clean_text)
    # Nếu có từ 2 câu trở lên: ngắt ở câu chính giữa
    if len(raw_sentences) >= 2:
        mid_idx = max(1, len(raw_sentences) // 2)
        part1 = " ".join(raw_sentences[:mid_idx]).strip()
        part2 = " ".join(raw_sentences[mid_idx:]).strip()
        if part1 and part2:
            return part1, part2
            
    # Nếu chỉ có 1 câu nhưng dài (>= 16 từ), tìm dấu phẩy, chấm phẩy hoặc liên từ ở khoảng giữa câu
    words = clean_text.split()
    if len(words) >= 16:
        clauses = re.split(r'(?<=[,;])\s+', clean_text)
        if len(clauses) >= 2:
            mid_clause = max(1, len(clauses) // 2)
            part1 = " ".join(clauses[:mid_clause]).strip()
            part2 = " ".join(clauses[mid_clause:]).strip()
            if part1 and part2:
                return part1, part2
                
    return None

def inject_patient_backchannels(
    turns: List[Dict[str, Any]],
    patient_name: str = "Bác Hùng",
    doctor_name: str = "Bác sĩ Hoàng",
    patient_age: int = 60,
    patient_persona: str = "",
    min_sentences_to_split: int = 2,
    backchannel_rate: float = 0.80,
    split_probability: float = 0.90,
    max_words_per_turn: int = 30,
    max_sentences_per_turn: int = 3
) -> List[Dict[str, Any]]:
    """
    Kiểm soát lượt thoại & Chèn lời đệm tương tác hai chiều (Quy tắc 1 & 3):
    1. Chỉ cắt khi lượt thoại đó có is_parsed == True.
    2. Mỗi lượt thoại CHỈ CẮT ĐÚNG 1 LẦN Ở GIỮA (chèn duy nhất 1 câu đệm, chia làm 2 phần cân đối).
       Tuyệt đối không cắt dồn dập sau mỗi dấu câu gây phiền toái.
    3. Áp dụng xác suất 80% (backchannel_rate) cho các câu có is_parsed == True.
    """
    new_turns = []
    patient_backchannel_counter = 0
    doctor_backchannel_counter = 0
    clinical_turn_index = 0
    
    for t in turns:
        clinical_turn_index += 1
        speaker = t.get("speaker") or t.get("role") or "doctor"
        is_doctor = speaker in ["doctor", "physician"]
        raw_text = t.get("text") or t.get("content") or ""
        clean_text = sanitize_spoken_text(raw_text)
        is_parsed = t.get("is_parsed")
        stage = t.get("stage") or ("Hỏi bệnh & Thăm khám" if is_doctor else "Kể bệnh & Phản hồi")
        clinical_action = t.get("clinicalAction")
        covered_item = t.get("covered_item") or t.get("covered_checklist")
        
        # ĐIỀU KIỆN 1: Bắt buộc phải có is_parsed == True mới được xem xét cắt câu
        # Nếu is_parsed là False hoặc None -> Giữ nguyên 100%, không ngắt
        if is_parsed is not True:
            t_copy = dict(t)
            t_copy["turn_id"] = clinical_turn_index
            t_copy["turn_number"] = clinical_turn_index
            t_copy["text"] = clean_text
            t_copy["content"] = clean_text
            t_copy["is_parsed"] = False
            t_copy["is_backchannel"] = False
            t_copy["is_counted_turn"] = True
            new_turns.append(t_copy)
            continue
            
        # ĐIỀU KIỆN 3: Tỷ lệ ngẫu nhiên ~40% (backchannel_rate)
        # Nếu không trúng tỷ lệ -> Giữ nguyên lượt, không cắt
        if random.random() > backchannel_rate:
            t_copy = dict(t)
            t_copy["turn_id"] = clinical_turn_index
            t_copy["turn_number"] = clinical_turn_index
            t_copy["text"] = clean_text
            t_copy["content"] = clean_text
            t_copy["is_parsed"] = True
            t_copy["is_backchannel"] = False
            t_copy["is_counted_turn"] = True
            new_turns.append(t_copy)
            continue
            
        # ĐIỀU KIỆN 2: CHỈ CẮT ĐÚNG 1 LẦN Ở GIỮA (chia 2 nửa cân đối, chèn 1 lời đệm)
        halves = split_turn_into_two_halves(clean_text)
        if not halves:
            # Không thể chia đôi (câu quá ngắn hoặc không có điểm ngắt phù hợp) -> Giữ nguyên
            t_copy = dict(t)
            t_copy["turn_id"] = clinical_turn_index
            t_copy["turn_number"] = clinical_turn_index
            t_copy["text"] = clean_text
            t_copy["content"] = clean_text
            t_copy["is_parsed"] = True
            t_copy["is_backchannel"] = False
            t_copy["is_counted_turn"] = True
            new_turns.append(t_copy)
            continue
            
        part1, part2 = halves
        
        if is_doctor:
            # === BÁC SĨ ĐƯỢC CHIA ĐÔI: BỆNH NHÂN CHÈN ĐÚNG 1 CÂU ĐỆM Ở GIỮA ===
            # Nửa đầu của Bác sĩ (Bắt đầu lượt clinical_turn_index)
            new_turns.append({
                "turn_id": clinical_turn_index,
                "turn_number": clinical_turn_index,
                "speaker": "physician",
                "role": "physician",
                "speaker_name": t.get("speaker_name") or doctor_name,
                "speakerName": t.get("speakerName") or doctor_name,
                "stage": stage,
                "text": part1,
                "content": part1,
                "clinicalAction": clinical_action,
                "covered_item": covered_item,
                "covered_checklist": covered_item,
                "is_parsed": True,
                "is_backchannel": False,
                "is_counted_turn": True,
                "sub_turn": "part1"
            })
            
            # Đúng 1 câu đệm duy nhất của Bệnh nhân ("Vâng.", "Dạ.", "Vâng ạ.") - KHÔNG TÍNH LÀ LƯỢT ĐỐI THOẠI ĐỘC LẬP
            bc_text = get_backchannel(patient_persona, patient_age, patient_backchannel_counter)
            patient_backchannel_counter += 1
            new_turns.append({
                "turn_id": clinical_turn_index,
                "turn_number": clinical_turn_index,
                "speaker": "patient",
                "role": "patient",
                "speaker_name": patient_name,
                "speakerName": patient_name,
                "stage": "Phản hồi xác nhận",
                "text": bc_text,
                "content": bc_text,
                "clinicalAction": None,
                "covered_item": "Xác nhận lời bác sĩ",
                "covered_checklist": "Xác nhận lời bác sĩ",
                "is_backchannel": True,
                "is_counted_turn": False,
                "parent_turn_id": clinical_turn_index,
                "sub_turn": "backchannel"
            })
            
            # Nửa sau của Bác sĩ (Tiếp tục lượt clinical_turn_index, KHÔNG TÍNH THÀNH LƯỢT MỚI)
            new_turns.append({
                "turn_id": clinical_turn_index,
                "turn_number": clinical_turn_index,
                "speaker": "physician",
                "role": "physician",
                "speaker_name": t.get("speaker_name") or doctor_name,
                "speakerName": t.get("speakerName") or doctor_name,
                "stage": stage,
                "text": part2,
                "content": part2,
                "clinicalAction": None,
                "covered_item": covered_item,
                "covered_checklist": covered_item,
                "is_parsed": True,
                "is_backchannel": False,
                "is_counted_turn": False,
                "is_continuation": True,
                "sub_turn": "part2"
            })
        else:
            # === BỆNH NHÂN ĐƯỢC CHIA ĐÔI: BÁC SĨ CHÈN ĐÚNG 1 CÂU ĐỆM Ở GIỮA ===
            # Nửa đầu của Bệnh nhân (Bắt đầu lượt clinical_turn_index)
            new_turns.append({
                "turn_id": clinical_turn_index,
                "turn_number": clinical_turn_index,
                "speaker": "patient",
                "role": "patient",
                "speaker_name": t.get("speaker_name") or patient_name,
                "speakerName": t.get("speakerName") or patient_name,
                "stage": stage,
                "text": part1,
                "content": part1,
                "clinicalAction": None,
                "covered_item": covered_item,
                "covered_checklist": covered_item,
                "is_parsed": True,
                "is_backchannel": False,
                "is_counted_turn": True,
                "sub_turn": "part1"
            })
            
            # Đúng 1 câu đệm duy nhất của Bác sĩ ("Vâng ạ.", "Tôi hiểu rồi.", "Vâng.", ...) - KHÔNG TÍNH LÀ LƯỢT ĐỐI THOẠI ĐỘC LẬP
            doc_bc = get_doctor_backchannel(doctor_backchannel_counter)
            doctor_backchannel_counter += 1
            new_turns.append({
                "turn_id": clinical_turn_index,
                "turn_number": clinical_turn_index,
                "speaker": "physician",
                "role": "physician",
                "speaker_name": doctor_name,
                "speakerName": doctor_name,
                "stage": "Lắng nghe bệnh nhân",
                "text": doc_bc,
                "content": doc_bc,
                "clinicalAction": None,
                "covered_item": "Lắng nghe và ghi nhận",
                "covered_checklist": "Lắng nghe và ghi nhận",
                "is_backchannel": True,
                "is_counted_turn": False,
                "parent_turn_id": clinical_turn_index,
                "sub_turn": "backchannel"
            })
            
            # Nửa sau của Bệnh nhân (Tiếp tục lượt clinical_turn_index, KHÔNG TÍNH THÀNH LƯỢT MỚI)
            new_turns.append({
                "turn_id": clinical_turn_index,
                "turn_number": clinical_turn_index,
                "speaker": "patient",
                "role": "patient",
                "speaker_name": t.get("speaker_name") or patient_name,
                "speakerName": t.get("speakerName") or patient_name,
                "stage": stage,
                "text": part2,
                "content": part2,
                "clinicalAction": None,
                "covered_item": covered_item,
                "covered_checklist": covered_item,
                "is_parsed": True,
                "is_backchannel": False,
                "is_counted_turn": False,
                "is_continuation": True,
                "sub_turn": "part2"
            })

    # Đánh số thứ tự phân đoạn âm thanh (segment_id cho ElevenLabs TTS)
    # Trong khi turn_id vẫn giữ đúng số lượt y khoa thực tế (1..clinical_turn_index)
    for seg_idx, t in enumerate(new_turns, 1):
        t["segment_id"] = seg_idx
        t["segment_number"] = seg_idx
        t["id"] = f"seg-{seg_idx}"
        if "turnNumber" in t:
            t["turnNumber"] = t["turn_id"]
            
    return new_turns

def recalculate_timestamps_for_turns(
    turns: List[Dict[str, Any]],
    duration_minutes: int = 8
) -> List[Dict[str, Any]]:
    """
    Tính toán lại timestamp [mm:ss - mm:ss] cho từng lượt thoại
    đảm bảo nhịp đọc ElevenLabs Audio chuẩn xác:
    - Lượt đệm ngắn ("Vâng.", "Dạ.") chiếm ~1.5 - 2 giây.
    - Lượt câu dài chiếm thời gian theo số âm tiết (khoảng 3 âm tiết / giây).
    """
    total_target_sec = max(180, duration_minutes * 60)
    
    # Ước tính trọng số thời lượng theo độ dài text
    weights = []
    for t in turns:
        txt = t.get("text") or t.get("content") or ""
        word_count = len(txt.split())
        # Câu đệm 1-2 từ: gán trọng số tối thiểu tương đương 2 giây
        if word_count <= 2:
            weights.append(2.0)
        else:
            # Ước tính số giây = số từ * 0.4s
            weights.append(max(2.5, word_count * 0.38))
            
    sum_weight = sum(weights) if sum(weights) > 0 else 1.0
    scale = total_target_sec / sum_weight
    
    current_sec = 0.0
    for idx, t in enumerate(turns):
        dur = weights[idx] * scale
        start_sec = current_sec
        end_sec = current_sec + dur
        current_sec = end_sec
        
        start_m = int(start_sec // 60)
        start_s = int(start_sec % 60)
        end_m = int(end_sec // 60)
        end_s = int(end_sec % 60)
        
        ts = f"[{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}]"
        t["timestamp"] = ts
        t["audioDuration"] = round(dur, 1)
        
    return turns

# Alias hỗ trợ đồng thời hai chiều Bác sĩ & Bệnh nhân
inject_bidirectional_backchannels = inject_patient_backchannels

