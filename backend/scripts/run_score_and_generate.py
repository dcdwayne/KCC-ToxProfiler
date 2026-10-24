# backend/scripts/run_score_and_generate.py
"""
現在我們可以把剛剛建立的 Evaluation ID = 1 直接拿來跑算分與生成報告！
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.rag.scorer import calculate_evaluation_scores
from app.rag.generator import generate_public_report, generate_expert_report

# 指定要計算並生成報告的評估單 ID (對應剛才產生的 ID=1)
TARGET_EVALUATION_ID = 1

def main():
    db = SessionLocal()
    try:
        print(f"🧮 [步驟 1/3] 正在計算評估單 #{TARGET_EVALUATION_ID} 的 10 KCC 分數與總危害分數...")
        score_res = calculate_evaluation_scores(db, TARGET_EVALUATION_ID)
        
        print(f"\n📊 算分完成！目標：{score_res['chemical_name']} | 總體危害分數：{score_res['hazard_score']} ({score_res['risk_level']})")
        print("-" * 65)
        for k in score_res["kcc_scores"]:
            print(f"  KC {k['id']} ({k['title']:<26}): {k['score']:>3}% | {k['evidence']:<10} | 文獻數: {k['paper_count']} 篇")
        print("-" * 65)

        print(f"\n✍️ [步驟 2/3] 正在先生成【民眾版】報告 (每個 KCC 取前 1 篇代表文獻)...")
        public_text = generate_public_report(db, TARGET_EVALUATION_ID)
        print("\n================ 【民眾版本報告預覽】 ================")
        print(public_text[:600] + "\n...(完整內容已存入表十 evaluations.public_report)...\n")

        print(f"\n✍️ [步驟 3/3] 正在接著生成【專家版】報告 (每個 KCC 取前 3 篇代表文獻)...")
        expert_text = generate_expert_report(db, TARGET_EVALUATION_ID)
        print("\n================ 【專家版本報告預覽】 ================")
        print(expert_text[:800] + "\n...(完整內容已存入表十 evaluations.expert_report)...\n")

        print(f"🎉 評估單 #{TARGET_EVALUATION_ID} 雙版本報告皆已生成完畢！")

    finally:
        db.close()

if __name__ == "__main__":
    main()