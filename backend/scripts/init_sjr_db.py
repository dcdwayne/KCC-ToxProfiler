# backend/scripts/init_sjr_db.py
import sys
from pathlib import Path
import pandas as pd

# 將 backend 目錄加入 Python 路徑
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.database import engine, SessionLocal, Base
from app.models.journal import JournalRanking

# CSV 檔案路徑 (請確保檔案放在 backend/data/ 目錄下)
CSV_FILE_PATH = BASE_DIR / "data" / "scimagojr_2025.csv"
RANKING_YEAR = 2025

def init_journal_rankings():
    if not CSV_FILE_PATH.exists():
        print(f"❌ 找不到 CSV 檔案：{CSV_FILE_PATH}")
        print("請先從 Scimago 下載全球排名 CSV，並命名為 scimagojr_2025.csv 放入 backend/data/ 資料夾！")
        return

    print("⏳ 正在讀取並清洗 Scimago CSV 資料...")
    # 1. Scimago CSV 使用分號 (;) 作為分隔符
    df = pd.read_csv(CSV_FILE_PATH, sep=';', low_memory=False)

    # 2. 只保留有效排名 (Q1 ~ Q4) 且有 ISSN 的期刊
    df = df[df['SJR Best Quartile'].isin(['Q1', 'Q2', 'Q3', 'Q4'])].copy()
    df = df[df['Issn'].notna() & (df['Issn'] != '-')].copy()

    # 3. 處理歐洲小數點格式 (將 "32,577" 轉成 32.577)
    df['SJR'] = (
        df['SJR'].astype(str)
        .str.replace(',', '.', regex=False)
        .replace({'': None, 'nan': None, '-': None})
    )
    df['SJR'] = pd.to_numeric(df['SJR'], errors='coerce')

    # 4. 拆解多組 ISSN (例如 "15227278, 0300483X" -> 拆成兩列獨立資料)
    df['Issn'] = df['Issn'].astype(str).str.split(',')
    df = df.explode('Issn')
    
    # 清除空白與連字號 (-)，統一變成 8 碼純字串
    df['Issn'] = df['Issn'].str.strip().str.replace('-', '', regex=False)
    df = df[df['Issn'] != '']

    # 5. 若有重複的 ISSN，保留排名最前面的一筆
    df = df.drop_duplicates(subset=['Issn'], keep='first')

    # 6. 準備轉換為資料庫格式
    records = []
    for _, row in df.iterrows():
        records.append({
            "issn": row['Issn'],
            "journal_title": str(row['Title']).strip(),
            "quartile": row['SJR Best Quartile'],
            "sjr_score": float(row['SJR']) if pd.notna(row['SJR']) else None,
            "h_index": int(row['H index']) if pd.notna(row['H index']) else None,
            "ranking_year": RANKING_YEAR
        })

    # 7. 建立資料表並批次寫入 PostgreSQL
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 清空舊資料重新匯入，避免重複執行時衝突
        db.query(JournalRanking).delete()
        
        # 使用 bulk_insert_mappings 高速批次寫入數萬筆資料
        db.bulk_insert_mappings(JournalRanking, records)
        db.commit()
        print(f"✅ [journal_rankings] 匯入完成！共寫入 {len(records)} 筆獨立 ISSN 期刊排名資料。")
    except Exception as e:
        db.rollback()
        print(f"❌ 匯入失敗：{e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_journal_rankings()