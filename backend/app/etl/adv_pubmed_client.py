# backend/app/etl/pubmed_client.py
import time
import requests
import xml.etree.ElementTree as ET

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# 💡 提示：若未來去 NCBI 免費申請一組 API Key 填在這裡，速度可從每秒 3 次提升至每秒 10 次！
NCBI_API_KEY = None 
SLEEP_INTERVAL = 0.12 if NCBI_API_KEY else 0.35


def _build_query(synonyms: list[str], require_tox_filter: bool = True) -> str:
    """組合 PubMed 檢索語法"""
    or_clause = " OR ".join([f'"{name}"[Title/Abstract]' for name in synonyms])
    if require_tox_filter:
        # 鎖定標題/摘要含有該化學物，且與毒理/致癌/機轉相關、並具備摘要的文獻
        return (
            f"({or_clause}) AND "
            f"(toxic*[Title/Abstract] OR carcinogen*[Title/Abstract] OR oxidative[Title/Abstract] "
            f"OR muta*[Title/Abstract] OR DNA[Title/Abstract] OR exposure[Title/Abstract] "
            f"OR hazard[Title/Abstract] OR cancer[Title/Abstract] OR cell[Title/Abstract]) "
            f"AND hasabstract[text]"
        )
    else:
        # 若想連非毒理領域、只要有摘要的全部抓下來，可將 require_tox_filter 設為 False
        return f"({or_clause}) AND hasabstract[text]"


def _fetch_pmid_page(query: str, retstart: int, retmax: int, mindate: str = None, maxdate: str = None) -> tuple[int, list[str]]:
    """執行單次 ESearch 分頁查詢，回傳 (總筆數, PMID清單)"""
    params = {
        "db": "pubmed",
        "term": query,
        "retstart": retstart,
        "retmax": retmax,
        "retmode": "json",
        "sort": "relevance"
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    if mindate and maxdate:
        params["datetype"] = "pdat"
        params["mindate"] = mindate
        params["maxdate"] = maxdate

    resp = requests.post(f"{BASE_URL}/esearch.fcgi", data=params, timeout=30)
    resp.raise_for_status()
    time.sleep(SLEEP_INTERVAL)
    
    res = resp.json().get("esearchresult", {})
    total_count = int(res.get("count", 0))
    id_list = res.get("idlist", [])
    return total_count, id_list


def search_pmids_by_synonyms(synonyms: list[str], max_results: int | None = None, require_tox_filter: bool = True) -> list[str]:
    """
    支援全量抓取的 ESearch：
    - 若 max_results 為整數 (如 500)，則最多抓 500 篇。
    - 若 max_results 為 None，則不設上限，自動翻頁把所有符合的 PMID 全部抓下來！
    """
    query = _build_query(synonyms, require_tox_filter)
    
    # 先抓第一頁探測總數量 (Count)
    first_page_size = min(max_results, 5000) if max_results else 5000
    total_count, pmids = _fetch_pmid_page(query, retstart=0, retmax=first_page_size)
    print(f"   📊 PubMed 符合條件總文獻數 (Count): {total_count} 篇")

    if total_count == 0:
        return []

    target_total = min(total_count, max_results) if max_results else total_count

    # 情況 A：目標數量在 9,999 篇以內，直接用 retstart 翻頁抓完
    if target_total <= 9999:
        while len(pmids) < target_total:
            retstart = len(pmids)
            retmax = min(5000, target_total - retstart)
            _, next_ids = _fetch_pmid_page(query, retstart=retstart, retmax=retmax)
            if not next_ids:
                break
            pmids.extend(next_ids)
        return list(dict.fromkeys(pmids))[:target_total]

    # 情況 B：若你要全抓且總數超過 9,999 篇 (突破 PubMed 9,999 限制：自動依年份區間切分查詢)
    print("   ⚡ 總數超過 PubMed 單次 9,999 篇上限，啟動「年份分段檢索」突破限制...")
    all_pmids = []
    year_ranges = [
        ("2022", "2026"),
        ("2017", "2021"),
        ("2010", "2016"),
        ("2000", "2009"),
        ("1900", "1999")
    ]
    for y_start, y_end in year_ranges:
        sub_count, sub_ids = _fetch_pmid_page(query, retstart=0, retmax=5000, mindate=y_start, maxdate=y_end)
        all_pmids.extend(sub_ids)
        # 若該年份區間超過 5000 筆，抓第二頁
        if sub_count > 5000:
            _, page2_ids = _fetch_pmid_page(query, retstart=5000, retmax=4999, mindate=y_start, maxdate=y_end)
            all_pmids.extend(page2_ids)
        if max_results and len(all_pmids) >= max_results:
            break

    unique_pmids = list(dict.fromkeys(all_pmids))
    return unique_pmids[:max_results] if max_results else unique_pmids


def fetch_citation_counts_batch(pmids: list[str]) -> dict[str, int]:
    """
    2. ELink：改用 POST 請求，傳入單一批次 (建議 <= 200 篇) 的 PMID 取得被引用次數
    """
    if not pmids:
        return {}

    citation_map = {pmid: 0 for pmid in pmids}
    data = [
        ("dbfrom", "pubmed"),
        ("linkname", "pubmed_pubmed_citedin"),
        ("retmode", "xml")
    ] + [("id", pmid) for pmid in pmids]
    
    if NCBI_API_KEY:
        data.append(("api_key", NCBI_API_KEY))

    resp = requests.post(f"{BASE_URL}/elink.fcgi", data=data, timeout=60)
    resp.raise_for_status()
    time.sleep(SLEEP_INTERVAL)

    root = ET.fromstring(resp.content)
    for linkset in root.findall(".//LinkSet"):
        source_pmid = linkset.findtext("./IdList/Id")
        if source_pmid:
            citing_links = linkset.findall("./LinkSetDb/Link/Id")
            citation_map[source_pmid] = len(citing_links)

    return citation_map


def fetch_pubmed_xml_batch(pmids: list[str]) -> ET.Element:
    """
    3. EFetch：改用 POST 請求，批次下載文獻完整 XML
    """
    data = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    if NCBI_API_KEY:
        data["api_key"] = NCBI_API_KEY

    resp = requests.post(f"{BASE_URL}/efetch.fcgi", data=data, timeout=60)
    resp.raise_for_status()
    time.sleep(SLEEP_INTERVAL)
    return ET.fromstring(resp.content)