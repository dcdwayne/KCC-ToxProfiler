# backend/scripts/run_pubmed_etl.py
"""
這支腳本會自動：
1.讀取你的表一 (target_chemicals) 與表二 (journal_rankings)。   
2.去 PubMed 抓取文獻 XML 與被引用次數。
3.對照表二的 ISSN 填入 Q1~Q4 級別。
4.同時解析並寫入表三 (papers)、表四 (paper_models)與表五 (paper_authors)。
"""
import sys
import re
from pathlib import Path
from collections import defaultdict

# 將 backend 目錄加入路徑
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models import TargetChemical, JournalRanking, Paper, PaperModel, PaperAuthor
from app.etl.pubmed_client import search_pmids_by_synonyms, fetch_citation_counts_batch, fetch_pubmed_xml_batch
from app.etl.model_classifier import classify_experimental_model

# 設定每個化學物質最多抓取幾篇文獻 (MVP 測試建議先設 30 篇，確認無誤後可調高至 100~200)
MAX_PAPERS_PER_CHEMICAL = 200


def extract_full_text(elem) -> str:
    """安全提取 XML 節點內的所有文字（包含 <i>, <sub> 等子標籤內的文字）"""
    if elem is None:
        return ""
    return "".join(elem.itertext()).strip()


def parse_pub_date(pub_date_elem) -> tuple[str, int | None]:
    """解析發表日期與純數字年份"""
    if pub_date_elem is None:
        return ("Unknown", None)
    
    year = pub_date_elem.findtext("Year")
    month = pub_date_elem.findtext("Month") or ""
    day = pub_date_elem.findtext("Day") or ""
    medline_date = pub_date_elem.findtext("MedlineDate")

    if year:
        date_str = f"{year} {month} {day}".strip()
        return (date_str, int(year) if year.isdigit() else None)
    elif medline_date:
        # 從 MedlineDate (如 "2023 Jan-Feb") 中用正則抓出 4 碼年份
        m = re.search(r"\b(19\d\d|20\d\d)\b", medline_date)
        return (medline_date, int(m.group(1)) if m else None)
    return ("Unknown", None)


def run_etl():
    # 1. 確保表三、表四、表五已在 PostgreSQL 中建立
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 2. 載入【表二：journal_rankings】建立記憶體快取字典 {issn: quartile}
        print("📚 正在載入表二 (journal_rankings) ISSN 對照字典...")
        sjr_rows = db.query(JournalRanking.issn, JournalRanking.quartile).all()
        sjr_map = {row.issn: row.quartile for row in sjr_rows}
        print(f"   已載入 {len(sjr_map)} 筆 ISSN 級別對照資料。")

        # 3. 載入【表一：target_chemicals】依 CAS 號碼分組所有同義詞
        chem_rows = db.query(TargetChemical).all()
        cas_groups = defaultdict(list)
        for c in chem_rows:
            cas_groups[c.cas_number].append(c.chemical_name)

        if not cas_groups:
            print("⚠️ 表一 (target_chemicals) 無資料，請先執行 init_tc_db.py！")
            return

        # 4. 針對每一個化學物質執行 ETL
        for cas_number, synonyms in cas_groups.items():
            primary_name = synonyms[0]
            print(f"\n🔍 開始處理化學物質: {primary_name} (CAS: {cas_number}) | 同義詞: {synonyms}")

            # 4.1 ESearch 取得 PMID 清單
            pmids = search_pmids_by_synonyms(synonyms, max_results=MAX_PAPERS_PER_CHEMICAL)
            if not pmids:
                print(f"   ⚠️ 找不到 {primary_name} 的相關文獻。")
                continue

            # 過濾掉資料庫已經抓過的 PMID (避免重複寫入報錯)
            existing_pmids = {
                r[0] for r in db.query(Paper.pmid).filter(Paper.pmid.in_(pmids)).all()
            }
            new_pmids = [p for p in pmids if p not in existing_pmids]
            print(f"   共找到 {len(pmids)} 篇 PMID，其中 {len(new_pmids)} 篇為全新文獻。")

            if not new_pmids:
                continue

            # 4.2 ELink 批次取得這批 PMID 的「被引用次數」
            print(f"   🔗 正在透過 ELink 批次查詢 {len(new_pmids)} 篇文獻的被引用次數...")
            citation_map = fetch_citation_counts_batch(new_pmids)

            # 4.3 EFetch 批次下載完整 XML
            print(f"   📥 正在透過 EFetch 下載完整 XML 與解析三張表資料...")
            xml_root = fetch_pubmed_xml_batch(new_pmids)

            saved_count = 0
            for article in xml_root.findall(".//PubmedArticle"):
                pmid = article.findtext(".//MedlineCitation/PMID")
                if not pmid:
                    continue

                # 提取完整摘要 (若無摘要則跳過，因為 RAG 必須有摘要才能切片)
                abstract_elems = article.findall(".//Article/Abstract/AbstractText")
                abstract_parts = []
                for ab in abstract_elems:
                    label = ab.attrib.get("Label")
                    text = extract_full_text(ab)
                    if text:
                        abstract_parts.append(f"{label}: {text}" if label else text)
                abstract_full = " ".join(abstract_parts)
                if not abstract_full:
                    continue

                # 提取標題與期刊資訊
                article_title = extract_full_text(article.find(".//Article/ArticleTitle")) or "No Title"
                journal_title = article.findtext(".//Article/Journal/Title")
                iso_abbr = article.findtext(".//Article/Journal/ISOAbbreviation")
                
                # 提取發表日期與年份
                pub_date_str, pub_year = parse_pub_date(article.find(".//Article/Journal/JournalIssue/PubDate"))

                # 提取 Publication Types
                pub_types = [pt.text for pt in article.findall(".//Article/PublicationTypeList/PublicationType") if pt.text]
                pub_type_str = "; ".join(pub_types)

                # 提取 DOI 與 PMCID
                doi, pmcid = None, None
                for aid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                    id_type = aid.attrib.get("IdType")
                    if id_type == "doi":
                        doi = aid.text
                    elif id_type == "pmc":
                        pmcid = aid.text

                # 提取 ISSN 與 ISSN Linking，並對照【表二】取得 Q1~Q4
                raw_issn = article.findtext(".//Article/Journal/ISSN") or ""
                raw_issn_linking = article.findtext(".//MedlineCitation/MedlineJournalInfo/ISSNLinking") or ""
                
                clean_issn = raw_issn.replace("-", "").strip()
                clean_linking = raw_issn_linking.replace("-", "").strip()
                
                # 優先用 ISSN 對照，若無則用 ISSNLinking 對照
                quartile = sjr_map.get(clean_issn) or sjr_map.get(clean_linking) or "Unranked"

                # --- 建立【表三：Paper】物件 ---
                paper_obj = Paper(
                    cas_number=cas_number,
                    pmid=pmid,
                    doi=doi,
                    pmcid=pmcid,
                    article_title=article_title,
                    journal_title=journal_title,
                    iso_abbreviation=iso_abbr,
                    abstract=abstract_full,
                    pub_date=pub_date_str,
                    pub_year=pub_year,
                    pub_type=pub_type_str,
                    issn=raw_issn if raw_issn else None,
                    issn_linking=raw_issn_linking if raw_issn_linking else None,
                    citation_count=citation_map.get(pmid, 0),
                    quartile=quartile
                )

                # --- 解析並建立【表四：PaperModel】物件 ---
                mesh_list = []
                for mh in article.findall(".//MedlineCitation/MeshHeadingList/MeshHeading"):
                    desc = mh.find("DescriptorName")
                    if desc is not None and desc.text:
                         is_major = (desc.attrib.get("MajorTopicYN") == "Y")
                    # 若 Qualifier (子主題) 被標為 MajorTopicYN="Y"，也視為 Major
                    for qual in mh.findall("QualifierName"):
                        if qual.attrib.get("MajorTopicYN") == "Y":
                            is_major = True
                    mesh_list.append({"descriptor": desc.text, "is_major": is_major})

                model_res = classify_experimental_model(mesh_list, pub_types, article_title, abstract_full)
                paper_obj.model_info = PaperModel(
                    pmid=pmid,
                    model_category=model_res["model_category"],
                    base_score=model_res["base_score"],
                    detection_source=model_res["detection_source"],
                    matched_terms=model_res["matched_terms"],
                    raw_mesh_terms=model_res["raw_mesh_terms"]
                )

                # --- 解析並建立【表五：PaperAuthor】物件清單 ---
                author_elems = article.findall(".//Article/AuthorList/Author")
                for idx, auth in enumerate(author_elems, start=1):
                    last_name = auth.findtext("LastName")
                    fore_name = auth.findtext("ForeName")
                    initials = auth.findtext("Initials")
                    affiliation = auth.findtext(".//AffiliationInfo/Affiliation")
                    
                    # 只有當作者有姓名時才寫入 (排除純團體名稱的空節點)
                    if last_name or fore_name:
                        paper_obj.authors.append(
                            PaperAuthor(
                                pmid=pmid,
                                author_order=idx,
                                last_name=last_name,
                                fore_name=fore_name,
                                initials=initials,
                                affiliation=affiliation
                            )
                        )

                db.add(paper_obj)
                saved_count += 1

            db.commit()
            print(f"   ✅ {primary_name} 處理完成！成功寫入 {saved_count} 篇完整文獻至表三、表四、表五。")

    except Exception as e:
        db.rollback()
        print(f"❌ ETL 執行發生錯誤：{e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_etl()