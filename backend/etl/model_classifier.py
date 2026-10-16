# backend/app/etl/model_classifier.py
# 【專職表四邏輯】獨立封裝 MeSH Major Topic 與 Regex 實驗模型判定規則
import re

def classify_experimental_model(mesh_terms: list[dict], pub_types: list[str], title: str, abstract: str) -> dict:
    """
    回傳結構對應【表四】：
    {
        "model_category": "Human" | "In Vivo" | "In Vitro" | "Unknown",
        "detection_method": "MeSH_Major" | "MeSH_General" | "Regex_Fallback",
        "matched_term": "實際配對到的字詞 (方便在前端顯示給專家看)"
    }
    """
    # 1. 第一優先：檢查 MeSH Major Topic (MajorTopicYN == 'Y')
    major_terms = [m["descriptor"].lower() for m in mesh_terms if m["is_major"]]
    if "humans" in major_terms:
        return {"model_category": "Human", "detection_method": "MeSH_Major", "matched_term": "Humans (Major)"}
    if "animals" in major_terms or "mice" in major_terms or "rats" in major_terms:
        return {"model_category": "In Vivo", "detection_method": "MeSH_Major", "matched_term": "Animals (Major)"}
    if any(k in major_terms for k in ["cells, cultured", "cell line", "in vitro techniques"]):
        return {"model_category": "In Vitro", "detection_method": "MeSH_Major", "matched_term": "In Vitro/Cells (Major)"}

    # 2. 第二優先：檢查一般 MeSH Terms (即使不是 Major Topic，但明確標註了物種)
    all_terms = [m["descriptor"].lower() for m in mesh_terms]
    if "humans" in all_terms and "animals" not in all_terms:
        return {"model_category": "Human", "detection_method": "MeSH_General", "matched_term": "Humans"}
    if "animals" in all_terms:
        return {"model_category": "In Vivo", "detection_method": "MeSH_General", "matched_term": "Animals"}

    # 3. 補漏備援 (Fallback)：針對剛發表、尚未被人工標註 MeSH 的新論文，用 Regex 掃描 Title + Abstract
    full_text = f"{title} {abstract}"
    if re.search(r"\b(cohort|epidemiolog\w+|patients|clinical trial)\b", full_text, re.IGNORECASE):
        return {"model_category": "Human", "detection_method": "Regex_Fallback", "matched_term": "Regex: Human/Cohort"}
    if re.search(r"\b(in vivo|mice|murine|rats|rodent|zebrafish)\b", full_text, re.IGNORECASE):
        return {"model_category": "In Vivo", "detection_method": "Regex_Fallback", "matched_term": "Regex: In Vivo"}
    if re.search(r"\b(in vitro|cell line|cell culture|hepg2|a549)\b", full_text, re.IGNORECASE):
        return {"model_category": "In Vitro", "detection_method": "Regex_Fallback", "matched_term": "Regex: In Vitro"}

    return {"model_category": "Unknown", "detection_method": "None", "matched_term": None}