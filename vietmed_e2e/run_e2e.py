# -*- coding: utf-8 -*-
"""
vietmed_e2e/run_e2e.py
CLI Entry Point & Bộ điều phối thực thi Pipeline VietMed E2E:
1. Sinh Hồ sơ Bệnh nhân (9 trường) & Bác sĩ (6 trường) bám sát Tri thức 60 bệnh.
2. Thiết lập cơ chế Sương mù thông tin (Fog of War) theo tiến trình lâm sàng.
3. Mô phỏng hội thoại lâm sàng đa tác tử (Physician-LLM, Patient-LLM, Polish-LLM).
4. Xuất kết quả tự động ra D:\\test STT\\output-600 theo đúng quy tắc đặt tên chuẩn.
"""

import os
import sys
import re
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from vietmed_e2e.config import (
    WORKSPACE_ROOT,
    OUTPUT_600_DIR,
    INPUT_600_DIR,
    DEFAULT_MODEL,
    LLM_PROVIDER
)
from vietmed_e2e.knowledge.kb_loader import kb_instance
from vietmed_e2e.pipeline import vietmed_e2e_pipeline
from vietmed_e2e.schemas.state import E2EState
from vietmed_e2e.sanitizer.dialogue_sanitizer import (
    sanitize_spoken_text,
    recalculate_timestamps_for_turns
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_group_dir_name(stt: int) -> str:
    """Xác định tên thư mục nhóm bệnh theo STT chuẩn 1-60."""
    if 1 <= stt <= 30:
        return "nhom_1_co_xuong_khop_day_chang"
    elif 31 <= stt <= 38:
        return "nhom_2_than_kinh"
    elif 39 <= stt <= 45:
        return "nhom_3_tieu_hoa_gan_mat"
    elif 46 <= stt <= 51:
        return "nhom_4_tim_mach_ho_hap"
    elif 52 <= stt <= 56:
        return "nhom_5_tiet_nieu_phu_khoa"
    elif 57 <= stt <= 60:
        return "nhom_6_tai_mui_hong_mat_rhm"
    else:
        return "nhom_khac"

def extract_scenario_seed_from_input_600(stt: int, scenario_idx: int) -> Dict[str, Any]:
    """
    Trích xuất thông tin hạt giống (seed) từ thư mục input-600 nếu có.
    """
    group_name = get_group_dir_name(stt)
    group_path = INPUT_600_DIR / group_name
    if not group_path.exists():
        return {}

    # Tìm file markdown tương ứng với STT
    target_file = None
    for f in group_path.glob("*.md"):
        prefix = f"KB_{stt:02d}_"
        if f.name.startswith(prefix) or f"STT {stt:02d}" in f.name:
            target_file = f
            break

    if not target_file or not target_file.exists():
        return {}

    try:
        with open(target_file, "r", encoding="utf-8") as fp:
            content = fp.read()

        # Tìm kịch bản thứ scenario_idx
        kb_pattern = rf"###\s*Kịch bản\s*{scenario_idx:02d}:.*?(?=###\s*Kịch bản\s*\d{{2}}:|$)"
        match = re.search(kb_pattern, content, re.DOTALL | re.IGNORECASE)
        if not match:
            return {}

        section = match.group(0)
        seed: Dict[str, Any] = {}

        # Parse Bác sĩ
        doc_match = re.search(r"Bác sĩ\s+([^(\n]+?)\s*\((Nam|Nữ)", section, re.IGNORECASE)
        if doc_match:
            seed["doctor_name"] = f"Bác sĩ {doc_match.group(1).strip()}"
            seed["doctor_gender"] = doc_match.group(2).strip()

        # Parse Bệnh nhân
        pat_match = re.search(r"Bệnh nhân\s+([^(\n]+?)\s*\((\d+)\s*tuổi,\s*(Nam|Nữ)(?:,\s*([^)]+))?\)", section, re.IGNORECASE)
        if pat_match:
            seed["patient_name"] = pat_match.group(1).strip()
            seed["patient_age"] = int(pat_match.group(2).strip())
            seed["patient_gender"] = pat_match.group(3).strip()
            if pat_match.group(4):
                seed["occupation"] = pat_match.group(4).strip()

        return seed
    except Exception as ex:
        print(f"[Seed Warning] Không thể trích xuất seed từ input-600: {ex}", flush=True)
        return {}

def run_e2e_simulation(
    disease_stt: int = 1,
    scenario_index: int = 1,
    duration_minutes: int = 12,
    target_turns: int = 28,
    sentiment: str = "Positive",
    patient_name: Optional[str] = None,
    patient_age: Optional[int] = None,
    patient_gender: Optional[str] = None,
    patient_occupation: Optional[str] = None,
    doctor_name: Optional[str] = None,
    doctor_gender: Optional[str] = None,
    force_prior_visit: Optional[bool] = None,
    force_confirm_identity: Optional[bool] = None,
    model_name: Optional[str] = None,
    llm_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Hàm thực thi toàn diện luồng E2E từ tri thức chuẩn đến hội thoại hoàn chỉnh.
    """
    if llm_provider:
        os.environ["LLM_PROVIDER"] = llm_provider
    if model_name:
        os.environ["OPENROUTER_MODEL"] = model_name

    current_provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER)
    current_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)

    # 1. Nạp tri thức chuẩn từ KB
    kb_entry = kb_instance.get_disease(disease_stt)
    if not kb_entry:
        raise ValueError(f"Không tìm thấy bệnh lý có STT: {disease_stt} trong cơ sở tri thức 60 bệnh!")

    disease_name = kb_entry.get("name", f"Bệnh STT {disease_stt}")
    specialty_group = kb_entry.get("category", get_group_dir_name(disease_stt))

    # 2. Đọc hạt giống từ input-600 nếu người dùng chưa chỉ định ghi đè
    seed = extract_scenario_seed_from_input_600(disease_stt, scenario_index)

    p_name = patient_name or seed.get("patient_name")
    p_age = patient_age or seed.get("patient_age")
    p_gender = patient_gender or seed.get("patient_gender")
    p_occ = patient_occupation or seed.get("occupation")
    d_name = doctor_name or seed.get("doctor_name")
    d_gender = doctor_gender or seed.get("doctor_gender")

    loop_target = max(18, int(target_turns * 0.85))
    hard_limit = loop_target + 12

    initial_state: E2EState = {
        "kb_entry": kb_entry,
        "disease_stt": disease_stt,
        "disease_name": disease_name,
        "specialty_group": specialty_group,
        "sentiment": sentiment,
        "scenario_index": scenario_index,
        "force_prior_visit": force_prior_visit,
        "force_confirm_identity": force_confirm_identity,
        "patient_name": p_name,
        "age": p_age,
        "gender": p_gender,
        "occupation": p_occ,
        "doctor_name": d_name,
        "doctor_gender": d_gender,
        "validation_passed": False,
        "validation_errors": [],
        "repair_attempts": 0,
        "max_repairs": 2,
        "target_turns": loop_target,
        "max_hard_limit": hard_limit,
        "duration_minutes": duration_minutes,
        "checklist": [],
        "completed_checklist": [],
        "current_focus": None,
        "turns": [],
        "polished_turns": None,
        "current_turn_count": 0,
        "is_finished": False,
        "final_markdown": ""
    }

    print("\n" + "="*80)
    print(f"🏥 VIETMED E2E PIPELINE: STT {disease_stt:02d} - {disease_name.upper()}")
    print(f"   Kịch bản: KB{scenario_index:02d} | Thời lượng: ~{duration_minutes} phút | Mục tiêu: ~{target_turns} lượt")
    print(f"   Model: {current_model} qua {current_provider}")
    print("="*80 + "\n")

    start_time = time.time()
    final_state = vietmed_e2e_pipeline.invoke(initial_state, config={"recursion_limit": 400})
    exec_time = time.time() - start_time

    # 3. Trích xuất thông tin kết quả
    pat_profile = final_state.get("final_patient", {})
    doc_profile = final_state.get("final_doctor", {})
    # Ưu tiên dùng polished_turns (đã được polish + sanitize), fallback sang turns thô
    turns = final_state.get("polished_turns") or final_state.get("turns", [])
    total_turns = len(turns)

    # Đảm bảo timestamp được tính chuẩn
    final_turns = recalculate_timestamps_for_turns(turns, duration_minutes=duration_minutes)

    # 4. Tạo nội dung docs.txt (text thuần) và markdown.md
    group_dir = get_group_dir_name(disease_stt)
    output_text_dir = OUTPUT_600_DIR / group_dir / "texts"
    output_voice_dir = OUTPUT_600_DIR / group_dir / "voices"
    output_text_dir.mkdir(parents=True, exist_ok=True)
    output_voice_dir.mkdir(parents=True, exist_ok=True)

    base_filename = f"Benh{disease_stt:02d}_KB{scenario_index:02d}"

    # Header chung
    p_gender_str = pat_profile.get("gender", "Nam")
    d_gender_str = doc_profile.get("gender", "Nam")
    pair_gender = f"{d_gender_str} – {p_gender_str} ({d_gender_str[0]}-{p_gender_str[0]})"

    # Ghi file docs.txt
    docs_lines = [
        f"KỊCH BẢN ĐỐI THOẠI KHÁM BỆNH: {disease_name.upper()}",
        f"Mã kịch bản: {base_filename} (Chuyên khoa: {specialty_group})",
        f"Bác sĩ: {doc_profile.get('name')} ({doc_profile.get('gender')}, {doc_profile.get('communication_tone', '')})",
        f"Bệnh nhân: {pat_profile.get('name')} ({pat_profile.get('age')} tuổi, {pat_profile.get('gender')}, {pat_profile.get('occupation')}, {pat_profile.get('speaking_style', '')})",
        f"Tổng số lượt thoại: {total_turns} lượt khám lâm sàng | Cặp giới tính: {pair_gender}",
        "",
        "---",
        ""
    ]
    for t in final_turns:
        ts = t.get("timestamp", "[00:00 - 00:00]")
        speaker = t.get("speaker_name", "Bác sĩ" if t.get("speaker") in ["physician", "doctor"] else "Bệnh nhân")
        clean_text = sanitize_spoken_text(t.get("text", ""))
        docs_lines.append(f"{ts} {speaker}: {clean_text}")

    docs_content = "\n".join(docs_lines)
    docs_path = output_text_dir / f"{base_filename}_docs.txt"
    with open(docs_path, "w", encoding="utf-8") as fp:
        fp.write(docs_content)

    # Ghi file markdown.md
    md_lines = [
        f"# KỊCH BẢN ĐỐI THOẠI KHÁM BỆNH: {disease_name.upper()}",
        f"> **Mã kịch bản:** {base_filename} (Chuyên khoa: {specialty_group})",
        f"> **Bác sĩ:** {doc_profile.get('name')} ({doc_profile.get('gender')}, {doc_profile.get('communication_tone', '')})",
        f"> **Bệnh nhân:** {pat_profile.get('name')} ({pat_profile.get('age')} tuổi, {pat_profile.get('gender')}, {pat_profile.get('occupation')}, {pat_profile.get('speaking_style', '')})",
        f"> **Tổng số lượt thoại:** {total_turns} lượt khám lâm sàng | **Cặp giới tính:** {pair_gender}",
        "",
        "---",
        ""
    ]
    for t in final_turns:
        ts = t.get("timestamp", "[00:00 - 00:00]")
        speaker = t.get("speaker_name", "Bác sĩ" if t.get("speaker") in ["physician", "doctor"] else "Bệnh nhân")
        clean_text = sanitize_spoken_text(t.get("text", ""))
        md_lines.append(f"- **`{ts}` {speaker}:** {clean_text}")

    md_content = "\n".join(md_lines)
    md_path = output_text_dir / f"{base_filename}_markdown.md"
    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write(md_content)

    # Ghi file profile metadata json để phục vụ kiểm tra và tái sử dụng
    profile_audit = {
        "metadata": {
            "disease_stt": disease_stt,
            "disease_name": disease_name,
            "specialty_group": specialty_group,
            "scenario_index": scenario_index,
            "total_turns": total_turns,
            "duration_minutes": duration_minutes,
            "execution_time_seconds": round(exec_time, 2),
            "model": current_model,
            "provider": current_provider,
            "validation_passed": final_state.get("validation_passed", False),
            "repair_attempts": final_state.get("repair_attempts", 0)
        },
        "patient_profile": pat_profile,
        "doctor_profile": doc_profile,
        "checklist": final_state.get("completed_checklist", []) + final_state.get("checklist", []),
        "reveal_sequence": final_state.get("reveal_sequence", [])
    }
    json_path = output_text_dir / f"{base_filename}_profile.json"
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(profile_audit, fp, ensure_ascii=False, indent=2)

    # Ghi file ground_truth_form.json (khung form bệnh án đau toàn diện)
    gt_form = final_state.get("ground_truth_form")
    form_path = None
    if gt_form:
        form_path = output_text_dir / f"{base_filename}_ground_truth_form.json"
        with open(form_path, "w", encoding="utf-8") as fp:
            json.dump(gt_form, fp, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print(f"✅ HOÀN THÀNH XUẤT SẮC TRONG {exec_time:.2f} GIÂY!")
    print(f"   📁 File docs:              {docs_path}")
    print(f"   📁 File markdown:          {md_path}")
    print(f"   📁 File profile:           {json_path}")
    if form_path:
        print(f"   📁 File ground truth form: {form_path}")
    print(f"   💬 Tổng số lượt thoại: {total_turns} lượt")
    print("="*80 + "\n")

    return {
        "success": True,
        "disease_stt": disease_stt,
        "scenario_index": scenario_index,
        "disease_name": disease_name,
        "total_turns": total_turns,
        "execution_time_seconds": round(exec_time, 2),
        "docs_path": str(docs_path),
        "markdown_path": str(md_path),
        "profile_path": str(json_path),
        "form_path": str(form_path) if form_path else None,
        "patient": pat_profile,
        "doctor": doc_profile
    }

def main():
    parser = argparse.ArgumentParser(description="Chạy Pipeline VietMed E2E sinh Profile, Fog of War và Kịch bản hội thoại.")
    parser.add_argument("--stt", type=int, default=1, help="Số thứ tự bệnh trong danh sách 60 bệnh (1-60). Mặc định: 1")
    parser.add_argument("--kb", "--scenario", type=int, default=1, dest="scenario", help="Chỉ số kịch bản lâm sàng (1-10). Mặc định: 1")
    parser.add_argument("--duration", type=int, default=12, help="Thời lượng buổi khám giả định (phút). Mặc định: 12")
    parser.add_argument("--target_turns", "--target-turns", "--turns", type=int, default=28, dest="target_turns", help="Số lượt thoại mục tiêu (28 - 60 lượt). Mặc định: 28")

    parser.add_argument("--sentiment", type=str, default="Positive", choices=["Positive", "Negative"], help="Tâm lý bệnh nhân. Mặc định: Positive")
    parser.add_argument("--force-prior-visit", action="store_true", default=False, help="Ép buộc bệnh nhân có lịch sử đi khám BV/PK trước đó (không null).")
    parser.add_argument("--no-prior-visit", action="store_true", default=False, help="Ép buộc bệnh nhân chưa từng đi khám ở đâu (null).")
    parser.add_argument("--force-confirm-identity", action="store_true", default=False, help="Ép buộc Bác sĩ hỏi xác nhận lại họ tên và tuổi lúc đầu.")
    parser.add_argument("--no-confirm-identity", action="store_true", default=False, help="Ép buộc Bác sĩ vào thẳng lý do khám không hỏi lại thông tin hành chính.")
    parser.add_argument("--model", type=str, default=None, help=f"Tên LLM model trên OpenRouter. Mặc định: {DEFAULT_MODEL}")
    parser.add_argument("--provider", type=str, default=None, choices=["openrouter", "gemini"], help="Provider LLM. Mặc định: openrouter")

    args = parser.parse_args()

    force_prior = None
    if args.force_prior_visit:
        force_prior = True
    elif args.no_prior_visit:
        force_prior = False

    force_confirm = None
    if args.force_confirm_identity:
        force_confirm = True
    elif args.no_confirm_identity:
        force_confirm = False

    run_e2e_simulation(
        disease_stt=args.stt,
        scenario_index=args.scenario,
        duration_minutes=args.duration,
        target_turns=args.target_turns,
        sentiment=args.sentiment,
        force_prior_visit=force_prior,
        force_confirm_identity=force_confirm,
        model_name=args.model,
        llm_provider=args.provider
    )

if __name__ == "__main__":
    main()
