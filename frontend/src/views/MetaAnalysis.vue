<template>
  <main class="meta-page">
    <!-- 頂部標題與分數區塊 -->
    <header class="meta-header">
      <div class="header-left">
        <h1 class="main-title">
          證據權重危害辨識統合分析 <span class="title-en">Meta-analysis</span>
        </h1>
        <div class="target-info">
          <span class="label">ANALYSIS TARGET (CAS: {{ metaInfo.cas_number }})</span>
          <h2 class="target-name">{{ metaInfo.chemical_name }}</h2>
          <span class="curated-date">Curated: {{ metaInfo.curated_date }}</span>
        </div>
      </div>
      
      <!-- 右側 Hazard Score 徽章 -->
      <div class="score-badge" :class="getRiskBorderClass(metaInfo.risk_level)">
        <span class="score-label">HAZARD SCORE</span>
        <span class="score-value">{{ metaInfo.hazard_score ?? '--' }}</span>
        <span class="score-risk" :class="getRiskTextClass(metaInfo.risk_level)">
          {{ metaInfo.risk_level }}
        </span>
      </div>
    </header>

    <!-- 頁籤導覽列：當報告尚未生成完畢時，民眾版本與專家版本反灰不可按 -->
    <nav class="tab-nav">
      <button class="info-btn" title="檢視 10 KCC 證據權重儀表板與 AI 雙版本評估報告">!</button>

      <button 
        class="action-btn tab-btn" 
        :class="{ active: activeTab === 'Dashboard' }" 
        @click="switchTab('Dashboard')"
      >
        分析成果儀表板
      </button>

      <button 
        class="action-btn tab-btn" 
        :class="{ active: activeTab === 'Public', disabled: !hasReports }" 
        :disabled="!hasReports"
        @click="switchTab('Public')"
        :title="hasReports ? '點擊檢視民眾版科普風險報告' : 'AI 報告正在背景生成中，完成後即可點擊'"
      >
        民眾版本
        <span v-if="!hasReports" class="generating-tag">(生成中...)</span>
      </button>

      <button 
        class="action-btn tab-btn" 
        :class="{ active: activeTab === 'Expert', disabled: !hasReports }" 
        :disabled="!hasReports"
        @click="switchTab('Expert')"
        :title="hasReports ? '點擊檢視專家版法規毒理報告' : 'AI 報告正在背景生成中，完成後即可點擊'"
      >
        專家版本
        <span v-if="!hasReports" class="generating-tag">(生成中...)</span>
      </button>
    </nav>

    <!-- 內容區域：根據 activeTab 顯示對應組件 -->
    <section class="content-area">
      <MetaDashboard 
        v-if="activeTab === 'Dashboard'" 
        :kccData="kccData" 
      />
      <MetaPublic 
        v-if="activeTab === 'Public' && hasReports" 
        :tabs="publicTabs"
        :chemicalName="metaInfo.chemical_name"
        :hazardScore="metaInfo.hazard_score"
      />
      <MetaExpert 
        v-if="activeTab === 'Expert' && hasReports" 
        :tabs="expertTabs"
        :chemicalName="metaInfo.chemical_name"
        :hazardScore="metaInfo.hazard_score"
      />
    </section>
  </main>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import MetaPublic from '../components/MetaPublic.vue'
import MetaExpert from '../components/MetaExpert.vue'
import MetaDashboard from '../components/MetaDashboard.vue'

const route = useRoute()
const API_BASE_URL = `http://${window.location.hostname}:8000/api`

// 預設先打開「分析成果儀表板」
const activeTab = ref('Dashboard')

const evaluationId = ref(Number(route.query.eval_id || localStorage.getItem('current_evaluation_id') || 1))

const metaInfo = reactive({
  chemical_name: 'LOADING...',
  cas_number: '',
  curated_date: '',
  hazard_score: null,
  risk_level: 'CALCULATING',
  status: 'REVIEWING'
})

const kccData = ref([])
const hasReports = ref(false)
const publicTabs = ref([])
const expertTabs = ref([])

let pollTimer = null

const switchTab = (tabName) => {
  if ((tabName === 'Public' || tabName === 'Expert') && !hasReports.value) {
    return
  }
  activeTab.value = tabName
}

const getRiskBorderClass = (level) => {
  if (level === 'MODERATE RISK') return 'border-moderate'
  if (level === 'LOW RISK') return 'border-low'
  return 'border-high'
}

const getRiskTextClass = (level) => {
  if (level === 'MODERATE RISK') return 'risk-moderate'
  if (level === 'LOW RISK') return 'risk-low'
  return 'risk-high'
}

// API 1: 取得儀表板與基礎分數資料 (瞬間返回)
const fetchDashboardData = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/meta/${evaluationId.value}/dashboard`)
    if (!res.ok) throw new Error('無法取得儀表板資料')
    const data = await res.json()

    metaInfo.chemical_name = data.chemical_name
    metaInfo.cas_number = data.cas_number
    metaInfo.curated_date = data.curated_date
    metaInfo.hazard_score = data.hazard_score
    metaInfo.risk_level = data.risk_level
    metaInfo.status = data.status
    kccData.value = data.kcc_data || []
  } catch (err) {
    console.error('載入儀表板資料失敗:', err)
  }
}

// API 2: 取得民眾版與專家版分段報告資料
const fetchReportsData = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/meta/${evaluationId.value}/reports`)
    if (!res.ok) throw new Error('無法取得報告資料')
    const data = await res.json()

    metaInfo.chemical_name = data.chemical_name
    metaInfo.cas_number = data.cas_number
    metaInfo.curated_date = data.curated_date
    metaInfo.hazard_score = data.hazard_score
    metaInfo.risk_level = data.risk_level
    metaInfo.status = data.status

    if (data.has_reports && data.public_tabs.length > 0 && data.expert_tabs.length > 0) {
      hasReports.value = true
      publicTabs.value = data.public_tabs
      expertTabs.value = data.expert_tabs
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    } else {
      hasReports.value = false
    }
  } catch (err) {
    console.error('載入報告資料失敗:', err)
  }
}

onMounted(async () => {
  await fetchDashboardData()
  await fetchReportsData()

  // 若報告尚在背景生成中，每 3 秒自動檢查一次，生成完畢後立即解鎖按鈕
  if (!hasReports.value) {
    pollTimer = setInterval(fetchReportsData, 3000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.meta-page { max-width: 1200px; margin: 16px auto 40px auto; padding: 0 20px; }

.meta-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.main-title { font-family: 'Georgia', serif; font-size: 38px; font-weight: 900; margin: 0 0 8px 0; letter-spacing: -1px; color: #222; }
.title-en { color: #e74c3c; }
.target-info { display: flex; flex-direction: column; gap: 4px; }
.label { font-size: 12px; color: #555; letter-spacing: 1px; font-weight: bold; }
.target-name { font-size: 28px; margin: 0; color: #222; font-weight: 700; letter-spacing: 1px; }
.curated-date { font-size: 12px; color: #555; font-weight: 600; }

.score-badge {
  background-color: #1a1e29;
  color: #fff;
  border-bottom: 6px solid #e74c3c;
  border-radius: 6px;
  padding: 16px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 8px 16px rgba(0,0,0,0.15);
  min-width: 100px;
}
.border-high { border-bottom-color: #e74c3c; }
.border-moderate { border-bottom-color: #f39c12; }
.border-low { border-bottom-color: #2ecc71; }

.score-label { font-size: 12px; letter-spacing: 1px; color: #aaa; font-weight: bold; }
.score-value { font-size: 50px; font-weight: bold; line-height: 1.2; margin: 4px 0; }
.score-risk { font-size: 12px; color: #e74c3c; font-weight: bold; letter-spacing: 1px; }
.risk-high { color: #e74c3c; }
.risk-moderate { color: #f39c12; }
.risk-low { color: #2ecc71; }

.tab-nav { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
.info-btn {
  width: 26px; height: 26px; border-radius: 50%; border: 1.5px solid var(--dark-color);
  background-color: var(--light-color); color: var(--dark-color); font-weight: 900; cursor: help;
}

.action-btn.tab-btn {
  background-color: #ffffff;
  color: #333;
  border: 1px solid var(--dark-color);
  padding: 8px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 140px;
}

.action-btn.tab-btn.active,
.action-btn.tab-btn:hover:not(:disabled) {
  background-color: var(--dark-color);
  color: #ffffff;
}

.action-btn.tab-btn:active:not(:disabled) {
  opacity: 0.8;
  transform: scale(0.96);
  transition: all 0.1s ease;
}

/* 報告尚未生成完畢時的反灰禁用樣式 */
.action-btn.tab-btn.disabled,
.action-btn.tab-btn:disabled {
  background-color: #e2e8f0;
  color: #94a3b8;
  border-color: #cbd5e1;
  cursor: not-allowed;
  transform: none;
}

.generating-tag {
  font-size: 12px;
  font-weight: normal;
  margin-left: 4px;
}

.content-area {
  background-color: #f8f9fa;
  padding: 24px;
  border-radius: 12px;
  min-height: 460px;
}
</style>