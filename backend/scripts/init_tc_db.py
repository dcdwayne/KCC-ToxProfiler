# backend/scripts/init_tc_db.py
"""
這支腳本設計了「防呆不重複（Idempotent）」機制：未來你隨時在清單裡新增化學物質或同義詞，直接重複執行這支腳本，它只會把「新加的名稱」寫入資料庫，已經存在的會自動跳過，不會報錯！
"""
import sys
from pathlib import Path

# 將 backend 目錄加入 Python 路徑，確保能正確 import app 模組
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models.chemical import TargetChemical

# =====================================================================
# 👇👇👇 【手動新增區】請在下方清單中新增或修改你要評估的化學物質 👇👇👇
# 格式說明：
# - cas_number: 該化學物質的 CAS 號碼
# - names: 清單中的「第一個名稱」會自動被設為主顯示名稱 (is_primary=True)，
#          後面的名稱都會被當作同義詞/別名，供 PubMed ETL 擴大抓取文獻使用。
#          後面的名稱，包括：常見縮寫、同義詞、括號異體字    
# =====================================================================
CHEMICALS_DATA = [
    {
        "cas_number": "50-32-8",
        "names": [
            "Benzo[a]pyrene",      # 主名稱
            "BaP",                 # 常見縮寫
            "3,4-Benzopyrene",     # 同義詞
            "Benzo(a)pyrene"       # 括號異體字
        ]
    },
    {
        "cas_number": "79-06-1",
        "names": [
            "Acrylamide",
            "2-Propenamide",
            "Acrylic acid amide",
            "Propenamide"
        ]
    },
    {
        "cas_number": "335-67-1",
        "names": [
            "PFOA",
            "Perfluorooctanoic acid"
        ]
    },
    {
        "cas_number": "117-81-7",
        "names": [
            "DEHP",
            "Di(2-ethylhexyl)phthalate"
        ]
    },
    {
        "cas_number": "1746-01-6",
        "names": [
            "TCDD",
            "2,3,7,8-Tetrachlorodibenzo-p-dioxin"
        ]
    },    
    # 💡 若要新增下一個化學物質，請複製上方大括號區塊貼在下面：
    # {
    #     "cas_number": "請輸入CAS號碼",
    #     "names": ["主名稱", "別名1", "別名2"]
    # },
]
# =====================================================================
# 👆👆👆 【手動新增區結束】下面的程式碼負責自動寫入資料庫，無需修改 👆👆👆
# =====================================================================

def init_target_chemicals():
    # 1. 若資料表還不存在，自動在 PostgreSQL 中建立資料表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    added_count = 0
    skipped_count = 0

    try:
        for item in CHEMICALS_DATA:
            cas = item["cas_number"].strip()
            for idx, name in enumerate(item["names"]):
                clean_name = name.strip()
                is_primary_flag = (idx == 0)  # 第一個名字設為主名稱

                # 檢查資料庫是否已經存在這個化學名稱
                exists = db.query(TargetChemical).filter_by(chemical_name=clean_name).first()
                if exists:
                    skipped_count += 1
                    continue

                # 新增紀錄
                new_chem = TargetChemical(
                    cas_number=cas,
                    chemical_name=clean_name,
                    is_primary=is_primary_flag
                )
                db.add(new_chem)
                added_count += 1

        db.commit()
        print(f"✅ [target_chemicals] 匯入完成！新增了 {added_count} 筆名稱，跳過了 {skipped_count} 筆已存在的名稱。")
    except Exception as e:
        db.rollback()
        print(f"❌ 匯入失敗：{e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_target_chemicals()