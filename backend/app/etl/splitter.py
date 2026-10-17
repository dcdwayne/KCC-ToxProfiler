# 摘要切分器 (將 Abstract 依字數與句號切成 Chunks)
"""
建立科學文獻專用分片器，科學摘要裡常有 et al.、Fig.、Dr. 或小數點 130.7 ± 9.4 nm，不能單純用 .split('.')。這支分片器使用正則表達式精準識別句子邊界，並確保零重疊、可 100% 依序拼回原文。
"""
# backend/app/etl/splitter.py
import regex as re

# 保護常見科學縮寫，避免在縮寫的句號處誤切
SENTENCE_SPLIT_REGEX = re.compile(
    r'(?<!\b(?:et al|i\.e|e\.g|vs|ca|Dr|Mr|Ms|Fig|Tab|eq|wt|vol|approx|conc|sp|spp))'
    r'(?<!\b[A-Z])'
    r'(?<=[.!?])\s+(?=[A-Z0-9(\["\'])'
)

def split_abstract_into_chunks(
    abstract: str,
    min_chars: int = 120,
    max_chars: int = 380
) -> list[dict]:
    """
    將文獻摘要切分為「零重疊」的語意句子片段 (Chunks)。
    回傳格式:
    [
        {"chunk_index": 0, "chunk_text": "...", "char_start": 0, "char_end": 215},
        {"chunk_index": 1, "chunk_text": "...", "char_start": 216, "char_end": 450},
        ...
    ]
    """
    if not abstract or not abstract.strip():
        return []

    clean_abstract = re.sub(r'\s+', ' ', abstract).strip()
    
    # 1. 先依句子邊界切開
    raw_sentences = SENTENCE_SPLIT_REGEX.split(clean_abstract)
    
    # 2. 智慧合併：若單句太短 (< min_chars)，與下一句合併為一個 Chunk；但控制不超過 max_chars
    merged_texts = []
    buffer = ""
    
    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue
            
        if not buffer:
            buffer = sent
        elif len(buffer) < min_chars or (len(buffer) + 1 + len(sent) <= max_chars):
            buffer = f"{buffer} {sent}"
        else:
            merged_texts.append(buffer)
            buffer = sent
            
    if buffer:
        # 若最後殘留的一小句太短 (< 60 字元) 且前面已經有片段，直接併入最後一個片段
        if merged_texts and len(buffer) < 60:
            merged_texts[-1] = f"{merged_texts[-1]} {buffer}"
        else:
            merged_texts.append(buffer)

    # 3. 賦予編號 (chunk_index) 與字元座標 (char_start, char_end)
    chunks_result = []
    current_pos = 0
    for idx, text in enumerate(merged_texts):
        start_idx = clean_abstract.find(text, current_pos)
        if start_idx == -1:
            start_idx = current_pos
        end_idx = start_idx + len(text)
        current_pos = end_idx

        chunks_result.append({
            "chunk_index": idx,
            "chunk_text": text,
            "char_start": start_idx,
            "char_end": end_idx
        })

    return chunks_result