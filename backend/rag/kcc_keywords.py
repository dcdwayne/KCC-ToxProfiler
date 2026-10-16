# 集中定義 10 KCC 的專屬擴展關鍵字字典 (如 DNA adduct 等)
# 未來教授如果建議微調某個 KCC 的檢索關鍵字，你只要打開 rag/kcc_keywords.py
"""
KCC 1 Genotoxicity、DNA addcut、Single-Strand Breaks、Double-Strand Breaks、Interstrand Crosslinks
1.FastAPI 收到 KCC 1 的任務後，把這 5 個關鍵字分別透過 Embedding 模型轉成 5 組向量。
2.將這 5 組向量丟進資料庫計算餘弦相似度。
3.只要文獻切片與這 5 組向量中任何一組的相似度超過你設定的閾值（例如 0.75），就將該切片召回。
"""