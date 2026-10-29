# backend/app/routers/chat.py
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.database import SessionLocal
from app.mcp_server import get_selected_chemicals, get_chemical_evaluation_data
from app.rag.generator import GEMINI_API_KEY, FALLBACK_MODELS
from app.routers.meta import _build_pmid_to_apa_map, _split_markdown_into_tabs

router = APIRouter(prefix="/api/chat", tags=["Dr. Manhattan AI Advisor"])

# 自動讀取 plugin/skills/tox-advisor/SKILL.md 作為 Dr. Manhattan 的核心規範
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SKILL_FILE_PATH = ROOT_DIR / "plugin" / "skills" / "tox-advisor" / "SKILL.md"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _load_skill_instruction() -> str:
    if SKILL_FILE_PATH.exists():
        return SKILL_FILE_PATH.read_text(encoding="utf-8")
    return "你是 Dr. Manhattan，KCC ToxProfiler 的毒理學危害辨識 AI 助手，僅能依據評估報告內容回答問題。"


def _format_chat_reply_to_html(md_text: str, pmid_map: dict, is_expert: bool = False) -> str:
    """
    專供 Dr. Manhattan 聊天氣泡使用的獨立 Markdown 轉 HTML 渲染器：
    支援粗體、條列清單、小標題，以及專家版的 (PMID: xxxxxxxx) 轉 APA 7th 懸浮標籤。
    """
    if not md_text:
        return ""

    text = md_text.strip()

    # 若為專家模式，將 (PMID: 12345678) 轉換為帶有 data-pmid 的 APA 7th 互動標籤
    if is_expert and pmid_map:
        def replace_pmid(match):
            full_str = match.group(0)
            pmids = re.findall(r'\d{6,9}', full_str)
            if not pmids:
                return full_str
            badges = []
            for pid in pmids:
                apa_label = pmid_map.get(pid, f"PMID: {pid}")
                badges.append(
                    f'<span class="apa-citation" data-pmid="PMID: {pid}">({apa_label})</span>'
                )
            return '<span class="apa-citation-group">' + "; ".join(badges) + '</span>'

        text = re.sub(r'\((?:PMID:\s*\d{6,9}[,\s;]*)+[\)]', replace_pmid, text)

    # 轉換粗體 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    lines = text.splitlines()
    html_parts = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### ") or stripped.startswith("#### "):
            clean_title = re.sub(r'^#+\s*', '', stripped)
            html_parts.append(f'<h4 class="sub-sec-title">{clean_title}</h4>')
        elif stripped.startswith("- ") or stripped.startswith("* "):
            item_content = stripped[2:].strip()
            html_parts.append(
                f'<div class="bullet-item"><span class="bullet-dot">•</span><span>{item_content}</span></div>'
            )
        elif re.match(r'^\d+\.\s+', stripped):
            m = re.match(r'^(\d+\.)\s+(.*)', stripped)
            html_parts.append(
                f'<div class="num-item"><span class="num-idx">{m.group(1)}</span><span>{m.group(2)}</span></div>'
            )
        else:
            html_parts.append(f'<p class="report-para">{stripped}</p>')

    return "\n".join(html_parts)


def _generate_chat_answer_fast(prompt: str) -> str:
    """
    聊天室專用高速生成器：
    設定單次呼叫 20 秒 Timeout，若單一模型塞車或額度滿，立即秒切下一顆備援模型，不讓使用者乾等！
    """
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=20000)  # 20 秒內無回應立即換下一顆模型
    )
    last_err = None

    for model_name in FALLBACK_MODELS:
        try:
            print(f"💬 [Dr. Manhattan] 嘗試使用模型 [{model_name}] 回答使用者提問...")
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.15)
            )
            if resp and resp.text:
                print(f"   ✅ [Dr. Manhattan] 模型 [{model_name}] 回覆成功！")
                return resp.text
        except APIError as e:
            last_err = e
            print(f"   ⚠️ 模型 [{model_name}] API 受限或忙碌 (HTTP {e.code})，立即切換下一顆...")
            continue
        except Exception as e:
            last_err = e
            print(f"   ⚠️ 模型 [{model_name}] 逾時或發生錯誤 ({e})，立即切換下一顆...")
            continue

    raise RuntimeError(f"所有備援模型皆無法回應：{last_err}")


# =====================================================================
# API 1: 取得目前歷史紀錄中已勾選 (is_selected = True) 的化學物質清單
# =====================================================================
@router.get("/chemicals")
def list_selected_chemicals():
    chemicals = get_selected_chemicals()
    return {
        "count": len(chemicals),
        "chemicals": chemicals
    }


# =====================================================================
# API 2: 選定角色與化學物質後，載入評估摘要與對應的主題卡片清單
# =====================================================================
class SelectChemicalRequest(BaseModel):
    chemical_query: str
    role: str = "一般民眾"


@router.post("/select-chemical")
def select_chemical_for_chat(payload: SelectChemicalRequest):
    data = get_chemical_evaluation_data(payload.chemical_query, payload.role)
    if not data.get("found"):
        raise HTTPException(status_code=404, detail=data.get("message", "找不到該化學物質的勾選紀錄"))

    return {
        "evaluation_id": data["evaluation_id"],
        "chemical_name_zh": data["chemical_name_zh"],
        "chemical_name_en": data["chemical_name_en"],
        "cas_number": data["cas_number"],
        "hazard_score": data["hazard_score"],
        "risk_level": data["risk_level"],
        "role": payload.role,
        "available_topics": data["available_topics"]
    }


# =====================================================================
# API 3: 回答「點擊主題按鈕」或「使用者自由輸入之問題」(含超綱防呆)
# =====================================================================
class ChatAskRequest(BaseModel):
    chemical_query: str
    role: str = "一般民眾"
    question: str
    is_topic_click: bool = False
    topic_index: int | None = None


@router.post("/ask")
def ask_dr_manhattan(payload: ChatAskRequest, db: Session = Depends(get_db)):
    # 1. 透過 FastMCP 工具取得該化學物質被勾選的評估報告與 10 KCC 分數
    mcp_data = get_chemical_evaluation_data(payload.chemical_query, payload.role)
    if not mcp_data.get("found"):
        return {
            "reply_html": f"<p class='report-para'>抱歉，目前知識庫中尚未勾選「{payload.chemical_query}」的評估紀錄，請先至「歷史紀錄」頁面勾選。</p>",
            "available_topics": []
        }

    report_raw = mcp_data.get("report_content", "")
    is_expert = (payload.role == "專家")
    pmid_map = _build_pmid_to_apa_map(db, report_raw) if is_expert else {}

    # 2. 若使用者是點擊「預設主題按鈕」，直接從已生成的報告切出該章節秒回
    if payload.is_topic_click and payload.topic_index is not None:
        tabs = _split_markdown_into_tabs(report_raw, pmid_map, is_expert=is_expert)
        if 0 <= payload.topic_index < len(tabs):
            chosen_tab = tabs[payload.topic_index]
            return {
                "reply_html": chosen_tab["content_html"],
                "chapter_title": chosen_tab["full_title"],
                "available_topics": mcp_data["available_topics"]
            }

    # 3. 若使用者是「自由輸入問題」，結合 SKILL.md 與報告內容呼叫 Gemini
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="未設定 GEMINI_API_KEY")

    skill_rules = _load_skill_instruction()
    chem_zh = mcp_data["chemical_name_zh"]
    chem_en = mcp_data["chemical_name_en"]

    # 整理精簡版 10 KCC 分數摘要，減少多餘 Token 加速回應
    kcc_brief_lines = []
    for k in (mcp_data.get("kcc_scores") or []):
        kcc_brief_lines.append(
            f"- KC {k.get('id')} ({k.get('title')}): 分數 {k.get('score')}% | 證據力: {k.get('evidence')} | 文獻數: {k.get('paper_count')} 篇"
        )
    kcc_summary_text = "\n".join(kcc_brief_lines)

    prompt = f"""
{skill_rules}

【你的身分設定】
你的名字是「Dr. Manhattan」，KCC ToxProfiler 毒理學風險評估智能助理。
目前對話的使用者身分為：【{payload.role}】
目前鎖定查詢的化學物質為：【{chem_zh} ({chem_en}, CAS: {mcp_data['cas_number']})】
總體危害分數：【{mcp_data['hazard_score']} / 100 ({mcp_data['risk_level']})】

【唯一允許引用的 10 KCC 分數與評估報告內容】
{kcc_summary_text}

{report_raw}

【使用者提問】
「{payload.question}」

【回覆嚴格守則】
1. 請完全依據上方【唯一允許引用的 10 KCC 分數與評估報告內容】回答使用者的問題，使用繁體中文（支援條列 `- ` 與加粗 `**文字**`）。
2. 若報告內容有提到相關概念（例如：高溫烹調油炸、食用油污染、飲食暴露途徑等），請直接引用報告內的資訊為使用者清楚解答！
3. 【超綱攔截鐵律】：只有當使用者的問題與「{chem_zh} ({chem_en})」的毒理評估報告完全無關、詢問其他未載入的化學物質、或報告內隻字未提時，請勿使用外部知識回答，必須統一回覆：
「抱歉，您的問題超出目前『{chem_zh} ({chem_en})』危害辨識評估報告的涵蓋範圍，Dr. Manhattan 無法提供回覆。建議您針對本報告涵蓋之暴露途徑、10 KCC 致癌機轉或危害分數進行提問，或點擊下方主題按鈕查閱。」
"""

    raw_answer = _generate_chat_answer_fast(prompt)
    reply_html = _format_chat_reply_to_html(raw_answer, pmid_map, is_expert=is_expert)

    return {
        "reply_html": reply_html,
        "available_topics": mcp_data["available_topics"]
    }