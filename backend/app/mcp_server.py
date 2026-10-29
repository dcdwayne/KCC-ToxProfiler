# backend/app/mcp_server.py
# from mcp.server.fastmcp import FastMCP
from app.database import SessionLocal
from app.models import Evaluation

# 初始化 FastMCP Server
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("KCC-ToxProfiler-MCP")
except ImportError:
    # 若 FastAPI 容器內未安裝 mcp 套件，提供輕量級裝飾器相容，讓 /api/chat 直接調用函式
    class _DummyMCP:
        def tool(self):
            return lambda func: func
        def run(self):
            pass
    mcp = _DummyMCP()

# 中英文對照表，方便按鈕顯示中文名稱
CAS_TO_ZH = {
    "50-32-8": "苯駢芘",
    "79-06-1": "丙烯醯胺",
    "117-81-7": "塑化劑",
    "1746-01-6": "戴奧辛",
    "335-67-1": "全氟辛酸",
}


@mcp.tool()
def get_selected_chemicals() -> list[dict]:
    """
    取得目前在歷史紀錄管理頁面中被勾選 (is_selected = True) 的所有化學物質清單。
    用於向使用者提供可選擇的關注化學物質按鈕。
    """
    db = SessionLocal()
    try:
        rows = (
            db.query(Evaluation)
            .filter(Evaluation.is_selected == True)
            .order_by(Evaluation.id.desc())
            .all()
        )
        result = []
        for r in rows:
            zh_name = (r.filter_criteria or {}).get("chemical_zh") or CAS_TO_ZH.get(r.cas_number, r.chemical_name)
            result.append({
                "evaluation_id": r.id,
                "cas_number": r.cas_number,
                "chemical_name_en": r.chemical_name,
                "chemical_name_zh": zh_name,
                "hazard_score": r.hazard_score,
                "risk_level": r.risk_level,
                "status": r.status
            })
        return result
    finally:
        db.close()


@mcp.tool()
def get_chemical_evaluation_data(chemical_query: str, role: str = "一般民眾") -> dict:
    """
    根據使用者選擇的化學物質名稱 (中文或英文或 CAS) 與角色 ('一般民眾' 或 '專家')，
    取得 evaluations 表中 is_selected = True 的完整評估報告與 10 KCC 分數。
    """
    db = SessionLocal()
    try:
        rows = db.query(Evaluation).filter(Evaluation.is_selected == True).all()
        target = None
        for r in rows:
            zh_name = (r.filter_criteria or {}).get("chemical_zh") or CAS_TO_ZH.get(r.cas_number, "")
            if (
                chemical_query in zh_name
                or chemical_query.lower() in (r.chemical_name or "").lower()
                or chemical_query == r.cas_number
            ):
                target = r
                break

        if not target:
            return {"found": False, "message": f"目前知識庫中並未勾選「{chemical_query}」的評估紀錄。"}

        zh_name = (target.filter_criteria or {}).get("chemical_zh") or CAS_TO_ZH.get(target.cas_number, target.chemical_name)
        report_text = target.expert_report if role == "專家" else target.public_report

        return {
            "found": True,
            "evaluation_id": target.id,
            "chemical_name_zh": zh_name,
            "chemical_name_en": target.chemical_name,
            "cas_number": target.cas_number,
            "hazard_score": target.hazard_score,
            "risk_level": target.risk_level,
            "kcc_scores": target.kcc_scores,
            "role_selected": role,
            "report_content": report_text or "該版本報告尚未生成完畢。",
            "available_topics": (
                ["化學物質介紹", "主要暴露途徑", "KCC 結論與危害分數"]
                if role == "一般民眾"
                else [
                    "Margin of Exposure (MoE) 與劑量效應評估",
                    "Critical Effects (關鍵毒理與臨界效應)",
                    "10 個關鍵致癌機轉 (10 KCCs) 分析成果詳解",
                    "綜合危害分數 (Hazard Score) 與證據權重結論"
                ]
            )
        }
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()