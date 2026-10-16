# backend/app/etl/pubmed_client.py
import time
import requests
import xml.etree.ElementTree as ET

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_pmids_by_synonyms(synonyms: list[str], max_results: int = 30) -> list[str]:
    """
    1. ESearch：利用表一的化學物質同義詞清單，搜尋具備摘要 (hasabstract) 的文獻 PMID
    """
    # 組合查詢語句：("Benzo[a]pyrene"[Title/Abstract] OR "BaP"[Title/Abstract] ...) AND hasabstract
    or_clause = " OR ".join([f'"{name}"[Title/Abstract]' for name in synonyms])
    query = f"({or_clause}) AND (toxic*[Title/Abstract] OR carcinogen*[Title/Abstract] OR oxidative[Title/Abstract] OR muta*[Title/Abstract] OR DNA[Title/Abstract]) AND hasabstract[text]"

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance" # 優先抓取關聯度最高的文獻
    }
    
    resp = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    time.sleep(0.35) # 遵守 NCBI 每秒不超過 3 次請求的限制
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_citation_counts_batch(pmids: list[str]) -> dict[str, int]:
    """
    2. ELink：利用 &id=111&id=222 多組 ID 同時查詢特性，一次拿回整批論文的「被引用次數」
    """
    if not pmids:
        return {}

    citation_map = {pmid: 0 for pmid in pmids}
    
    # 重要：在 requests 的 params 放入 list，網址會自動編成 &id=9542332&id=1234567...
    params = [
        ("dbfrom", "pubmed"),
        ("linkname", "pubmed_pubmed_citedin"),
        ("retmode", "xml")
    ] + [("id", pmid) for pmid in pmids]

    resp = requests.get(f"{BASE_URL}/elink.fcgi", params=params, timeout=60)
    resp.raise_for_status()
    time.sleep(0.35)

    root = ET.fromstring(resp.content)
    # 解析每一個 LinkSet (對應每一篇查詢的 PMID)
    for linkset in root.findall(".//LinkSet"):
        source_pmid = linkset.findtext("./IdList/Id")
        if source_pmid:
            # 計算 LinkSetDb 底下的 Link 數量，即為引用該篇論文的文獻數量
            citing_links = linkset.findall("./LinkSetDb/Link/Id")
            citation_map[source_pmid] = len(citing_links)

    return citation_map


def fetch_pubmed_xml_batch(pmids: list[str]) -> ET.Element:
    """
    3. EFetch：批次抓取文獻的完整 XML (包含摘要、ISSN、MeSH 與作者清單)
    """
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    resp = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=60)
    resp.raise_for_status()
    time.sleep(0.35)
    return ET.fromstring(resp.content)