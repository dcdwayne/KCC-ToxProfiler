# LLM 報告生成器設計
"""
這支生成器會把算分器算出來的 10 KCC 結構化數據 與 表九中專家保留的文獻切片 (matched_chunks) + PMID 組合成嚴謹的 RAG Context，並分別根據你指定的「民眾版 3 大重點」與「專家版 4 大重點（含 MoE、Critical effects、10 KCC 證據強弱區分與 PMID 引用、危害分數）」生成報告。
"""
# backend/app/rag/generator.py
import os
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from google import genai

from app.models import Evaluation, EvaluationEvidence, Paper

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = "gemini-3.8-flash"


def _build_rag_evidence_context(db: Session, evaluation_id: int, kcc_scores: list[dict]) -> str:
    """
    將表九中 is_selected=True 的文獻與命中切片，整理成帶有 PMID 與實驗模型的結構化文字，供 LLM 引用。
    """
    rows = (
        db.query(EvaluationEvidence, Paper.article_title, Paper.pub_year)
        .join(Paper, EvaluationEvidence.paper_id == Paper.id)
        .filter(
            EvaluationEvidence.evaluation_id == evaluation_id,
            EvaluationEvidence.is_selected == True
        )
        .order_by(EvaluationEvidence.kcc_id, EvaluationEvidence.max_rerank_score.desc())
        .all()
    )

    grouped = defaultdict(list)
    for ev, title, pub_year in rows:
        # 取該論文在此 KCC 最具代表性的前 2 個命中片段
        top_chunks = ev.matched_chunks[:2] if ev.matched_chunks else []
        snippets = " | ".join([f"({c['query_code']}) {c['chunk_text']}" for c in top_chunks])
        grouped[ev.kcc_id].append(
            f"  - [PMID: {ev.pmid}] ({pub_year}, Model: {ev.model_category}, Journal: {ev.quartile}, Score: {ev.base_score}) "
            f"Title: {title}\n    Matched Evidence: {snippets}"
        )

    context_lines = []
    for kcc in kcc_scores:
        kid = kcc["id"]
        context_lines.append(
            f"### KC {kid}: {kcc['title']} | 系統算分: {kcc['score']}% | 證據等級: {kcc['evidence']} ({kcc['statusText']}) | "
            f"納入文獻數: {kcc['paper_count']} 篇 (Human: {kcc['model_breakdown'].get('Human', 0)}, "
            f"In Vivo: {kcc['model_breakdown'].get('In Vivo', 0)}, In Vitro: {kcc['model_breakdown'].get('In Vitro', 0)})"
        )
        if grouped[kid]:
            # 每個 KCC 提供前 5 篇最高分文獻細節給 LLM，避免 Context 過長同時確保引用精準
            context_lines.extend(grouped[kid][:5])
        else:
            context_lines.append("  - [無符合門檻之文獻證據 (0 papers)]")
        context_lines.append("")

    return "\n".join(context_lines)


def generate_evaluation_reports(db: Session, evaluation_id: int) -> dict:
    """
    生成「民眾版本 (public_report)」與「專家版本 (expert_report)」，並更新至第十張表 (evaluations)。
    """
    if not GEMINI_API_KEY:
        raise ValueError("❌ 找不到 GEMINI_API_KEY！請於根目錄 .env 檔案中設定。")

    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj or not eval_obj.kcc_scores:
        raise ValueError(f"請先對 Evaluation ID {evaluation_id} 執行 calculate_evaluation_scores 算分！")

    client = genai.Client(api_key=GEMINI_API_KEY)
    evidence_context = _build_rag_evidence_context(db, evaluation_id, eval_obj.kcc_scores)

    # =========================================================================
    # 1. 產生【民眾版本報告 (Public Report)】
    # =========================================================================
    public_prompt = f"""
你是一位專業且善於科普溝通的毒理學與公共衛生專家。請根據以下針對化學物質「{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})」的系統性文獻回顧數據，撰寫一份給一般民眾閱讀的【大眾版風險評估報告】（使用繁體中文，語氣清晰易懂，支援 Markdown 格式）。

【本次系統計算結果】
- 目標化學物質：{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})
- 總體危害分數 (Hazard Score)：{eval_obj.hazard_score} / 100 ({eval_obj.risk_level})

【10 大致癌關鍵特徵 (10 KCCs) 檢索摘要】
{evidence_context}

請嚴格依照以下三個結構撰寫（使用 Markdown 標題 `###`）：
### 1. 化學物質介紹
以淺顯易懂的語言介紹「{eval_obj.chemical_name}」是什麼、它的基本特性，以及在日常生活或環境中常見於哪些地方（例如：特定飲食加工、空氣污染、消費品或工業環境）。

### 2. 主要暴露途徑
說明一般民眾或工作者主要會透過哪些途徑接觸到該物質（如：飲食攝入、吸入空氣微粒、皮膚接觸等），並簡述如何減少日常暴露。

### 3. 10 個關鍵致癌機轉 (KCC) 分析結論與危害分數說明
- 用白話文總結本次 AI 系統分析科學文獻後的發現（例如：科學證據顯示它最主要會透過「破壞 DNA（基因毒性）」、「引發細胞氧化壓力」等哪幾個機轉對人體造成威脅）。
- 清楚說明最終得出的 **危害分數 {eval_obj.hazard_score}/100 ({eval_obj.risk_level})** 代表什麼健康風險意義。
"""

    print("🤖 正在呼叫 LLM 生成【民眾版本報告 (Public Report)】...")
    public_resp = client.models.generate_content(
        model=LLM_MODEL,
        contents=public_prompt
    )
    public_report_text = public_resp.text

    # =========================================================================
    # 2. 產生【專家版本報告 (Expert Report)】
    # =========================================================================
    expert_prompt = f"""
你是一位資深法規毒理學家（Regulatory Toxicologist），專精於 IARC 10 Key Characteristics of Carcinogens (10 KCCs) 與風險評估。
請根據以下經由 RAG 檢索、Cross-Encoder 重排與專家篩選後的實證文獻池（Evidence Pool），為「{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})」撰寫一份嚴謹的【專家版毒理學統合分析報告】（使用專業繁體中文，專有名詞附註英文，並必須在內文中明確標註參考文獻的 `(PMID: xxxxxxxx)`，支援 Markdown 格式）。

【量化評估數據】
- 評估目標：{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})
- 總體危害分數 (Hazard Score)：{eval_obj.hazard_score} / 100 ({eval_obj.risk_level})
- 分數定義標準：75~100% 為 Strong/High Evidence (證據明確)；50~74% 為 Moderate Evidence (中等證據)；20~49% 為 Weak Evidence (證據薄弱)；0~19% 為 Inadequate Evidence (證據不足)。

【實證文獻池明細 (10 KCCs Evidence Pool)】
{evidence_context}

請嚴格依照以下四個核心章節撰寫報告（使用 Markdown 標題 `###`）：

### 1. Margin of Exposure (MoE) 與劑量效應評估
- 綜合文獻中的實驗模型分佈（Human Epidemiological、In Vivo 動物模型、In Vitro 細胞模型）與暴露條件，評估該物質的暴露邊際（Margin of Exposure, MoE）與劑量效應關係（Dose-Response / Biological Gradient）。
- 若檢索到的基因毒性與致癌機轉極強（如形成共價 DNA 加合物），請以法規毒理角度探討其「無閾值（Non-threshold）」特性對 MoE 評估與風險管理的意義，並指出目前摘要文獻中若缺乏精確 BMDL10 / 人體暴露量數據時的評估限制。

### 2. Critical Effects (關鍵毒理與臨界效應)
- 歸納「{eval_obj.chemical_name}」最關鍵的生物學臨界效應（Critical Effects）、主要靶器官與核心致病途徑（Mode of Action / Adverse Outcome Pathway），引用具體的文獻發現與 PMID 加以佐證。

### 3. 10 個關鍵致癌機轉 (10 KCCs) 分析成果詳解
請將 10 個 KCC 分為兩大區塊進行深度剖析：
- **(A) 證據明確之機轉 (Strong & Moderate Evidence)**：針對分數較高的 KCC，逐一說明其具體分子機轉（例如代謝活化酵素 CYP450、DNA adducts、ROS 誘導等）、實驗模型支撐度（Human/In Vivo/In Vitro 篇數），並**必須在敘述後標註對應的 `(PMID: xxxxxxxx)`**。
- **(B) 證據不足或尚待釐清之機轉 (Weak & Inadequate Evidence)**：明確列出分數偏低或文獻數為 0 的 KCC（例如本次檢索中證據缺乏的項目），探討目前的科學知識缺口（Data Gaps），並具體建議未來應補充哪類型的體內或體外毒理實驗。

### 4. 綜合危害分數 (Hazard Score) 與證據權重結論
- 總結為何該化學物質獲得 **{eval_obj.hazard_score} / 100 ({eval_obj.risk_level})** 的危害分數，交代主要得分來源與證據權重（Weight of Evidence, WoE）最終定論。
"""

    print("🧬 正在呼叫 LLM 生成【專家版本報告 (Expert Report)】...")
    expert_resp = client.models.generate_content(
        model=LLM_MODEL,
        contents=expert_prompt
    )
    expert_report_text = expert_resp.text

    # 3. 將生成完畢的報告寫入【第十張表：evaluations】並將狀態改為 COMPLETED
    eval_obj.public_report = public_report_text
    eval_obj.expert_report = expert_report_text
    eval_obj.status = "COMPLETED"
    db.commit()
    db.refresh(eval_obj)

    return {
        "evaluation_id": eval_obj.id,
        "status": eval_obj.status,
        "hazard_score": eval_obj.hazard_score,
        "public_report": public_report_text,
        "expert_report": expert_report_text
    }