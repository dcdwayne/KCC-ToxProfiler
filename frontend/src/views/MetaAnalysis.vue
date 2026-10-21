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

    <!-- 頁籤導覽列：民眾版本與專家版本各自獨立解鎖，並具備流光掃描與 ✨ READY 無到有彈跳特效 -->
    <nav class="tab-nav">
      <button class="info-btn" title="點擊查看使用說明" @click="isGuideOpen = true">!</button>

      <button 
        class="action-btn tab-btn" 
        :class="{ active: activeTab === 'Dashboard' }" 
        @click="switchTab('Dashboard')"
      >
        分析成果儀表板
      </button>

      <!-- 民眾版本按鈕：先跑，完成後立即亮起並觸發 ✨ READY 特效 -->
      <button 
        class="action-btn tab-btn" 
        :class="{
          active: activeTab === 'Public' && hasPublicReport,
          'tab-processing': !hasPublicReport,
          'tab-just-ready': justReadyPublic
        }" 
        :disabled="!hasPublicReport"
        @click="switchTab('Public')"
        :title="hasPublicReport ? '點擊檢視民眾版科普風險報告' : 'AI 正在優先生成民眾版報告，完成後即可點擊'"
      >
        <span v-if="justReadyPublic" class="just-ready-badge">✨ READY</span>
        民眾版本
        <span v-if="!hasPublicReport" class="generating-tag">⏳ 生成中...</span>
      </button>

      <!-- 專家版本按鈕：民眾版跑完後接著跑，完成後觸發 ✨ READY 特效 -->
      <button 
        class="action-btn tab-btn" 
        :class="{
          active: activeTab === 'Expert' && hasExpertReport,
          'tab-pending': !hasExpertReport && !hasPublicReport,
          'tab-processing': !hasExpertReport && hasPublicReport,
          'tab-just-ready': justReadyExpert
        }" 
        :disabled="!hasExpertReport"
        @click="switchTab('Expert')"
        :title="hasExpertReport ? '點擊檢視專家版法規毒理報告' : 'AI 正在背景生成專家版報告，完成後即可點擊'"
      >
        <span v-if="justReadyExpert" class="just-ready-badge">✨ READY</span>
        專家版本
        <span v-if="!hasExpertReport && hasPublicReport" class="generating-tag">⏳ 生成中...</span>
        <span v-else-if="!hasExpertReport" class="generating-tag">(待生成...)</span>
      </button>
    </nav>

    <!-- 內容區域：根據 activeTab 顯示對應組件 -->
    <section class="content-area">
      <MetaDashboard 
        v-if="activeTab === 'Dashboard'" 
        :kccData="kccData" 
      />
      <MetaPublic 
        v-if="activeTab === 'Public' && hasPublicReport" 
        :tabs="publicTabs"
        :chemicalName="metaInfo.chemical_name"
        :hazardScore="metaInfo.hazard_score"
      />
      <MetaExpert 
        v-if="activeTab === 'Expert' && hasExpertReport" 
        :tabs="expertTabs"
        :chemicalName="metaInfo.chemical_name"
        :hazardScore="metaInfo.hazard_score"
      />
    </section>
    <InfoGuideModal :isOpen="isGuideOpen" page="meta" @close="isGuideOpen = false" />
  </main>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import MetaPublic from '../components/MetaPublic.vue'
import MetaExpert from '../components/MetaExpert.vue'
import MetaDashboard from '../components/MetaDashboard.vue'
import InfoGuideModal from '../components/InfoGuideModal.vue'

const isGuideOpen = ref(false)
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

// 拆分為兩個獨立狀態：民眾版與專家版各自獨立解鎖！
const hasPublicReport = ref(false)
const hasExpertReport = ref(false)

// 控制按鈕「從無到有」完成瞬間的翠綠彈跳與 ✨ READY 閃耀特效
const justReadyPublic = ref(false)
const justReadyExpert = ref(false)

const publicTabs = ref([])
const expertTabs = ref([])

let pollTimer = null

const switchTab = (tabName) => {
  if (tabName === 'Public' && !hasPublicReport.value) return
  if (tabName === 'Expert' && !hasExpertReport.value) return
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

// 觸發按鈕「資料準備完成」的閃耀彈跳特效 (持續 1.8 秒)
const triggerButtonReadyEffect = (targetRef) => {
  targetRef.value = true
  setTimeout(() => {
    targetRef.value = false
  }, 1800)
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

// API 2: 取得民眾版與專家版分段報告資料 (支援民眾版先好就先解鎖，且不重複覆寫已載入的報告！)
const fetchReportsData = async (isInitialLoad = false) => {
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

    // 1. 檢查【民眾版本】是否已生成完畢
    if (data.has_public_report && data.public_tabs && data.public_tabs.length > 0) {
      // 關鍵修正：只有當「原本還沒載入過民眾版」時，才寫入 publicTabs 並觸發特效！
      // 避免等待專家版期間每 2 秒輪詢重複覆寫 publicTabs 導致打字機一直重頭開始
      if (!hasPublicReport.value) {
        if (!isInitialLoad) {
          triggerButtonReadyEffect(justReadyPublic)
        }
        publicTabs.value = data.public_tabs
        hasPublicReport.value = true
      }
    } else {
      hasPublicReport.value = false
    }

    // 2. 檢查【專家版本】是否已生成完畢
    if (data.has_expert_report && data.expert_tabs && data.expert_tabs.length > 0) {
      // 同樣只有當「原本還沒載入過專家版」時才寫入 expertTabs
      if (!hasExpertReport.value) {
        if (!isInitialLoad) {
          triggerButtonReadyEffect(justReadyExpert)
        }
        expertTabs.value = data.expert_tabs
        hasExpertReport.value = true
      }
    } else {
      hasExpertReport.value = false
    }

    // 當兩個版本都已經生成完畢時，停止輪詢
    if (hasPublicReport.value && hasExpertReport.value) {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }
  } catch (err) {
    console.error('載入報告資料失敗:', err)
  }
}

onMounted(async () => {
  await fetchDashboardData()
  await fetchReportsData(true)

  // 若民眾版或專家版尚在背景生成中，每 2 秒自動檢查一次，誰先生成完畢就先觸發特效並解鎖！
  if (!hasPublicReport.value || !hasExpertReport.value) {
    pollTimer = setInterval(() => {
      fetchReportsData(false)
    }, 2000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
/* 修改 1：強制鎖定 1200px 寬度，不隨內部打字機字數多寡而收縮 */
.meta-page {
  width: 100%;
  max-width: 1200px;
  min-width: min(1200px, calc(100vw - 40px));
  margin: 16px auto 40px auto;
  padding: 0 20px;
  box-sizing: border-box;
}

.meta-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.main-title {
  color: #1b1e29;
  font-size: 38px;
  margin-top: 0px;
  margin-bottom: 12px;
  font-weight: 900;
  letter-spacing: 1.5px;
  text-shadow: 
    1px 1px 0px #f6d32d,
    2px 2px 0px #f6d32d,
    3px 3px 0px #e25740,
    4px 4px 0px #f6d32d;
}
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
  width: 32px; height: 32px; border-radius: 50%; border: 1px solid var(--dark-color);
  background-color: var(--light-color); color: var(--dark-color); font-weight: 950; cursor: help;
}

.action-btn.tab-btn {
  position: relative;
  background-color: #ffffff;
  color: #333;
  border: 1.5px solid var(--dark-color);
  padding: 10px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1);
  min-width: 155px;
  overflow: hidden;
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

/* 狀態 A：反灰排隊等待中 (例如民眾版還在跑時，專家版處於待生成) */
.action-btn.tab-btn.tab-pending {
  background-color: #e2e8f0;
  color: #94a3b8;
  border-color: #cbd5e1;
  cursor: not-allowed;
  transform: none;
}

/* 狀態 B：目前正由 LLM 生成該版本報告中 (流光掃描呼吸特效) */
.action-btn.tab-btn.tab-processing {
  background: linear-gradient(110deg, #e2e8f0 25%, #f8fafc 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmerScan 1.5s infinite linear;
  border: 1.5px dashed var(--dark-color);
  color: #475569;
  cursor: wait;
  transform: none;
}

@keyframes shimmerScan {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 狀態 C：報告生成完畢瞬間的「無到有」立體彈跳與翠綠光暈特效 */
.action-btn.tab-btn.tab-just-ready {
  animation: kccReadyPop 0.95s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border-color: #10b981 !important;
}

@keyframes kccReadyPop {
  0% {
    transform: scale(0.88);
    background-color: #d1fae5;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  50% {
    transform: scale(1.06);
    box-shadow: 0 0 0 12px rgba(16, 185, 129, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  }
}

.just-ready-badge {
  position: absolute;
  top: 2px;
  right: 5px;
  font-size: 9px;
  font-weight: 900;
  color: #059669;
  background-color: #d1fae5;
  padding: 1px 5px;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

.generating-tag {
  font-size: 12px;
  font-weight: 700;
  margin-left: 4px;
}

/* 修改 2：確保內容區與內部報告組件永遠撐滿 100% 寬度 */
.content-area {
  width: 100%;
  box-sizing: border-box;
  background-color: #f8f9fa;
  padding: 24px;
  border-radius: 12px;
  min-height: 460px;
}
</style>