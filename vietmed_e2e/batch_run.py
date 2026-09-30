# -*- coding: utf-8 -*-
"""
vietmed_e2e/batch_run.py
Bộ điều phối chạy hàng loạt (Batch Runner) cho VietMed E2E Pipeline:
- Chạy danh sách các bệnh (mặc định STT 1 đến 10, hoặc danh sách tùy chọn).
- Quản lý tiến trình, đo lường thời gian, ghi log chi tiết.
- Tự động bỏ qua lỗi và tiếp tục các bệnh kế tiếp.
- Xuất báo cáo tổng kết hoàn thành.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

from vietmed_e2e.config import WORKSPACE_ROOT, OUTPUT_600_DIR
from vietmed_e2e.run_e2e import run_e2e_simulation

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_batch(
    disease_stts: List[int],
    scenario_index: int = 1,
    duration_minutes: int = 12,
    target_turns: int = 28,
    model_name: str = None,
    provider: str = None
) -> List[Dict[str, Any]]:
    """
    Thực thi batch simulation tuần tự cho danh sách STT bệnh.
    """
    total = len(disease_stts)
    print("=" * 80)
    print(f"🚀 BẮT ĐẦU CHẠY BATCH E2E CHO {total} BỆNH:")
    print(f"   Danh sách STT: {disease_stts}")
    print(f"   Kịch bản: KB{scenario_index:02d} | Thời lượng mỗi buổi: ~{duration_minutes} phút")
    print("=" * 80 + "\n")

    results = []
    start_all = time.time()

    for idx, stt in enumerate(disease_stts, 1):
        print(f"\n[{idx}/{total}] ----------------------------------------------------")
        print(f"▶ ĐANG XỬ LÝ BỆNH STT {stt:02d} (KB{scenario_index:02d})...")
        t0 = time.time()
        try:
            res = run_e2e_simulation(
                disease_stt=stt,
                scenario_index=scenario_index,
                duration_minutes=duration_minutes,
                target_turns=target_turns,
                model_name=model_name,
                llm_provider=provider
            )
            elapsed = time.time() - t0
            res["status"] = "SUCCESS"
            res["time"] = round(elapsed, 2)
            results.append(res)
            print(f"✔ Hoàn thành STT {stt:02d} trong {elapsed:.1f}s ({res.get('total_turns', 0)} lượt)")
        except Exception as ex:
            elapsed = time.time() - t0
            print(f"❌ LỖI KHI XỬ LÝ STT {stt:02d}: {ex}")
            results.append({
                "disease_stt": stt,
                "scenario_index": scenario_index,
                "status": "FAILED",
                "error": str(ex),
                "time": round(elapsed, 2)
            })

    total_time = time.time() - start_all
    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")

    print("\n" + "=" * 80)
    print(f"🏁 TỔNG KẾT BATCH E2E: {success_count}/{total} THÀNH CÔNG (Tổng thời gian: {total_time/60:.2f} phút)")
    print("-" * 80)
    for r in results:
        status_icon = "✔" if r.get("status") == "SUCCESS" else "❌"
        d_name = r.get("disease_name", f"Bệnh STT {r['disease_stt']}")
        turns = f"{r.get('total_turns', 0)} lượt" if r.get("status") == "SUCCESS" else r.get("error", "Error")
        print(f" {status_icon} STT {r['disease_stt']:02d}: {d_name} - {turns} ({r['time']}s)")
    print("=" * 80 + "\n")

    return results

def main():
    parser = argparse.ArgumentParser(description="Batch Runner cho VietMed E2E Pipeline.")
    parser.add_argument("--stts", type=str, default="1,2,3,4,5,6,7,8,9,10", help="Danh sách STT phân tách bằng dấu phẩy (mặc định: 1,2,3,4,5,6,7,8,9,10)")
    parser.add_argument("--kb", type=int, default=1, help="Kịch bản KB (mặc định: 1)")
    parser.add_argument("--duration", type=int, default=12, help="Thời lượng buổi khám phút (mặc định: 12)")
    parser.add_argument("--target_turns", type=int, default=28, help="Số lượt thoại mục tiêu (mặc định: 28)")
    parser.add_argument("--model", type=str, default=None, help="Tên model LLM")
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider (openrouter/gemini)")

    args = parser.parse_args()
    stt_list = [int(s.strip()) for s in args.stts.split(",") if s.strip().isdigit()]

    run_batch(
        disease_stts=stt_list,
        scenario_index=args.kb,
        duration_minutes=args.duration,
        target_turns=args.target_turns,
        model_name=args.model,
        provider=args.provider
    )

if __name__ == "__main__":
    main()
