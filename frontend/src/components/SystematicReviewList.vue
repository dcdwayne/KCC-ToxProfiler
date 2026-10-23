<template>
  <div class="paper-row">
    <div class="row-left">
      <span class="index">{{ index }}.</span>
      <h5 class="paper-title" @click="$emit('view-details', paper)" title="點擊查看完整標題與摘要細節">
        {{ paper.title }}
      </h5>
      <!-- 資料來源視覺化標注框框 (白字) -->
      <span class="model-badge" :class="getModelClass(paper.model)">
        {{ paper.model }}
      </span>
    </div>

    <div class="row-right">
      <!-- 期刊排名視覺化標注框框 -->
      <span class="rank-badge" :class="getRankClass(paper.quartile)">
        {{ paper.quartile }}
      </span>

      <!-- 適配度百分比 -->
      <span class="rerank-text">
        適配度 <strong>{{ paper.rerank_pct }}%</strong>
      </span>

      <!-- 刪除按鈕 -->
      <button class="delete-btn" @click="$emit('remove-paper', paper)" title="從 Evidence Pool 中移除">
        X
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  index: Number,
  paper: Object
})
defineEmits(['view-details', 'remove-paper'])

// 資料來源顏色分類：cohort(紅)、in vivo(黃)、in vitro(淺灰)，統一白字
const getModelClass = (model) => {
  const m = (model || '').toLowerCase()
  if (m === 'cohort') return 'badge-cohort'
  if (m === 'in vivo') return 'badge-invivo'
  if (m === 'in vitro') return 'badge-invitro'
  return 'badge-unknown'
}

// 期刊排名視覺框顏色
const getRankClass = (quartile) => {
  if (quartile === 'Q1') return 'rank-q1'
  if (quartile === 'Q2') return 'rank-q2'
  if (quartile === 'Q3' || quartile === 'Q4') return 'rank-q34'
  return 'rank-unranked'
}
</script>

<style scoped>
.paper-row {
  background-color: #ffffff; 
  border: 1px solid #ffffff;
  border-radius: 12px;
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.paper-row:hover {
  background-color: #f4f8f9;
  transform: translateY(-1px);
}

.row-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}

.index {
  font-weight: bold;
  font-size: 16px;
  color: #444;
  min-width: 24px;
}

.paper-title {
  margin: 0;
  font-size: 16px;
  color: #333;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 430px;
}

.paper-title:hover {
  color: var(--dark-color);
  text-decoration: underline;
}

/* 資料來源視覺化標注框 (統一白字) */
.model-badge {
  color: #ffffff;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: bold;
  letter-spacing: 0.3px;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge-cohort {
  background-color: #e74c3c; /* 紅色 */
}

.badge-invivo {
  background-color: #f39c12; /* 黃/琥珀色 (搭配白字清晰易讀) */
}

.badge-invitro {
  background-color: #95a5a6; /* 淺灰色 */
}

.badge-unknown {
  background-color: #bdc3c7;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

/* 期刊排名視覺化標注框框 */
.rank-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 800;
  border: 1px solid var(--dark-color);
  color: var(--dark-color);
  background-color: var(--light-color);
  min-width: 42px;
  text-align: center;
}

.rank-q1 {
  background-color: var(--dark-color);
  color: #ffffff;
  border-color: var(--dark-color);
}

.rank-q2 {
  background-color: #e0f2f1;
  color: var(--dark-color);
  border-color: var(--primary-color);
}

.rank-q34 {
  background-color: #f5f5f5;
  color: #666;
  border-color: #ccc;
}

.rank-unranked {
  background-color: #fafafa;
  color: #999;
  border-color: #ddd;
  font-size: 12px;
}

.rerank-text {
  color: #444;
  font-size: 14px;
  min-width: 88px;
  text-align: right;
}

.rerank-text strong {
  color: var(--dark-color);
  font-size: 15px;
}

.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid #666;
  background-color: transparent;
  cursor: pointer;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.delete-btn:hover {
  background-color: #ffebee;
  color: #c62828;
  border-color: #c62828;
}
</style>