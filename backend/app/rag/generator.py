# LLM 報告生成器設計
"""
這支生成器會把算分器算出來的 10 KCC 結構化數據 與 表九中專家保留的文獻切片 (matched_chunks) + PMID 組合成嚴謹的 RAG Context，並分別根據你指定的「民眾版 3 大重點」與「專家版 4 大重點（含 MoE、Critical effects、10 KCC 證據強弱區分與 PMID 引用、危害分數）」生成報告。
"""
# backend/app/rag/generator.py
import os
import time  # 👈 1. 新增 import time
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from google import genai
from google.genai.errors import APIError  # 👈 2. 引入 APIError 以捕捉 503/429

from app.models import Evaluation, EvaluationEvidence, Paper, PaperChunk, PaperAuthor

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =====================================================================
# 👇👇👇 【多模型自動備援清單 (Fallback Models)】 👇👇👇
# 系統會優先使用清單中的第 1 個模型；當遇到 429 (每日免費額度 20 次用完) 或 503 塞車時，
# 會自動無縫切換至下一個模型繼續生成報告，確保 DEMO 與測試永不中斷！
# =====================================================================
# 依據帳號實際可用模型排列之免費額度備援清單 (由高品質至高額度 Lite 依序遞補)
FALLBACK_MODELS = [
    # --- 第一梯隊：高階旗艦 Flash (各擁獨立每日免費額度，寫作與毒理分析品質最佳) ---
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    # --- 第二梯隊：Omni 分支模型 ---
    "gemini-omni-1.1-flash",
    # --- 第三梯隊：高速輕量 Lite 模型 (免費額度最高、速度最快，確保 DEMO 永不斷線) ---
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
]

# 讓原有的 LLM_MODEL 變數直接指向備援清單，向下相容無須改動下方函式呼叫
LLM_MODEL = FALLBACK_MODELS

# =====================================================================
# 👇👇👇 【各版本輸入 LLM 的文獻篇數調整區】可在此自由調整每個 KCC 要放入幾篇文獻 👇👇👇
# - PUBLIC_MAX_PAPERS_PER_KCC: 民眾版每個 KCC 最多放入幾篇文獻 (預設 3 篇，加速科普報告生成)
# - EXPERT_MAX_PAPERS_PER_KCC: 專家版每個 KCC 最多放入幾篇文獻 (預設 5 篇)
# =====================================================================
PUBLIC_MAX_PAPERS_PER_KCC = 3
EXPERT_MAX_PAPERS_PER_KCC = 5


def _build_rag_evidence_context(
    db: Session,
    evaluation_id: int,
    kcc_scores: list[dict],
    max_papers_per_kcc: int | None = None
) -> str:
    """
    將表九中 is_selected=True 的文獻與命中切片，整理成帶有 APA 7th (FirstAuthor et al., Year) 與 PMID 的文字供 LLM 引用。
    - max_papers_per_kcc: 若傳入整數 (如 3)，則每個 KCC 只取前 3 高分文獻；若為 None，則將所有選定的文獻全部放入！
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

    paper_ids = list({ev.paper_id for ev, _, _ in rows})
    chunk_text_map = {}
    first_author_map = {}

    if paper_ids:
        # 載入切片文字備援
        chunk_rows = (
            db.query(PaperChunk.paper_id, PaperChunk.chunk_index, PaperChunk.chunk_text)
            .filter(PaperChunk.paper_id.in_(paper_ids))
            .all()
        )
        chunk_text_map = {(r.paper_id, r.chunk_index): r.chunk_text for r in chunk_rows}

        # 從【第五張表：paper_authors】載入第一作者姓氏 (author_order == 1)
        author_rows = (
            db.query(PaperAuthor.paper_id, PaperAuthor.last_name, PaperAuthor.fore_name)
            .filter(PaperAuthor.paper_id.in_(paper_ids), PaperAuthor.author_order == 1)
            .all()
        )
        for pid, last_name, fore_name in author_rows:
            first_author_map[pid] = last_name or fore_name or "Anonymous"

    grouped = defaultdict(list)
    for ev, title, pub_year in rows:
        author_last = first_author_map.get(ev.paper_id, "Author")
        year_str = str(pub_year) if pub_year else "n.d."
        apa_cite = f"{author_last} et al., {year_str}"

        top_chunks = ev.matched_chunks[:2] if ev.matched_chunks else []
        snippet_parts = []
        for c in top_chunks:
            c_text = c.get("chunk_text") or chunk_text_map.get((ev.paper_id, c["chunk_index"]), "")
            snippet_parts.append(f"({c['query_code']}) {c_text}")

        snippets = " | ".join(snippet_parts)
        grouped[ev.kcc_id].append(
            f"  - [Citation: ({apa_cite}) | PMID: {ev.pmid}] (Model: {ev.model_category}, Journal: {ev.quartile}, Score: {ev.base_score}) "
            f"Title: {title}\n    Matched Evidence: {snippets}"
        )

    context_lines = []
    for kcc in kcc_scores:
        kid = kcc["id"]
        context_lines.append(
            f"### KC {kid}: {kcc['title']} | 系統算分: {kcc['score']}% | 證據等級: {kcc['evidence']} ({kcc['statusText']}) | "
            f"納入文獻數: {kcc['paper_count']} 篇 (High Impact Q1/Q2: {kcc.get('high_impact_papers', 0)} 篇 | "
            f"Human: {kcc['model_breakdown'].get('Human', 0)}, In Vivo: {kcc['model_breakdown'].get('In Vivo', 0)}, In Vitro: {kcc['model_breakdown'].get('In Vitro', 0)})"
        )
        if grouped[kid]:
            # 根據 max_papers_per_kcc 決定放入幾篇文獻 (None 代表全部放入)
            selected_group = grouped[kid][:max_papers_per_kcc] if max_papers_per_kcc is not None else grouped[kid]
            context_lines.extend(selected_group)
        else:
            context_lines.append("  - [無符合門檻之文獻證據 (0 papers)]")
        context_lines.append("")

    return "\n".join(context_lines)


def _generate_with_retry(
    client: genai.Client,
    model: str | list[str],
    prompt: str,
    max_retries_per_model: int = 2
) -> str:
    """
    具備「多模型自動切換 (Model Fallback)」與「重試機制」的 LLM 呼叫器：
    1. 若遇到 429 (Quota Exceeded 免費額度用完) 或 404 (模型不支援)，立即秒切下一個備援模型。
    2. 若遇到 503 / 500 (伺服器暫時忙碌)，短暫重試後若仍塞車，同樣自動切換下一個備援模型。
    """
    model_list = [model] if isinstance(model, str) else model
    last_error = None

    for current_model in model_list:
        for attempt in range(1, max_retries_per_model + 1):
            try:
                print(f"   📡 嘗試使用模型 [{current_model}] 生成報告 (第 {attempt} 次)...")
                resp = client.models.generate_content(
                    model=current_model,
                    contents=prompt
                )
                print(f"   ✨ 模型 [{current_model}] 生成成功！")
                return resp.text

            except APIError as e:
                last_error = e
                err_msg = str(e)

                # 429 (該模型今日免費額度已滿) 或 404 -> 不等待，直接換下一個模型！
                if e.code in (429, 404) or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"   ⚠️ 模型 [{current_model}] 今日免費額度已滿或無法使用 (HTTP {e.code})，立即切換下一個模型...")
                    break

                # 503 / 500 伺服器尖峰塞車 -> 等待 3 秒重試一次，若還是塞車就換下一個模型
                if e.code in (503, 500) and attempt < max_retries_per_model:
                    wait_sec = 3 * attempt
                    print(f"   ⏳ 模型 [{current_model}] 伺服器忙碌中 (HTTP {e.code})，等待 {wait_sec} 秒後重試...")
                    time.sleep(wait_sec)
                else:
                    print(f"   ⚠️ 模型 [{current_model}] 伺服器持續忙碌，自動切換下一個模型...")
                    break

    raise last_error


# =========================================================================
# 獨立函式 1：先產生【民眾版本報告 (Public Report)】並立即寫入資料庫解鎖按鈕
# =========================================================================
def generate_public_report(db: Session, evaluation_id: int) -> str:
    """
    單獨生成「民眾版本 (public_report)」：
    每個 KCC 預設僅取前 PUBLIC_MAX_PAPERS_PER_KCC (3) 篇文獻，生成完畢後立即 Commit 至資料庫，
    讓前端『民眾版本』按鈕率先解鎖，無須等待專家版！
    """
    if not GEMINI_API_KEY:
        raise ValueError("❌ 找不到 GEMINI_API_KEY！請於根目錄 .env 檔案中設定。")

    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj or not eval_obj.kcc_scores:
        raise ValueError(f"請先對 Evaluation ID {evaluation_id} 執行 calculate_evaluation_scores 算分！")

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 民眾版使用精簡版文獻池 (每個 KCC 取前 PUBLIC_MAX_PAPERS_PER_KCC 篇)
    public_evidence_context = _build_rag_evidence_context(
        db,
        evaluation_id,
        eval_obj.kcc_scores,
        max_papers_per_kcc=PUBLIC_MAX_PAPERS_PER_KCC
    )

    public_prompt = f"""
你是一位專業且善於科普溝通的毒理學與公共衛生專家。請根據以下針對化學物質「{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})」的系統性文獻回顧數據，撰寫一份給一般民眾閱讀的【大眾版風險評估報告】（使用繁體中文，語氣清晰易懂，支援 Markdown 格式）。

【本次系統計算結果】
- 目標化學物質：{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})
- 總體危害分數 (Hazard Score)：{eval_obj.hazard_score} / 100 ({eval_obj.risk_level})

【10 大致癌關鍵特徵 (10 KCCs) 檢索摘要（每個機轉取代表性前 {PUBLIC_MAX_PAPERS_PER_KCC} 篇）】
{public_evidence_context}

請嚴格依照以下三個結構撰寫（必須使用 Markdown 標題 `### 1.`、`### 2.`、`### 3.`，以便前端切分標籤頁）：
### 1. 化學物質介紹
以淺顯易懂的語言介紹「{eval_obj.chemical_name}」是什麼、它的基本特性，以及在日常生活或環境中常見於哪些地方（例如：特定飲食加工、空氣污染、消費品或工業環境）。

### 2. 主要暴露途徑
說明一般民眾或工作者主要會透過哪些途徑接觸到該物質（如：飲食攝入、吸入空氣微粒、皮膚接觸等），並條列具體的日常減毒預防行動。

### 3. 10 個關鍵致癌機轉 (KCC) 分析結論與危害分數說明
- 用白話文總結本次 AI 系統分析科學文獻後的發現（例如它如何透過破壞 DNA、引發氧化壓力等機轉對人體造成威脅）。
- 清楚說明最終得出的 **危害分數 {eval_obj.hazard_score}/100 ({eval_obj.risk_level})** 代表什麼健康風險意義與總結建議。
"""

    print(f"🤖 [1/2] 正在呼叫 LLM 生成【民眾版本報告 (每個 KCC 取最多 {PUBLIC_MAX_PAPERS_PER_KCC} 篇文獻)】...")
    public_report_text = _generate_with_retry(client, LLM_MODEL, public_prompt)

    # 立即寫入資料庫並 Commit，讓前端輪詢馬上偵測到民眾版已完成！
    eval_obj.public_report = public_report_text
    eval_obj.status = "GENERATING_EXPERT"
    db.commit()
    db.refresh(eval_obj)
    print("   ✅ 【民眾版本報告】已生成並寫入資料庫！前端按鈕已可解鎖。")

    return public_report_text


# =========================================================================
# 獨立函式 2：接著產生【專家版本報告 (Expert Report)】(納入每個 KCC 的 5 篇選定文獻)
# =========================================================================
def generate_expert_report(db: Session, evaluation_id: int) -> str:
    """
    單獨生成「專家版本 (expert_report)」：
    將專家精鍊後保留 (is_selected=True) 納入每個 KCC 的 5 篇選定文獻放入 Prompt，生成完畢後更新狀態為 COMPLETED。
    """
    if not GEMINI_API_KEY:
        raise ValueError("❌ 找不到 GEMINI_API_KEY！請於根目錄 .env 檔案中設定。")

    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj or not eval_obj.kcc_scores:
        raise ValueError(f"請先對 Evaluation ID {evaluation_id} 執行 calculate_evaluation_scores 算分！")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # 專家版放入 5 篇選定文獻 (EXPERT_MAX_PAPERS_PER_KCC = 5)
    expert_evidence_context = _build_rag_evidence_context(
        db,
        evaluation_id,
        eval_obj.kcc_scores,
        max_papers_per_kcc=EXPERT_MAX_PAPERS_PER_KCC
    )

    expert_prompt = f"""
你是一位資深法規毒理學家（Regulatory Toxicologist），專精於 IARC 10 Key Characteristics of Carcinogens (10 KCCs) 與風險評估。
請根據以下經由 RAG 檢索、Cross-Encoder 重排與專家篩選後的實證文獻池（Evidence Pool），為「{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})」撰寫一份嚴謹的【專家版毒理學統合分析報告】（使用專業繁體中文，專有名詞附註英文，支援 Markdown 格式）。

【文獻引用格式嚴格規定】
在內文中引用任何文獻時，請統一標註 `(PMID: xxxxxxxx)`（若同時引用多篇可寫 `(PMID: 11111111, PMID: 22222222)`），系統後端會自動將其轉換為 APA 7th `(Author et al., Year)` 並綁定 PMID 懸浮視窗。

【量化評估數據】
- 評估目標：{eval_obj.chemical_name} (CAS: {eval_obj.cas_number})
- 總體危害分數 (Hazard Score)：{eval_obj.hazard_score} / 100 ({eval_obj.risk_level})
- 分數定義標準：75~100% 為 Strong/High Evidence (證據明確)；50~74% 為 Moderate Evidence (中等證據)；20~49% 為 Weak Evidence (證據薄弱)；0~19% 為 Inadequate Evidence (證據不足)。

【實證文獻池明細 (10 KCCs Evidence Pool 每個機轉取代表性前 {EXPERT_MAX_PAPERS_PER_KCC} 篇）】
{expert_evidence_context}

請嚴格依照以下四個核心章節撰寫報告（必須使用 Markdown 標題 `### 1.`、`### 2.`、`### 3.`、`### 4.`，以便前端切分標籤頁）：

### 1. Margin of Exposure (MoE) 與劑量效應評估
- 綜合文獻中的實驗模型分佈與暴露條件，評估該物質的暴露邊際（Margin of Exposure, MoE）與劑量效應關係（Dose-Response / Biological Gradient）。
- 若檢索到的基因毒性與致癌機轉極強，請以法規毒理角度探討其「無閾值（Non-threshold）」特性對 MoE 評估與風險管理的意義，並指出現有摘要文獻資料庫的評估限制。

### 2. Critical Effects (關鍵毒理與臨界效應)
- 歸納「{eval_obj.chemical_name}」最關鍵的生物學臨界效應（Critical Effects）、主要靶器官與核心致病途徑（Mode of Action / Adverse Outcome Pathway），引用具體文獻並標註 `(PMID: xxxxxxxx)`。

### 3. 10 個關鍵致癌機轉 (10 KCCs) 分析成果詳解
請將 10 個 KCC 分為兩大區塊進行深度剖析：
- **(A) 證據明確之機轉 (Strong & Moderate Evidence)**：針對分數較高的 KCC，逐一說明其具體分子機轉、實驗模型支撐度，並標註對應的 `(PMID: xxxxxxxx)`。
- **(B) 證據不足或尚待釐清之機轉 (Weak & Inadequate Evidence)**：明確列出分數偏低或文獻數為 0 的 KCC，探討科學知識缺口（Data Gaps），並具體建議未來應補充哪類型的毒理實驗。

### 4. 綜合危害分數 (Hazard Score) 與證據權重結論
- 總結為何該化學物質獲得 **{eval_obj.hazard_score} / 100 ({eval_obj.risk_level})** 的危害分數，交代主要得分來源與證據權重（Weight of Evidence, WoE）最終定論。
"""

    print(f"🧬 [2/2] 正在呼叫 LLM 生成【專家版本報告 (每個 KCC 取最多 {EXPERT_MAX_PAPERS_PER_KCC} 篇文獻)】...")
    expert_report_text = _generate_with_retry(client, LLM_MODEL, expert_prompt)

    # 寫入資料庫並將狀態改為 COMPLETED
    eval_obj.expert_report = expert_report_text
    eval_obj.status = "COMPLETED"
    db.commit()
    db.refresh(eval_obj)
    print("   ✅ 【專家版本報告】已生成並寫入資料庫！全數報告皆已完成。")

    return expert_report_text


def generate_evaluation_reports(db: Session, evaluation_id: int) -> dict:
    """
    依序執行「1. 民眾版本 (先跑並先存檔)」與「2. 專家版本 (後跑並存檔)」。
    """
    public_text = generate_public_report(db, evaluation_id)
    expert_text = generate_expert_report(db, evaluation_id)

    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    return {
        "evaluation_id": evaluation_id,
        "status": eval_obj.status if eval_obj else "COMPLETED",
        "hazard_score": eval_obj.hazard_score if eval_obj else None,
        "public_report": public_text,
        "expert_report": expert_text
    }