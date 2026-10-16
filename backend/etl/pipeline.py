# backend/app/etl/pipeline.py 概念範例
# 【ETL 總指揮】解析 XML，組裝表三、表四、表五，並統一寫入 PostgreSQL
from app.models import Paper, PaperModel, PaperAuthor
from app.etl.model_classifier import classify_experimental_model

def parse_and_save_articles(xml_root, citation_map: dict, sjr_Rank_map: dict, db_session):
    for article_elem in xml_root.findall(".//PubmedArticle"):
        pmid = article_elem.findtext(".//PMID")
        
        # --- 1. 準備【表三：papers】資料 ---
        article_title = article_elem.findtext(".//ArticleTitle") or ""
        journal_title = article_elem.findtext(".//Journal/Title") or ""
        issn_linking = article_elem.findtext(".//MedlineJournalInfo/ISSNLinking") or ""
        clean_issn = issn_linking.replace("-", "")
        
        new_paper = Paper(
            pmid=pmid,
            article_title=article_title,      # 注意：論文標題與期刊名稱建議分成兩個欄位！
            journal_title=journal_title,
            iso_abbreviation=article_elem.findtext(".//Journal/ISOAbbreviation"),
            abstract=" ".join([t.text for t in article_elem.findall(".//AbstractText") if t.text]),
            issn_linking=issn_linking,
            quartile=sjr_Rank_map.get(clean_issn, "Unranked"), # 對照表二取得 Q1~Q4
            citation_count=citation_map.get(pmid, 0)           # 對照 ELink 取得引用數
        )

        # --- 2. 準備【表四：paper_models】資料 ---
        mesh_list = []
        for mesh in article_elem.findall(".//MeshHeading"):
            desc = mesh.find(".//DescriptorName")
            if desc is not None:
                mesh_list.append({
                    "descriptor": desc.text,
                    "is_major": desc.attrib.get("MajorTopicYN") == "Y"
                })
        
        model_res = classify_experimental_model(mesh_list, [], article_title, new_paper.abstract)
        new_paper.model_info = PaperModel(
            model_category=model_res["model_category"],
            detection_method=model_res["detection_method"],
            matched_term=model_res["matched_term"]
        )

        # --- 3. 準備【表五：paper_authors】資料 ---
        for author_elem in article_elem.findall(".//Author"):
            new_paper.authors.append(
                PaperAuthor(
                    last_name=author_elem.findtext("LastName"),
                    fore_name=author_elem.findtext("ForeName"),
                    initials=author_elem.findtext("Initials"),
                    affiliation=author_elem.findtext(".//Affiliation")
                )
            )

        # 將組裝好的母物件加入 Session，SQLAlchemy 會自動同步寫入表三、表四、表五！
        db_session.add(new_paper)

    db_session.commit()