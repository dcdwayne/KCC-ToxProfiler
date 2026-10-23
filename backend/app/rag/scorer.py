# KCC 算分器設計
"""
算分器只會讀取表九中 is_selected == True（專家精鍊後保留）的文獻，且輸出的 JSON 結構已完全對齊你前端 MetaDashboard.vue 的欄位（id, title, evidence, statusText, score）：

1.單篇文獻加權分 (paper_score)：
Paper Score = Base Score (人10 / 動物7 / 細胞3)*期刊級別權重 (Q1: 1.2, Q2: 1.0...)*重排相關度加成

2.單一 KCC 機轉分數 (0 ~ 100%)：
將該 KCC 下所有保留文獻的加權分加總，換算為百分比（達標基準值設為 65.0 分即滿分 100%），並自動分級為 High (STRONG)、Moderate (MODERATE)、Weak (WEAK) 或 Inadequate (INADEQUATE)。

3.總體危害分數 (Hazard Score: 0 ~ 100)：
在毒理學中，強致癌物通常由數個核心機轉強力驅動，因此採 「前 5 高分核心 KCC 平均值佔 70% + 全 10 個 KCC 廣度平均值佔 30%」 計算總分。
"""

# backend/app/rag/scorer.py
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models import Evaluation, EvaluationEvidence, KccQuery

# 期刊 Q1~Q4 權重加成
QUARTILE_WEIGHTS = {
    "Q1": 1.25,
    "Q2": 1.00,
    "Q3": 0.85,
    "Q4": 0.70,
    "Unranked": 0.75
}

# 單一 KCC 滿分(100%)的積分飽和基準值 (約相當於 7~8 篇高品質 Q1 動物/人體實驗文獻)
KCC_SATURATION_BENCHMARK = 65.0


def classify_kcc_level(score: int) -> tuple[str, str]:
    """
    對齊前端 MetaDashboard.vue 的 evidence 與 statusText 欄位格式
    """
    if score >= 75:
        return ("High", "STRONG")
    elif score >= 50:
        return ("Moderate", "MODERATE")
    elif score >= 20:
        return ("Weak", "WEAK")
    else:
        return ("Inadequate", "INADEQUATE")


def calculate_evaluation_scores(db: Session, evaluation_id: int) -> dict:
    """
    根據第九張表 (evaluation_evidence) 中 is_selected=True 的文獻，
    計算 10 個 KCC 的個別分數與總體 Hazard Score，並更新回第十張表 (evaluations)。
    """
    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj:
        raise ValueError(f"找不到 Evaluation ID: {evaluation_id}")

    # 1. 取得完整的 10 KCC 清單 (確保像 KC 07 這種 0 篇文獻的機轉也會出現在儀表板上)
    kcc_defs = (
        db.query(KccQuery.kcc_id, KccQuery.kcc_title)
        .distinct()
        .order_by(KccQuery.kcc_id)
        .all()
    )

    # 2. 撈出該評估單底下所有被專家勾選保留 (is_selected=True) 的文獻證據
    selected_evidences = (
        db.query(EvaluationEvidence)
        .filter_by(evaluation_id=evaluation_id, is_selected=True)
        .all()
    )

    ev_by_kcc = defaultdict(list)
    for ev in selected_evidences:
        ev_by_kcc[ev.kcc_id].append(ev)

    kcc_scores_list = []

    # 3. 逐一計算 KC 01 ~ KC 10 的分數與證據等級
    for kcc_id, kcc_title in kcc_defs:
        ev_list = ev_by_kcc.get(kcc_id, [])
        raw_weighted_sum = 0.0
        
        model_counts = {"Human": 0, "In Vivo": 0, "In Vitro": 0, "Unknown": 0}
        q1_q2_count = 0

        for ev in ev_list:
            q_weight = QUARTILE_WEIGHTS.get(ev.quartile, 0.75)
            # 結合 Cross-Encoder 重排適配度 (0.6 ~ 1.0 區間加權)
            relevance_factor = 0.6 + (0.4 * float(ev.max_rerank_score))
            
            paper_score = float(ev.base_score) * q_weight * relevance_factor
            raw_weighted_sum += paper_score

            model_counts[ev.model_category] = model_counts.get(ev.model_category, 0) + 1
            if ev.quartile in ("Q1", "Q2"):
                q1_q2_count += 1

        # 轉換為 0 ~ 100 百分比分數
        normalized_score = min(100, round((raw_weighted_sum / KCC_SATURATION_BENCHMARK) * 100)) if ev_list else 0
        evidence_level, status_text = classify_kcc_level(normalized_score)

        kcc_scores_list.append({
            "id": kcc_id,
            "title": kcc_title,
            "evidence": evidence_level,      # High / Moderate / Weak / Inadequate
            "statusText": status_text,       # STRONG / MODERATE / WEAK / INADEQUATE
            "score": normalized_score,       # 0 ~ 100
            "paper_count": len(ev_list),
            "model_breakdown": model_counts,
            "high_impact_papers": q1_q2_count
        })

    # 4. 計算總體危害分數 (Hazard Score: 0 ~ 100)
    all_scores = sorted([k["score"] for k in kcc_scores_list], reverse=True)
    if all_scores:
        top5_avg = sum(all_scores[:5]) / min(5, len(all_scores))
        overall_avg = sum(all_scores) / len(all_scores)
        hazard_score = min(100, round(0.7 * top5_avg + 0.3 * overall_avg))
    else:
        hazard_score = 0

    if hazard_score >= 70:
        risk_level = "HIGH RISK"
    elif hazard_score >= 40:
        risk_level = "MODERATE RISK"
    else:
        risk_level = "LOW RISK"

    # 5. 更新回【第十張表：evaluations】
    eval_obj.hazard_score = hazard_score
    eval_obj.risk_level = risk_level
    eval_obj.kcc_scores = kcc_scores_list
    db.commit()
    db.refresh(eval_obj)

    return {
        "evaluation_id": eval_obj.id,
        "chemical_name": eval_obj.chemical_name,
        "cas_number": eval_obj.cas_number,
        "hazard_score": hazard_score,
        "risk_level": risk_level,
        "kcc_scores": kcc_scores_list
    }