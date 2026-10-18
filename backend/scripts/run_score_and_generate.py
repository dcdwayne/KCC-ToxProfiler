# backend/scripts/run_score_and_generate.py
"""
現在我們可以把剛剛建立的 Evaluation ID = 1 直接拿來跑算分與生成報告！
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.rag.scorer import calculate_evaluation_scores
from app.rag.generator import generate_evaluation_reports

# 指定要計算並生成報告的評估單 ID (對應剛才產生的 ID=1)
TARGET_EVALUATION_ID = 1

def main():
    db = SessionLocal()
    try:
        print(f"🧮 [步驟 1/2] 正在計算評估單 #{TARGET_EVALUATION_ID} 的 10 KCC 分數與總危害分數...")
        score_res = calculate_evaluation_scores(db, TARGET_EVALUATION_ID)
        
        print(f"\n📊 算分完成！目標：{score_res['chemical_name']} | 總體危害分數：{score_res['hazard_score']} ({score_res['risk_level']})")
        print("-" * 65)
        for k in score_res["kcc_scores"]:
            print(f"  KC {k['id']} ({k['title']:<26}): {k['score']:>3}% | {k['evidence']:<10} | 文獻數: {k['paper_count']} 篇")
        print("-" * 65)

        print(f"\n✍️ [步驟 2/2] 正在根據證據池與分數生成【民眾版】與【專家版】報告...")
        report_res = generate_evaluation_reports(db, TARGET_EVALUATION_ID)

        print("\n================ 【民眾版本報告預覽】 ================")
        print(report_res["public_report"][:600] + "\n...(完整內容已存入表十 evaluations.public_report)...\n")

        print("================ 【專家版本報告預覽】 ================")
        print(report_res["expert_report"][:800] + "\n...(完整內容已存入表十 evaluations.expert_report)...\n")

        print(f"🎉 評估單 #{TARGET_EVALUATION_ID} 狀態已更新為 [{report_res['status']}]！十張表全流程數據皆已就緒！")

    finally:
        db.close()

if __name__ == "__main__":
    main()