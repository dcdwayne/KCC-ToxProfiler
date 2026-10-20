<template>
  <div class="dashboard-view">
    <div class="dashboard-header">
      <div class="header-left-group">
        <span class="section-subtitle">MECHANISM ATTRIBUTION / WEIGHT OF EVIDENCE</span>
        <span class="legend-hint">💡 標題括號數字如 <strong>(12)</strong> 代表高影響力期刊 (Q1/Q2) 文獻篇數</span>
      </div>
      <span class="model-tag">10 Key Characteristics Model</span>
    </div>
    
    <div class="kcc-grid">
      <div v-for="kcc in kccData" :key="kcc.id" class="kcc-card" :class="{ 'card-empty': kcc.score === 0 }">
        <!-- 卡片頂部：KC 編號 + 名稱 (high_impact_papers) + 證據強度標籤 -->
        <div class="card-top">
          <div class="kc-top-meta">
            <span class="kc-id">KC {{ kcc.id }}</span>
            <span class="total-papers-tag" title="納入統合分析之總文獻篇數">
              共 {{ kcc.paper_count ?? 0 }} 篇
            </span>
          </div>

          <h4 class="kc-title" :title="`高影響力期刊 (Q1/Q2): ${kcc.high_impact_papers ?? 0} 篇`">
            {{ kcc.title }}
            <span class="high-impact-count">({{ kcc.high_impact_papers ?? 0 }})</span>
          </h4>
          
          <div class="evidence-badge" :class="getEvidenceClass(kcc.evidence)">
            {{ kcc.evidence.toUpperCase() }} EVIDENCE
          </div>
        </div>

        <!-- 卡片中段：實驗模型分佈小標籤 (Human / In Vivo / In Vitro) -->
        <div class="model-mini-row" v-if="kcc.model_breakdown">
          <span class="mini-pill pill-human" :class="{ 'dimmed': !kcc.model_breakdown['Human'] }">
            Cohort: {{ kcc.model_breakdown['Human'] || 0 }}
          </span>
          <span class="mini-pill pill-invivo" :class="{ 'dimmed': !kcc.model_breakdown['In Vivo'] }">
            In Vivo: {{ kcc.model_breakdown['In Vivo'] || 0 }}
          </span>
          <span class="mini-pill pill-invitro" :class="{ 'dimmed': !kcc.model_breakdown['In Vitro'] }">
            In Vitro: {{ kcc.model_breakdown['In Vitro'] || 0 }}
          </span>
        </div>
        
        <!-- 卡片底部：證據強度文字、百分比與動態進度條 -->
        <div class="card-bottom">
          <div class="status-text">
            <span :class="getEvidenceTextClass(kcc.evidence)">{{ kcc.statusText }}</span>
            <span class="percentage">{{ kcc.score }}%</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :class="getEvidenceClass(kcc.evidence)" 
              :style="{ width: kcc.score + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  kccData: {
    type: Array,
    default: () => []
  }
})

const getEvidenceClass = (level) => {
  switch (level) {
    case 'High': return 'bg-high'
    case 'Moderate': return 'bg-moderate'
    case 'Weak': return 'bg-weak'
    default: return 'bg-inadequate'
  }
}

const getEvidenceTextClass = (level) => {
  switch (level) {
    case 'High': return 'text-high'
    case 'Moderate': return 'text-moderate'
    case 'Weak': return 'text-weak'
    default: return 'text-inadequate'
  }
}
</script>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 8px;
}

.header-left-group {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.section-subtitle {
  font-size: 14px;
  font-weight: 800;
  color: #444;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.legend-hint {
  font-size: 12.5px;
  color: var(--dark-color);
  background-color: var(--light-color);
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 600;
}

.model-tag {
  font-size: 12px;
  color: #666;
  font-weight: bold;
}

.kcc-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.kcc-card {
  background-color: #ffffff;
  border: 1px solid #eaeaea;
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 195px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.03);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kcc-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.07);
}

.kcc-card.card-empty {
  background-color: #fcfcfc;
  opacity: 0.85;
}

.kc-top-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kc-id {
  font-size: 12px;
  color: #666;
  font-weight: 800;
}

.total-papers-tag {
  font-size: 11px;
  color: #555;
  background-color: #f1f3f5;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 700;
}

.kc-title {
  font-size: 13.5px;
  font-weight: 800;
  margin: 6px 0 10px 0;
  color: #1a2533;
  line-height: 1.3;
  min-height: 34px;
}

.high-impact-count {
  color: var(--dark-color);
  font-weight: 900;
  margin-left: 2px;
}

.evidence-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
}

/* 實驗模型分佈小標籤列 */
.model-mini-row {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin: 12px 0 10px 0;
}

.mini-pill {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.pill-human {
  background-color: #fdecea;
  color: #c0392b;
}

.pill-invivo {
  background-color: #fef5e7;
  color: #d68910;
}

.pill-invitro {
  background-color: #f2f4f4;
  color: #566573;
}

.mini-pill.dimmed {
  opacity: 0.4;
}

.card-bottom {
  margin-top: auto;
}

.status-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 800;
  margin-bottom: 5px;
}

.percentage {
  font-size: 13px;
  color: #333;
  font-weight: 900;
}

.progress-bar {
  height: 5px;
  background-color: #eee;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.6s ease;
}

.bg-high { background-color: #ff5252; }
.bg-moderate { background-color: #ffca28; color: #333 !important; }
.bg-weak { background-color: #90a4ae; }
.bg-inadequate { background-color: #e0e0e0; color: #777 !important; }

.text-high { font-size: 12px; color: #ff5252; }
.text-moderate { font-size: 12px; color: #f57f17; }
.text-weak { font-size: 12px; color: #607d8b; }
.text-inadequate { font-size: 12px; color: #9e9e9e; }
</style>