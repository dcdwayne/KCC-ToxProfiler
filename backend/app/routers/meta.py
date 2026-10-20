# backend/app/routers/meta.py
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Evaluation, Paper, PaperAuthor
from app.rag.scorer import calculate_evaluation_scores

router = APIRouter(prefix="/api/meta", tags=["Meta-Analysis"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _format_curated_date(dt) -> str:
    if not dt:
        return "2026/10/20"
    return dt.strftime("%Y/%m/%d")


def _build_pmid_to_apa_map(db: Session, text_content: str) -> dict[str, dict]:
    """
    掃描報告內文中所有出現的 PMID，從資料庫查出第一作者姓氏 (LastName) 與發表年份 (pub_year)，
    組成 APA 7th 格式: FirstAuthor et al., Year
    """
    if not text_content:
        return {}

    pmids = list(set(re.findall(r"PMID:\s*(\d+)", text_content)))
    if not pmids:
        return {}

    papers = db.query(Paper.id, Paper.pmid, Paper.pub_year, Paper.journal_title).filter(Paper.pmid.in_(pmids)).all()
    paper_id_map = {p.id: p for p in papers}

    if not paper_id_map:
        return {}

    authors = (
        db.query(PaperAuthor.paper_id, PaperAuthor.last_name, PaperAuthor.fore_name)
        .filter(PaperAuthor.paper_id.in_(list(paper_id_map.keys())), PaperAuthor.author_order == 1)
        .all()
    )
    first_author_by_pid = {a.paper_id: (a.last_name or a.fore_name or "Study") for a in authors}

    pmid_apa_map = {}
    for pid, p_obj in paper_id_map.items():
        author_name = first_author_by_pid.get(pid, "Author")
        year_str = str(p_obj.pub_year) if p_obj.pub_year else "n.d."
        pmid_apa_map[p_obj.pmid] = {
            "apa_text": f"{author_name} et al., {year_str}",
            "pmid": p_obj.pmid,
            "journal": p_obj.journal_title or ""
        }

    return pmid_apa_map


def _convert_citations_to_apa_html(text: str, pmid_map: dict[str, dict]) -> str:
    """
    將報告中的 ` (PMID: 33420596, PMID: 25995008) ` 或 `(PMID: 36509717)`
    轉換為符合 APA 7th 的 `(AuthorA et al., 2021; AuthorB et al., 2015)` 互動式 HTML 標籤，
    當滑鼠 Hover 時顯示原始 PMID！
    """
    # 先移除包在括號外的反引號 `(...)`
    text = re.sub(r"`(\([^`]*PMID:[^`]*\))`", r"\1", text)

    def replace_paren_group(match):
        inner = match.group(1)
        found_pmids = re.findall(r"PMID:\s*(\d+)", inner)
        if not found_pmids:
            return match.group(0)

        cite_spans = []
        for pmid in found_pmids:
            info = pmid_map.get(pmid)
            apa_label = info["apa_text"] if info else f"et al., PMID:{pmid}"
            tooltip_text = f"PMID: {pmid}" + (f" ({info['journal']})" if info and info.get("journal") else "")
            cite_spans.append(
                f'<span class="apa-citation" data-pmid="{tooltip_text}">{apa_label}</span>'
            )

        return f'<span class="apa-citation-group">({"; ".join(cite_spans)})</span>'

    # 匹配包含 PMID: 的括號區塊
    return re.sub(r"\(([^()]*PMID:\s*\d+[^()]*)\)", replace_paren_group, text)


def _markdown_to_clean_html(md_text: str, pmid_map: dict[str, dict]) -> str:
    """
    將分段後的 Markdown 內文轉為適合前端打字機特效逐字渲染的乾淨 HTML
    """
    # 1. 先將 PMID 引用轉為 APA 7th HTML span
    text = _convert_citations_to_apa_html(md_text, pmid_map)

    # 2. 移除多餘的水平分隔線 ---
    lines = text.splitlines()
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == "---" or stripped == "***":
            continue

        # 處理 LaTeX 區塊公式 (例如 MoE = BMDL10 / Human Intake)
        if stripped.startswith("$$") and stripped.endswith("$$"):
            html_lines.append(
                '<div class="formula-box">MoE = BMDL<sub>10</sub> / Human Intake</div>'
            )
            continue

        # 行內粗體與斜體轉換
        line_formatted = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
        line_formatted = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_formatted)
        line_formatted = line_formatted.replace("$\\rightarrow$", "→")

        # 標題與清單轉換
        if line_formatted.startswith("#### "):
            html_lines.append(f'<h4 class="sub-sec-title">{line_formatted[5:]}</h4>')
        elif line_formatted.startswith("### "):
            html_lines.append(f'<h3 class="sec-title">{line_formatted[4:]}</h3>')
        elif re.match(r"^[-*]\s+", line_formatted):
            content = re.sub(r"^[-*]\s+", "", line_formatted)
            html_lines.append(f'<div class="bullet-item"><span class="bullet-dot">•</span><span>{content}</span></div>')
        elif re.match(r"^\d+\.\s+", line_formatted):
            m = re.match(r"^(\d+\.)\s+(.*)$", line_formatted)
            html_lines.append(f'<div class="num-item"><span class="num-idx">{m.group(1)}</span><span>{m.group(2)}</span></div>')
        elif line_formatted == "":
            html_lines.append('<div class="para-spacer"></div>')
        else:
            html_lines.append(f'<p class="report-para">{line_formatted}</p>')

    return "".join(html_lines)


def _split_markdown_into_tabs(raw_md: str, pmid_map: dict[str, dict], is_expert: bool = False) -> list[dict]:
    """
    依照 Markdown 中的 `### 1.`, `### 2.` 切分為獨立標籤頁資料，供前端 MetaPublic / MetaExpert 渲染
    """
    if not raw_md or not raw_md.strip():
        return []

    # 尋找所有 `### ` 開頭的主章節
    pattern = re.compile(r"(?=^###\s+\d+\.)", re.MULTILINE)
    parts = pattern.split(raw_md.strip())

    intro_prefix = ""
    sections = []

    for part in parts:
        part_strip = part.strip()
        if not part_strip:
            continue
        if not re.match(r"^###\s+\d+\.", part_strip):
            # 若第一段是前言 (如民眾版開頭的導言)，併入第一個章節上方
            intro_prefix = part_strip + "\n\n"
        else:
            sections.append(part_strip)

    if intro_prefix and sections:
        sections[0] = intro_prefix + sections[0]
    elif not sections:
        sections = [raw_md.strip()]

    # 定義簡潔好看的標籤頁短標題
    public_short_titles = ["1. 化學物質介紹", "2. 主要暴露途徑", "3. KCC 結論與危害分數"]
    expert_short_titles = [
        "1. MoE 與劑量效應",
        "2. Critical Effects (臨界效應)",
        "3. 10 KCCs 成果詳解",
        "4. 綜合危害分數與結論"
    ]
    short_list = expert_short_titles if is_expert else public_short_titles

    tabs = []
    for idx, sec_text in enumerate(sections):
        # 提取第一行 `### ...` 作為完整章節標題
        first_line_match = re.match(r"^###\s+([^\n]+)\n?(.*)", sec_text, re.DOTALL)
        if first_line_match:
            full_heading = first_line_match.group(1).strip()
            body_md = first_line_match.group(2).strip()
        else:
            full_heading = short_list[idx] if idx < len(short_list) else f"章節 {idx + 1}"
            body_md = sec_text

        tab_label = short_list[idx] if idx < len(short_list) else full_heading[:18]

        tabs.append({
            "id": f"tab-{idx + 1}",
            "tab_label": tab_label,
            "full_title": full_heading,
            "content_html": _markdown_to_clean_html(body_md, pmid_map)
        })

    return tabs


# =====================================================================
# API 1: 取得 Meta-analysis 儀表板數據與基礎標頭資料
# =====================================================================
@router.get("/{evaluation_id}/dashboard")
def get_meta_dashboard(evaluation_id: int, db: Session = Depends(get_db)):
    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj:
        raise HTTPException(status_code=404, detail=f"找不到評估單 ID: {evaluation_id}")

    # 若尚未計算過分數，自動即時計算一次
    if eval_obj.kcc_scores is None or eval_obj.hazard_score is None:
        calculate_evaluation_scores(db, evaluation_id)
        db.refresh(eval_obj)

    has_reports = bool(eval_obj.public_report and eval_obj.expert_report)

    return {
        "evaluation_id": eval_obj.id,
        "chemical_name": eval_obj.chemical_name.upper(),
        "cas_number": eval_obj.cas_number,
        "curated_date": _format_curated_date(eval_obj.updated_at or eval_obj.created_at),
        "hazard_score": eval_obj.hazard_score,
        "risk_level": eval_obj.risk_level,
        "status": eval_obj.status,
        "has_reports": has_reports,
        "kcc_data": eval_obj.kcc_scores
    }


# =====================================================================
# API 2: 取得民眾版與專家版分段標籤頁報告 (含 APA 7th 引用與 PMID Hover 資料)
# =====================================================================
@router.get("/{evaluation_id}/reports")
def get_meta_reports(evaluation_id: int, db: Session = Depends(get_db)):
    eval_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
    if not eval_obj:
        raise HTTPException(status_code=404, detail=f"找不到評估單 ID: {evaluation_id}")

    has_reports = bool(eval_obj.public_report and eval_obj.expert_report)

    public_tabs = []
    expert_tabs = []

    if has_reports:
        combined_text = f"{eval_obj.public_report}\n{eval_obj.expert_report}"
        pmid_map = _build_pmid_to_apa_map(db, combined_text)

        public_tabs = _split_markdown_into_tabs(eval_obj.public_report, pmid_map, is_expert=False)
        expert_tabs = _split_markdown_into_tabs(eval_obj.expert_report, pmid_map, is_expert=True)

    return {
        "evaluation_id": eval_obj.id,
        "chemical_name": eval_obj.chemical_name.upper(),
        "cas_number": eval_obj.cas_number,
        "curated_date": _format_curated_date(eval_obj.updated_at or eval_obj.created_at),
        "hazard_score": eval_obj.hazard_score,
        "risk_level": eval_obj.risk_level,
        "status": eval_obj.status,
        "has_reports": has_reports,
        "public_tabs": public_tabs,
        "expert_tabs": expert_tabs
    }