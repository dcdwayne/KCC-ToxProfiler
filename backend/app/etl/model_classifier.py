# backend/app/etl/model_classifier.py
# 「1. MeSH Major Topic 優先 $\rightarrow$ 2. Publication Type 與次要 MeSH $\rightarrow$ 3. Title/Abstract 正則表達式補漏」三層判定邏輯
import re

# MVP 分數對照表 (人=10, 動物=7, 細胞=3, 未分類=1)
SCORE_MAP = {
    "Human": 10,
    "In Vivo": 7,
    "In Vitro": 3,
    "Unknown": 1
}

# MeSH 詞彙分類字典
HUMAN_MESH = {"humans", "epidemiologic studies", "cohort studies", "case-control studies", "clinical study"}
INVIVO_MESH = {"animals", "mice", "rats", "rodentia", "zebrafish", "rabbits", "guinea pigs", "dogs", "swine", "mammals"}
INVITRO_MESH = {"cells, cultured", "cell line", "cell line, tumor", "in vitro techniques", "cell survival", "primary cell culture"}

# Publication Type 臨床/人體研究關鍵字
HUMAN_PUBTYPES = {"Clinical Trial", "Observational Study", "Randomized Controlled Trial", "Case Reports", "Multicenter Study"}

# 正則表達式補漏 (使用 \b 確保比對完整單字，避免誤判)
REGEX_HUMAN = re.compile(r"\b(cohort|epidemiolog\w+|patients|clinical trial|human subjects|workers|populations|participants)\b", re.IGNORECASE)
REGEX_INVIVO = re.compile(r"\b(in vivo|mice|mouse|murine|rats|rat|rodent\w*|zebrafish|hamster\w*|animal model\w*|balb/c|c57bl/6|sprague-dawley|wistar)\b", re.IGNORECASE)
REGEX_INVITRO = re.compile(r"\b(in vitro|cell line\w*|cell culture\w*|cultured cells|hepg2|a549|mcf-7|hela|hek293|beas-2b|cho cells|ames test|cytotoxic\w*)\b", re.IGNORECASE)


def classify_experimental_model(mesh_list: list[dict], pub_types: list[str], title: str, abstract: str) -> dict:
    """
    輸入：
      - mesh_list: [{"descriptor": "Animals", "is_major": True}, ...]
      - pub_types: ["Journal Article", "Clinical Trial", ...]
      - title, abstract: 論文標題與摘要
    輸出：對應表四 (paper_models) 的欄位字典
    """
    raw_mesh_str = "; ".join([f"{m['descriptor']}{'[Major]' if m['is_major'] else ''}" for m in mesh_list])

    # =================================================================
    # 第一層 (最高優先)：檢查 MeSH Major Topic (MajorTopicYN="Y") 或明確的臨床 PubType
    # 避免抓到論文中順帶提及的次要模型
    # =================================================================
    major_terms = [m["descriptor"] for m in mesh_list if m["is_major"]]
    major_lower = {t.lower() for t in major_terms}

    # 1A. 檢查 Publication Type 是否為明確臨床研究
    matched_pub = [pt for pt in pub_types if pt in HUMAN_PUBTYPES]
    if matched_pub:
        return _build_result("Human", "PubType", "; ".join(matched_pub), raw_mesh_str)

    # 1B. 檢查 MeSH Major Topic
    human_major = [t for t in major_terms if t.lower() in HUMAN_MESH]
    if human_major:
        return _build_result("Human", "MeSH_Major", "; ".join(human_major), raw_mesh_str)

    invivo_major = [t for t in major_terms if t.lower() in INVIVO_MESH]
    if invivo_major:
        return _build_result("In Vivo", "MeSH_Major", "; ".join(invivo_major), raw_mesh_str)

    invitro_major = [t for t in major_terms if t.lower() in INVITRO_MESH]
    if invitro_major:
        return _build_result("In Vitro", "MeSH_Major", "; ".join(invitro_major), raw_mesh_str)

    # =================================================================
    # 第二層 (次要核心)：檢查一般 MeSH Terms
    # (因為 PubMed 標記習慣中，Humans 與 Animals 常被標為 N，但搭配實驗名詞)
    # =================================================================
    all_terms = [m["descriptor"] for m in mesh_list]
    all_lower = {t.lower() for t in all_terms}

    # 先判斷是否有明確的細胞株/In Vitro MeSH
    invitro_minor = [t for t in all_terms if t.lower() in INVITRO_MESH]
    # 若同時有 Animals (非人體)，優先歸類為 In Vivo；若只有 Humans + Cultured Cells，通常是人類細胞株實驗 (In Vitro)
    invivo_minor = [t for t in all_terms if t.lower() in INVIVO_MESH]
    human_minor = [t for t in all_terms if t.lower() in HUMAN_MESH]

    if invivo_minor:
        return _build_result("In Vivo", "MeSH_General", "; ".join(invivo_minor), raw_mesh_str)
    if invitro_minor:
        return _build_result("In Vitro", "MeSH_General", "; ".join(invitro_minor), raw_mesh_str)
    if human_minor:
        return _build_result("Human", "MeSH_General", "; ".join(human_minor), raw_mesh_str)

    # =================================================================
    # 第三層 (補漏備援)：針對尚未標註 MeSH 的最新論文，使用 Regex 掃描 Title 與 Abstract
    # =================================================================
    full_text = f"{title} {abstract}"

    # 檢查順序：先看有無明確動物或人體流行病學字眼，再看細胞字眼
    m_human = set(m.group(0).lower() for m in REGEX_HUMAN.finditer(full_text))
    m_invivo = set(m.group(0).lower() for m in REGEX_INVIVO.finditer(full_text))
    m_invitro = set(m.group(0).lower() for m in REGEX_INVITRO.finditer(full_text))

    if m_human and not m_invitro:
        return _build_result("Human", "Regex_Fallback", ", ".join(m_human), raw_mesh_str)
    if m_invivo:
        return _build_result("In Vivo", "Regex_Fallback", ", ".join(m_invivo), raw_mesh_str)
    if m_invitro:
        return _build_result("In Vitro", "Regex_Fallback", ", ".join(m_invitro), raw_mesh_str)
    if m_human:
        return _build_result("Human", "Regex_Fallback", ", ".join(m_human), raw_mesh_str)

    return _build_result("Unknown", "Unclassified", None, raw_mesh_str)


def _build_result(category: str, source: str, matched: str, raw_mesh: str) -> dict:
    return {
        "model_category": category,
        "base_score": SCORE_MAP.get(category, 1),
        "detection_source": source,
        "matched_terms": matched,
        "raw_mesh_terms": raw_mesh if raw_mesh else None
    }