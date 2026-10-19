<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <!-- 載入中狀態 -->
      <div v-if="loading" class="loading-box">
        正在載入文獻詳細資料與 KCC 命中片段...
      </div>

      <template v-else-if="paperDetail">
        <!-- 頂部列：pub_type + pub_date 與右上角 X -->
        <div class="modal-top-bar">
          <div class="top-meta">
            <span class="pub-type-badge">{{ paperDetail.pub_type }}</span>
            <span class="pub-date">{{ paperDetail.pub_date }}</span>
          </div>
          <button class="close-btn" @click="$emit('close')" title="關閉視窗">✕</button>
        </div>

        <!-- 論文完整標題 -->
        <h2 class="paper-full-title">{{ paperDetail.title }}</h2>

        <!-- 前三位主要作者 -->
        <div class="authors-row" v-if="paperDetail.authors && paperDetail.authors.length > 0">
          <template v-for="(author, idx) in paperDetail.authors" :key="idx">
            <span class="author-name">{{ author }}</span>
            <span v-if="idx < paperDetail.authors.length - 2" class="author-sep">, </span>
            <span v-else-if="idx === paperDetail.authors.length - 2" class="author-sep"> and </span>
          </template>
        </div>

        <!-- 作者機構/單位 (Affiliation) -->
        <p class="affiliation-text">{{ paperDetail.affiliation }}</p>

        <!-- 分隔線 -->
        <hr class="divider" />

        <!-- 資料標籤框 (加入適配度與期刊排名) -->
        <div class="meta-badges-row">
          <span class="info-tag">PMID: {{ paperDetail.pmid }}</span>
          <span class="info-tag">模型: {{ paperDetail.model }}</span>
          <span class="info-tag">期刊排名: {{ paperDetail.quartile }}</span>
          <span class="info-tag">引用次數: {{ paperDetail.citations }}</span>
          <span class="info-tag highlight-tag">適配度: {{ paperDetail.rerank_pct }}%</span>
        </div>

        <!-- 摘要區 (支援滑鼠 Hover 浮現對應的 KCC 關鍵片段) -->
        <div class="abstract-section">
          <div class="abstract-header">
            <h4 class="abstract-title">Abstract</h4>
            <span class="hover-hint">💡 提示：將滑鼠移至標記底色的句子上，可檢視配對到的 KCC 關鍵片段</span>
          </div>

          <div class="abstract-container">
            <span
              v-for="chunk in paperDetail.chunks"
              :key="chunk.chunk_index"
              class="chunk-span"
              :class="{ 'kcc-matched-highlight': chunk.matched_kccs && chunk.matched_kccs.length > 0 }"
            >
              {{ chunk.chunk_text }}{{ ' ' }}

              <!-- 滑鼠 Hover 時浮現的 KCC 關鍵片段 Tooltip -->
              <span
                v-if="chunk.matched_kccs && chunk.matched_kccs.length > 0"
                class="kcc-hover-tooltip"
              >
                <span class="tooltip-header">🎯 對應之 KCC 關鍵特徵片段</span>
                <span
                  v-for="(match, mIdx) in chunk.matched_kccs"
                  :key="mIdx"
                  class="tooltip-item"
                >
                  <strong class="tooltip-code">
                    {{ match.kcc_code }}
                    (適配度: {{ Math.round(match.rerank_score * 100) }}% | 餘弦相似度: {{ (match.cosine_score * 100).toFixed(1) }}%)
                  </strong>
                  <span class="tooltip-query">{{ match.query_text }}</span>
                </span>
              </span>
            </span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
defineProps({
  paperDetail: Object,
  loading: Boolean
})
defineEmits(['close'])
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0, 0, 0, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background-color: #ffffff;
  width: 95%;
  max-width: 820px;
  max-height: 85vh;
  border-radius: 16px;
  padding: 28px 36px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  overflow-y: auto;
  position: relative;
}

.loading-box {
  padding: 60px 20px;
  text-align: center;
  font-size: 16px;
  font-weight: bold;
  color: var(--dark-color);
}

/* 頂部列：pub_type + pub_date 與關閉按鈕 */
.modal-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.top-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pub-type-badge {
  background-color: #f0f2f5;
  color: #4a5568;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.pub-date {
  color: #2d3748;
  font-size: 14px;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  color: #4a5568;
  line-height: 1;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f0f2f5;
  color: #000;
}

/* 論文完整大標題 */
.paper-full-title {
  margin: 0 0 14px 0;
  font-size: 24px;
  line-height: 1.35;
  color: #1a2533;
  font-weight: 700;
}

/* 前三位作者 */
.authors-row {
  margin-bottom: 12px;
  font-size: 15px;
  color: #2d3748;
}

.author-name {
  text-decoration: underline;
  text-underline-offset: 3px;
  font-weight: 500;
}

.author-sep {
  color: #4a5568;
}

/* 作者機構 Affiliation */
.affiliation-text {
  margin: 0 0 18px 0;
  font-size: 13.5px;
  line-height: 1.5;
  color: #4a5568;
}

.divider {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 16px 0 20px 0;
}

/* 標籤列 */
.meta-badges-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 22px;
}

.info-tag {
  background-color: #d8f0f4;
  color: #2b6cb0;
  color: var(--dark-color);
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13.5px;
  font-weight: 700;
}

.info-tag.highlight-tag {
  background-color: var(--dark-color);
  color: #ffffff;
}

/* Abstract 區塊 */
.abstract-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.abstract-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #1a2533;
}

.hover-hint {
  font-size: 12.5px;
  color: #666;
  font-weight: bold;
}

.abstract-container {
  line-height: 1.85;
  color: #2d3748;
  font-size: 15.5px;
  text-align: justify;
}

.chunk-span {
  position: relative;
  transition: background-color 0.2s ease;
}

/* 命中 KCC 的句子螢光筆標記 */
.kcc-matched-highlight {
  background-color: #fff3bf;
  border-bottom: 2px solid #f59f00;
  padding: 2px 4px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.kcc-matched-highlight:hover {
  background-color: #ffe066;
}

/* 滑鼠 Hover 時彈出的 KCC 關鍵片段視窗 */
.kcc-hover-tooltip {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  left: 0;
  bottom: calc(100% + 10px);
  width: 420px;
  max-width: 80vw;
  background-color: #1a1e29;
  color: #ffffff;
  padding: 14px 16px;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
  z-index: 2000;
  transition: opacity 0.2s ease, transform 0.2s ease;
  transform: translateY(4px);
  pointer-events: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  line-height: 1.45;
}

.kcc-matched-highlight:hover .kcc-hover-tooltip {
  visibility: visible;
  opacity: 1;
  transform: translateY(0);
}

.tooltip-header {
  font-size: 12px;
  color: #ffd43b;
  font-weight: 800;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  padding-bottom: 6px;
}

.tooltip-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-code {
  font-size: 13px;
  color: #63e6be;
}

.tooltip-query {
  font-size: 13px;
  color: #f1f3f5;
  font-weight: normal;
}
</style>