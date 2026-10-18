# backend/scripts/init_kcc_db.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models.kcc import KccQuery, KccQueryEmbedding

# =====================================================================
# 👇👇👇 【手動新增/修改區】10 KCC 關鍵片段字典 👇👇👇
# 說明：
# - kcc_id: 對應前端儀表板的 "01" ~ "10"
# - kcc_title: 對應前端儀表板的 KCC 標題
# - queries: 每個 KCC 底下的多個關鍵片段 (query_code 必須唯一)
# =====================================================================
KCC_QUERIES_DATA = [
    {
        "kcc_id": "01",
        "kcc_title": "ELECTROPHILIC",
        "queries": [
            {
                "query_code": "KC1-1",
                "query_text": "Electrophilicity and metabolic activation: parent compound or reactive metabolite electrophilicity."
            },
            {
                "query_code": "KC1-2",
                "query_text": "Electrophilicity and metabolic activation: electrophilic structure such as epoxide, aldehyde, or quinone."
            },
            {
                "query_code": "KC1-3",
                "query_text": "Electrophilicity and metabolic activation: covalent binding and formation of DNA adducts or protein adducts."
            },
        ]
    },
    {
        "kcc_id": "02",
        "kcc_title": "GENOTOXIC",
        "queries": [
            {
                "query_code": "KC2-1",
                "query_text": "Genotoxicity: DNA damage, single-strand breaks, double-strand breaks, or interstrand crosslinks."
            },
            {
                "query_code": "KC2-2",
                "query_text": "Genotoxicity: gene mutations, mutagenic activity in Ames test, or point mutations."
            },
            {
                "query_code": "KC2-3",
                "query_text": "Genotoxicity: chromosomal aberrations, micronucleus formation, sister chromatid exchange, or aneuploidy."
            },
        ]
    },
    {
        "kcc_id": "03",
        "kcc_title": "ALTERS DNA REPAIR",
        "queries": [
            {
                "query_code": "KC3-1",
                "query_text": "Alters DNA repair or causes genomic instability: inhibition of base excision repair or nucleotide excision repair."
            },
            {
                "query_code": "KC3-2",
                "query_text": "Alters DNA repair or causes genomic instability: homologous recombination deficiency, mismatch repair defects, or microsatellite instability."
            },
        ]
    },
    {
        "kcc_id": "04",
        "kcc_title": "EPIGENETIC ALTERATIONS",
        "queries": [
            {
                "query_code": "KC4-1",
                "query_text": "Induces epigenetic alterations: aberrant DNA methylation, CpG island hypermethylation, or global hypomethylation."
            },
            {
                "query_code": "KC4-2",
                "query_text": "Induces epigenetic alterations: histone modification, chromatin remodeling, or altered microRNA and non-coding RNA expression."
            },
        ]
    },
    {
        "kcc_id": "05",
        "kcc_title": "OXIDATIVE STRESS",
        "queries": [
            {
                "query_code": "KC5-1",
                "query_text": "Induces oxidative stress: generation of reactive oxygen species (ROS), reactive nitrogen species, or free radicals."
            },
            {
                "query_code": "KC5-2",
                "query_text": "Induces oxidative stress: lipid peroxidation, 8-oxo-dG oxidative DNA damage, or depletion of glutathione (GSH) and antioxidant enzymes."
            },
        ]
    },
    {
        "kcc_id": "06",
        "kcc_title": "CHRONIC INFLAMMATION",
        "queries": [
            {
                "query_code": "KC6-1",
                "query_text": "Induces chronic inflammation: persistent inflammatory cell infiltration, macrophage activation, or tissue inflammation."
            },
            {
                "query_code": "KC6-2",
                "query_text": "Induces chronic inflammation: upregulation of pro-inflammatory cytokines (IL-6, TNF-alpha, IL-1beta), chemokines, or NF-kappaB signaling."
            },
        ]
    },
    {
        "kcc_id": "07",
        "kcc_title": "IMMUNOSUPPRESSIVE",
        "queries": [
            {
                "query_code": "KC7-1",
                "query_text": "Is immunosuppressive: suppression of immune surveillance, T-cell function, or natural killer (NK) cell cytotoxicity."
            },
            {
                "query_code": "KC7-2",
                "query_text": "Is immunosuppressive: impaired humoral or cellular immunity, lymphotoxicity, or decreased antibody production."
            },
        ]
    },
    {
        "kcc_id": "08",
        "kcc_title": "RECEPTOR-MEDIATED EFFECTS",
        "queries": [
            {
                "query_code": "KC8-1",
                "query_text": "Modulates receptor-mediated effects: binding and activation of aryl hydrocarbon receptor (AhR), CAR, PXR, or PPAR."
            },
            {
                "query_code": "KC8-2",
                "query_text": "Modulates receptor-mediated effects: endocrine disruption, estrogen receptor, androgen receptor, or thyroid hormone signaling modulation."
            },
        ]
    },
    {
        "kcc_id": "09",
        "kcc_title": "IMMORTALIZATION",
        "queries": [
            {
                "query_code": "KC9-1",
                "query_text": "Causes immortalization: activation of telomerase (hTERT), telomere length maintenance, or bypass of cellular senescence."
            },
            {
                "query_code": "KC9-2",
                "query_text": "Causes immortalization: inactivation of p53 or retinoblastoma (Rb) tumor suppressor pathways leading to unlimited replicative potential."
            },
        ]
    },
    {
        "kcc_id": "10",
        "kcc_title": "CELL PROLIFERATION/DEATH",
        "queries": [
            {
                "query_code": "KC10-1",
                "query_text": "Alters cell proliferation, cell death, or nutrient supply: evasion of apoptosis, sustained proliferative signaling, or hyperplasia."
            },
            {
                "query_code": "KC10-2",
                "query_text": "Alters cell proliferation, cell death, or nutrient supply: induction of angiogenesis, VEGF upregulation, or altered cellular energetics."
            },
        ]
    },
]
# =====================================================================
# 👆👆👆 【手動新增/修改區結束】 👆👆👆
# =====================================================================

def init_kcc_queries():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    added_count = 0
    updated_count = 0
    unchanged_count = 0

    try:
        for kcc_group in KCC_QUERIES_DATA:
            kcc_id = kcc_group["kcc_id"].strip()
            kcc_title = kcc_group["kcc_title"].strip()

            for q in kcc_group["queries"]:
                code = q["query_code"].strip()
                text = q["query_text"].strip()

                existing = db.query(KccQuery).filter_by(query_code=code).first()
                if not existing:
                    new_q = KccQuery(
                        kcc_id=kcc_id,
                        kcc_title=kcc_title,
                        query_code=code,
                        query_text=text
                    )
                    db.add(new_q)
                    added_count += 1
                else:
                    # 若你修改了某條關鍵片段的文字，自動更新文字並刪除舊向量以便重算
                    if existing.query_text != text or existing.kcc_title != kcc_title:
                        existing.query_text = text
                        existing.kcc_title = kcc_title
                        existing.kcc_id = kcc_id
                        if existing.embedding_record:
                            db.delete(existing.embedding_record)
                        updated_count += 1
                    else:
                        unchanged_count += 1

        db.commit()
        print(f"✅ [表七: kcc_queries] 同步完成！新增: {added_count} 筆 | 修改: {updated_count} 筆 | 未變動: {unchanged_count} 筆。")
    except Exception as e:
        db.rollback()
        print(f"❌ 匯入失敗：{e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_kcc_queries()