<template>
  <div class="history-row" :class="{ 'row-selected': record.is_selected }">
    <!-- 左側：勾選框 + 序號 + 化學物質名稱 -->
    <div class="row-left">
      <label class="checkbox-wrapper" title="勾選作為 FastMCP 回答此化學物質之代表紀錄（每種化學物質限選一筆）">
        <input 
          type="checkbox" 
          :checked="record.is_selected" 
          @change="$emit('toggle-select', record)"
        />
        <span class="custom-Checkmark"></span>
      </label>

      <span class="index">{{ index }}.</span>
      <h5 class="chem-name">{{ record.chemical_name }}</h5>
    </div>

    <!-- 右側：危害等級(分數) + 狀態 + 台灣時間 + 導向 Meta 按鈕 + 刪除 X -->
    <div class="row-right">
      <!-- 1. 危害等級(危害分數)：仿照 Meta 儀表板 紅/黃/灰 設計 -->
      <span class="hazard-badge" :class="getHazardClass(record.risk_level, record.hazard_score)">
        <template v-if="record.hazard_score !== null">
          {{ record.risk_level }} ({{ record.hazard_score }})
        </template>
        <template v-else>
          UNSCORED (--)
        </template>
      </span>

      <!-- 2. 狀態：仿照 Review 頁面 期刊排名 (Q1/Q2/Q3) 設計 -->
      <span class="status-badge" :class="getStatusClass(record.status)">
        {{ record.status }}
      </span>

      <!-- 3. 製作時間 (已轉換為台灣時區 UTC+8) -->
      <span class="created-time">{{ record.created_at_tw }}</span>

      <!-- 4. 導向該評估紀錄的 Meta 頁面圓形圖示按鈕 (放置於刪除 X 前方) -->
      <button 
        class="meta-link-btn" 
        @click="$emit('go-meta', record)" 
        title="前往 Meta-analysis 頁面查看評估成果與報告"
      >
        <!-- 專為統合分析成果設計的「分析圖表 + 跳轉箭頭」SVG Icon -->
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline points="15 3 21 3 21 9" />
          <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
      </button>

      <!-- 5. 刪除叉叉按鈕 -->
      <button 
        class="delete-btn" 
        @click="$emit('delete-record', record)" 
        title="刪除此筆評估紀錄與相關證據資料"
      >
        X
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  index: Number,
  record: Object
})

defineEmits(['toggle-select', 'go-meta', 'delete-record'])

// 危害等級配色：仿照 MetaDashboard.vue 的 High(紅) / Moderate(黃) / Weak & Low(灰)
const getHazardClass = (riskLevel, score) => {
  if (score === null || score === undefined) return 'hazard-unscored'
  if (riskLevel === 'HIGH RISK') return 'hazard-high'
  if (riskLevel === 'MODERATE RISK') return 'hazard-moderate'
  return 'hazard-low'
}

// 狀態配色：仿照 SystematicReviewList.vue 的 Q1(深青色) / Q2(淺青色) / Q34(淺灰)
const getStatusClass = (status) => {
  if (status === 'COMPLETED') return 'status-completed'
  if (status && status.startsWith('GENERATING')) return 'status-generating'
  if (status === 'REVIEWING') return 'status-reviewing'
  return 'status-retrieving'
}
</script>

<style scoped>
.history-row {
  background-color: #ffffff;
  border: 1.5px solid #ffffff;
  border-radius: 12px;
  padding: 13px 22px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  transition: all 0.2s ease;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
  gap: 50px;
}

.history-row:hover {
  background-color: #f4f8f9;
  transform: translateY(-1px);
}

/* 當被勾選為 FastMCP 代表紀錄時，加上細緻的深青色左邊框高亮 */
.history-row.row-selected {
  border-color: var(--primary-color);
  background-color: #f8fdfe;
}

.row-left {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 360px;
  flex-shrink: 0;
}

/* 勾選框樣式 (與圖片一致的圓角方框) */
.checkbox-wrapper {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--dark-color);
  border-radius: 4px;
  margin: 0;
}

.index {
  font-weight: 800;
  font-size: 16px;
  color: #333;
  min-width: 24px;
}

.chem-name {
  margin: 0;
  font-size: 16.5px;
  font-weight: 900;
  color: #1b1e29;
  letter-spacing: 0.5px;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 18px;
  flex: 1;
}

/* 1. 危害等級標籤 (仿照 Meta 儀表板紅/黃/灰設計) */
.hazard-badge {
  display: inline-block;
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.4px;
  width: 150px;
  text-align: center;
}

.hazard-high {
  background-color: #ef5327; /* 如設計圖的鮮明紅橘色 */
  color: #ffffff;
}

.hazard-moderate {
  background-color: #ffca28; /* 儀表板黃色 */
  color: #333333;
}

.hazard-low {
  background-color: #b0bec5; /* 儀表板灰色 */
  color: #ffffff;
}

.hazard-unscored {
  background-color: #e0e0e0;
  color: #777777;
}

/* 2. 狀態標籤 (仿照 Review 頁面 期刊排名 Q1~Q4 設計) */
.status-badge {
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.5px;
  width: 160px;
  text-align: center;
  border: 1px solid var(--dark-color);
}

/* COMPLETED 對應 Q1 深青色底白字 */
.status-completed {
  background-color: var(--dark-color);
  color: #ffffff;
  border-color: var(--dark-color);
}

/* REVIEWING / GENERATING 對應 Q2 淺青底深字 */
.status-reviewing,
.status-generating {
  background-color: #e0f2f1;
  color: var(--dark-color);
  border-color: var(--primary-color);
}

/* RETRIEVING 對應 Q3/Q4 灰底 */
.status-retrieving {
  background-color: #f5f5f5;
  color: #666666;
  border-color: #cccccc;
}

/* 3. 台灣時間 */
.created-time {
  font-size: 15px;
  font-weight: 700;
  color: #1b1e29;
  min-width: 150px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  margin-left: auto;
}

/* 4. 導向 Meta 評估成果頁圓形圖示按鈕 */
.meta-link-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1.5px solid #666;
  background-color: transparent;
  color: #444;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.2s ease;
}

.meta-link-btn:hover {
  background-color: var(--dark-color);
  color: #ffffff;
  border-color: var(--dark-color);
  transform: scale(1.08);
}

/* 5. 刪除按鈕 */
.delete-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1.5px solid #666;
  background-color: transparent;
  color: #333;
  cursor: pointer;
  font-weight: 900;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background-color: #ffebee;
  color: #c62828;
  border-color: #c62828;
  transform: scale(1.08);
}
</style>