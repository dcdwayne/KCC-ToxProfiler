<template>
  <div class="dashboard-view">
    <div class="dashboard-header">
      <span class="section-subtitle">MECHANISM ATTRIBUTION / WEIGH OF EVIDENCE</span>
      <span class="model-tag">10 Key Characteristics Model</span>
    </div>
    
    <div class="kcc-grid">
      <div v-for="kcc in kccData" :key="kcc.id" class="kcc-card">
        <div class="card-top">
          <span class="kc-id">KC {{ kcc.id }}</span>
          <h4 class="kc-title">{{ kcc.title }}</h4>
          
          <div v-if="kcc.evidence !== 'Inadequate'" class="evidence-badge" :class="getEvidenceClass(kcc.evidence)">
            {{ kcc.evidence.toUpperCase() }} EVIDENCE
          </div>
        </div>
        
        <div class="card-bottom">
          <div class="status-text">
            <span :class="getEvidenceTextClass(kcc.evidence)">{{ kcc.statusText }}</span>
            <span class="percentage">{{ kcc.score }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :class="getEvidenceClass(kcc.evidence)" :style="{ width: kcc.score + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const getEvidenceClass = (level) => {
  switch(level) {
    case 'High': return 'bg-high';
    case 'Moderate': return 'bg-moderate';
    case 'Weak': return 'bg-weak';
    default: return 'bg-inadequate';
  }
}
const getEvidenceTextClass = (level) => {
  switch(level) {
    case 'High': return 'text-high';
    case 'Moderate': return 'text-moderate';
    case 'Weak': return 'text-weak';
    default: return 'text-inadequate';
  }
}

const kccData = ref([
  { id: '01', title: 'ELECTROPHILIC', evidence: 'High', statusText: 'STRONG', score: 95 },
  { id: '02', title: 'GENOTOXIC', evidence: 'High', statusText: 'STRONG', score: 98 },
  { id: '03', title: 'ALTERS DNA REPAIR', evidence: 'Inadequate', statusText: 'INADEQUATE', score: 25 },
  { id: '04', title: 'EPIGENETIC ALTERATIONS', evidence: 'High', statusText: 'MODERATE', score: 70 },
  { id: '05', title: 'OXIDATIVE STRESS', evidence: 'High', statusText: 'STRONG', score: 92 },
  { id: '06', title: 'CHRONIC INFLAMMATION', evidence: 'Moderate', statusText: 'MODERATE', score: 65 },
  { id: '07', title: 'IMMUNOSUPPRESSIVE', evidence: 'Weak', statusText: 'WEAK', score: 30 },
  { id: '08', title: 'RECEPTOR-MEDIATED EFFECTS', evidence: 'High', statusText: 'MODERATE', score: 75 },
  { id: '09', title: 'IMMORTALIZATION', evidence: 'High', statusText: 'STRONG', score: 90 },
  { id: '10', title: 'CELL PROLIFERATION/DEATH', evidence: 'High', statusText: 'STRONG', score: 94 }
])
</script>

<style scoped>
.dashboard-header { display: flex; justify-content: space-between; margin-bottom: 24px; }
.section-subtitle { font-size: 12px; font-weight: bold; color: #888; letter-spacing: 1.5px; text-transform: uppercase; }
.model-tag { font-size: 12px; color: #bbb; }

.kcc-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.kcc-card { background-color: #fff; border: 1px solid #eee; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; height: 160px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.kc-id { font-size: 10px; color: #aaa; font-weight: bold; }
.kc-title { font-size: 12px; font-weight: 800; margin: 4px 0 12px 0; color: #222; }

.evidence-badge { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #fff; margin-top: auto; }
.card-bottom { margin-top: auto; }
.status-text { display: flex; justify-content: space-between; font-size: 9px; font-weight: bold; margin-bottom: 4px; }
.percentage { color: #888; }
.progress-bar { height: 3px; background-color: #eee; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; }

.bg-high { background-color: #ff5252; } .bg-moderate { background-color: #ffca28; color: #333 !important;} .bg-weak { background-color: #b0bec5; } .bg-inadequate { background-color: #eeeeee; }
.text-high { color: #ff5252; } .text-moderate { color: #f57f17; } .text-weak { color: #78909c; } .text-inadequate { color: #bdbdbd; }
</style>