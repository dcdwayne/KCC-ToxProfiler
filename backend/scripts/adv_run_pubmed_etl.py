# backend/scripts/run_pubmed_etl.py (只需替換設定區與 run_etl 迴圈部分，或直接整份覆蓋)
import sys
import re
from pathlib import Path
from collections import defaultdict

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models import TargetChemical, JournalRanking, Paper, PaperModel, PaperAuthor
from app.etl.pubmed_client import search_pmids_by_synonyms, fetch_citation_counts_batch, fetch_pubmed_xml_batch
from app.etl.model_classifier import classify_experimental_model

# =====================================================================
# 👇👇👇 【抓取數量設定】 👇👇👇
# - 若設為整數 (例如 500)：每個化學物質最多抓關聯度最高的前 500 篇
# - 若設為 None：解除限制，把符合條件的數千/上萬篇文獻「全部抓下來」！
# =====================================================================
MAX_PAPERS_PER_CHEMICAL = None

# 每次向 NCBI EFetch / ELink 請求並寫入資料庫的批次大小 (200 篇最穩定，不會超時)
BATCH_SIZE = 200


def extract_full_text(elem) -> str:
    if elem is None:
        return ""
    return "".join(elem.itertext()).strip()


def parse_pub_date(pub_date_elem) -> tuple[str, int | None]:
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
        m = re.search(r"\b(19\d\d|20\d\d)\b", medline_date)
        return (medline_date, int(m.group(1)) if m else None)
    return ("Unknown", None)


def run_etl():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("📚 正在載入表二 (journal_rankings) ISSN 對照字典...")
        sjr_rows = db.query(JournalRanking.issn, JournalRanking.quartile).all()
        sjr_map = {row.issn: row.quartile for row in sjr_rows}

        chem_rows = db.query(TargetChemical).all()
        cas_groups = defaultdict(list)
        for c in chem_rows:
            cas_groups[c.cas_number].append(c.chemical_name)

        for cas_number, synonyms in cas_groups.items():
            primary_name = synonyms[0]
            print(f"\n🔍 開始處理化學物質: {primary_name} (CAS: {cas_number}) | 同義詞: {synonyms}")

            # 1. 取得所有符合的 PMID 清單
            pmids = search_pmids_by_synonyms(synonyms, max_results=MAX_PAPERS_PER_CHEMICAL)
            if not pmids:
                continue

            # 2. 比對資料庫中已經抓過的所有 PMID (支援斷點續傳！)
            existing_pmids = {
                r[0] for r in db.query(Paper.pmid).filter(Paper.cas_number == cas_number).all()
            }
            # 為防止不同化學物質抓到同一篇綜合性論文導致 Unique 衝突，也檢查全表 PMID
            all_db_pmids = {r[0] for r in db.query(Paper.pmid).all()}
            
            new_pmids = [p for p in pmids if p not in all_db_pmids]
            total_new = len(new_pmids)
            print(f"   共找到 {len(pmids)} 篇 PMID，扣除已存在文獻後，尚有 {total_new} 篇準備抓取。")

            if not new_pmids:
                continue

            # 3. 以每 BATCH_SIZE (200 篇) 為單位，分批下載並寫入資料庫
            total_saved_for_chem = 0
            for start_idx in range(0, total_new, BATCH_SIZE):
                batch_pmids = new_pmids[start_idx : start_idx + BATCH_SIZE]
                batch_num = (start_idx // BATCH_SIZE) + 1
                total_batches = (total_new + BATCH_SIZE - 1) // BATCH_SIZE

                print(f"   ⏳ [{primary_name}] 正在處理第 {batch_num}/{total_batches} 批次 ({len(batch_pmids)} 篇)...")

                # 3.1 批次查詢被引用次數
                citation_map = fetch_citation_counts_batch(batch_pmids)

                # 3.2 批次下載 XML
                xml_root = fetch_pubmed_xml_batch(batch_pmids)

                batch_saved = 0
                for article in xml_root.findall(".//PubmedArticle"):
                    pmid = article.findtext(".//MedlineCitation/PMID")
                    if not pmid:
                        continue

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

                    article_title = extract_full_text(article.find(".//Article/ArticleTitle")) or "No Title"
                    journal_title = article.findtext(".//Article/Journal/Title")
                    iso_abbr = article.findtext(".//Article/Journal/ISOAbbreviation")
                    pub_date_str, pub_year = parse_pub_date(article.find(".//Article/Journal/JournalIssue/PubDate"))

                    pub_types = [pt.text for pt in article.findall(".//Article/PublicationTypeList/PublicationType") if pt.text]
                    pub_type_str = "; ".join(pub_types)

                    doi, pmcid = None, None
                    for aid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                        id_type = aid.attrib.get("IdType")
                        if id_type == "doi":
                            doi = aid.text
                        elif id_type == "pmc":
                            pmcid = aid.text

                    raw_issn = article.findtext(".//Article/Journal/ISSN") or ""
                    raw_issn_linking = article.findtext(".//MedlineCitation/MedlineJournalInfo/ISSNLinking") or ""
                    clean_issn = raw_issn.replace("-", "").strip()
                    clean_linking = raw_issn_linking.replace("-", "").strip()
                    quartile = sjr_map.get(clean_issn) or sjr_map.get(clean_linking) or "Unranked"

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

                    mesh_list = []
                    for mh in article.findall(".//MedlineCitation/MeshHeadingList/MeshHeading"):
                        desc = mh.find("DescriptorName")
                        if desc is not None and desc.text:
                            is_major = (desc.attrib.get("MajorTopicYN") == "Y")
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

                    author_elems = article.findall(".//Article/AuthorList/Author")
                    for idx, auth in enumerate(author_elems, start=1):
                        last_name = auth.findtext("LastName")
                        fore_name = auth.findtext("ForeName")
                        initials = auth.findtext("Initials")
                        affiliation = auth.findtext(".//AffiliationInfo/Affiliation")
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
                    batch_saved += 1

                # 每 200 篇立即 Commit 存檔一次，確保進度不遺失！
                db.commit()
                total_saved_for_chem += batch_saved
                print(f"      💾 第 {batch_num} 批次已寫入 {batch_saved} 篇 (累計新增: {total_saved_for_chem} 篇)")

            print(f"   🎉 {primary_name} 全數處理完成！本次共寫入 {total_saved_for_chem} 篇文獻。")

    except Exception as e:
        db.rollback()
        print(f"❌ ETL 執行發生錯誤：{e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_etl()