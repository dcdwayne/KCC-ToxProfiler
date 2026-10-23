<template>
  <div class="report-wrapper">
    <!-- 瀏覽器風格 4 大主題標籤頁 -->
    <div class="browser-tab-bar">
      <button
        v-for="(tab, idx) in tabs"
        :key="tab.id"
        class="folder-tab"
        :class="{ active: activeSubTabIdx === idx }"
        @click="selectSubTab(idx)"
      >
        <span class="tab-dot"></span>
        <span class="tab-title">{{ tab.tab_label }}</span>
      </button>
    </div>

    <!-- 專家報告主視窗 -->
    <div class="report-view">
      <div class="report-header">
        <div class="header-left-meta">
          <span class="section-subtitle">
            REGULATORY TOXICOLOGY SYNTHESIS / 專家版統合分析報告 (移動滑鼠至 APA 引用可檢視 PMID)
          </span>
          <h3 class="current-chapter-title" v-if="currentTab">{{ currentTab.full_title }}</h3>
        </div>

        <div class="header-right-actions">
          <button v-if="isTyping" class="skip-btn" @click="finishTypingImmediately">
            ⚡ 立即顯示全文
          </button>
          <div v-if="isFinished" class="completion-badge">
            <span class="sparkle-icon">✨</span>
            <span>專家版評估報告生成完畢</span>
          </div>
        </div>
      </div>

      <!-- 打字機渲染內容區 (內含 APA 7th 引用與 PMID Hover Tooltip) -->
      <div class="report-content">
        <div class="typewriter-body" v-html="displayedHtml"></div>
        <span v-if="isTyping" class="typing-cursor">▍</span>
      </div>

      <!-- 打字結束後底部的總結高亮特效框 -->
      <transition name="pop-fade">
        <div v-if="isFinished" class="completion-footer-banner">
          <div class="footer-check">✓</div>
          <div class="footer-text">
            <strong>Weight of Evidence (WoE) 專家章節已完整載入：</strong>
            <span>將滑鼠移至內文藍底引用標記（如 <em>(Author et al., Year)</em>）即可直接查閱原始文獻 PMID 編號。</span>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  tabs: {
    type: Array,
    default: () => []
  },
  chemicalName: String,
  hazardScore: Number
})

// =====================================================================
// 👇👇👇 【打字機速度調整區】可在此自由調整專家版打字快慢 👇👇👇
// - TYPEWRITER_INTERVAL_MS: 每隔幾毫秒更新一次畫面 (預設 15 毫秒，數字越小越快)
// - CHARS_PER_TICK: 每次更新吐出幾個字元 (預設 4 個字，因為專家版篇幅較長)
// =====================================================================
const TYPEWRITER_INTERVAL_MS = 15
const CHARS_PER_TICK = 4

const activeSubTabIdx = ref(0)
const displayedHtml = ref('')
const isTyping = ref(false)
const isFinished = ref(false)
let typingTimer = null

const currentTab = computed(() => {
  return props.tabs[activeSubTabIdx.value] || null
})

const startTypewriter = (fullHtml) => {
  if (typingTimer) clearInterval(typingTimer)
  displayedHtml.value = ''
  isFinished.value = false

  if (!fullHtml) {
    isTyping.value = false
    return
  }

  isTyping.value = true
  let cursor = 0
  const totalLen = fullHtml.length

  typingTimer = setInterval(() => {
    let charsAdded = 0
    while (charsAdded < CHARS_PER_TICK && cursor < totalLen) {
      if (fullHtml[cursor] === '<') {
        const closeIdx = fullHtml.indexOf('>', cursor)
        if (closeIdx !== -1) {
          cursor = closeIdx + 1
          continue
        }
      }
      cursor++
      charsAdded++
    }

    displayedHtml.value = fullHtml.slice(0, cursor)

    if (cursor >= totalLen) {
      clearInterval(typingTimer)
      typingTimer = null
      isTyping.value = false
      isFinished.value = true
    }
  }, TYPEWRITER_INTERVAL_MS)
}

const finishTypingImmediately = () => {
  if (typingTimer) {
    clearInterval(typingTimer)
    typingTimer = null
  }
  if (currentTab.value) {
    displayedHtml.value = currentTab.value.content_html
  }
  isTyping.value = false
  isFinished.value = true
}

const selectSubTab = (idx) => {
  if (activeSubTabIdx.value === idx) return
  activeSubTabIdx.value = idx
}

// 關鍵修正：只監聽 content_html 實際字串內容是否改變 (newHtml !== oldHtml)
// 就算父組件重新渲染，只要章節內容一樣，打字機就絕對不會被中斷或重跑！
watch(
  () => currentTab.value?.content_html,
  (newHtml, oldHtml) => {
    if (newHtml && newHtml !== oldHtml) {
      startTypewriter(newHtml)
    }
  }
)

onMounted(() => {
  if (currentTab.value) {
    startTypewriter(currentTab.value.content_html)
  }
})

onUnmounted(() => {
  if (typingTimer) clearInterval(typingTimer)
})
</script>

<style scoped>
/* 鎖定 100% 滿版寬度，防止左右伸縮晃動 */
.report-wrapper {
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* 瀏覽器式無叉叉標籤列 */
.browser-tab-bar {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  background-color: #1a1e29;
  padding: 10px 14px 0 14px;
  border-radius: 12px 12px 0 0;
  overflow-x: auto;
  width: 100%;
  box-sizing: border-box;
}

.folder-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: rgba(255, 255, 255, 0.08);
  color: #b0bec5;
  border: none;
  padding: 10px 20px;
  border-radius: 10px 10px 0 0;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.folder-tab:hover:not(.active) {
  background-color: rgba(255, 255, 255, 0.16);
  color: #ffffff;
}

.folder-tab.active {
  background-color: #ffffff;
  color: #1a1e29;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
}

.tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-color);
}

.folder-tab.active .tab-dot {
  background-color: #e74c3c;
}

/* 報告主體視窗 */
.report-view {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  border-top: none;
  border-left: 4px solid var(--dark-color);
  border-radius: 0 0 12px 12px;
  padding: 28px 36px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.04);
  min-height: 380px;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid #edf2f7;
  padding-bottom: 16px;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap;
}

.section-subtitle {
  font-size: 12px;
  font-weight: 800;
  color: #888;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  display: block;
  margin-bottom: 6px;
}

.current-chapter-title {
  margin: 0;
  font-size: 22px;
  color: #1a2533;
  font-weight: 800;
}

.skip-btn {
  background-color: var(--light-color);
  color: var(--dark-color);
  border: 1px solid var(--primary-color);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.skip-btn:hover {
  background-color: var(--dark-color);
  color: #fff;
}

.completion-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #e6fcf5 0%, #c3fae8 100%);
  color: #087f5b;
  border: 1px solid #63e6be;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 0 3px 10px rgba(9, 146, 104, 0.12);
}

.report-content {
  line-height: 1.85;
  color: #2d3748;
  font-size: 15.5px;
  flex: 1;
}

.typing-cursor {
  display: inline-block;
  color: var(--dark-color);
  font-weight: bold;
  animation: blink 0.7s infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 深度選擇器美化專家報告格式與 APA 7th 互動式引用標籤 */
:deep(.report-para) {
  margin: 0 0 14px 0;
  line-height: 1.85;
}

:deep(.sub-sec-title) {
  margin: 22px 0 12px 0;
  font-size: 17.5px;
  color: #1a1e29;
  background-color: #f1f5f9;
  padding: 8px 14px;
  border-left: 4px solid var(--dark-color);
  border-radius: 4px;
  font-weight: 800;
}

:deep(.formula-box) {
  margin: 16px auto;
  padding: 12px 24px;
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-family: 'Georgia', serif;
  font-size: 17px;
  font-weight: bold;
  text-align: center;
  color: #1e293b;
  width: fit-content;
}

:deep(.bullet-item),
:deep(.num-item) {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
  padding-left: 6px;
  line-height: 1.8;
}

:deep(.bullet-dot),
:deep(.num-idx) {
  color: var(--dark-color);
  font-weight: 900;
  flex-shrink: 0;
}

:deep(.para-spacer) {
  height: 8px;
}

/* APA 7th (Author et al., Year) 引用樣式與滑鼠 Hover 浮現 PMID 特效 */
:deep(.apa-citation-group) {
  color: var(--dark-color);
  font-weight: 700;
  margin: 0 2px;
}

:deep(.apa-citation) {
  position: relative;
  display: inline-block;
  background-color: #e3f2fd;
  color: #0d47a1;
  padding: 0px 6px;
  border-radius: 4px;
  cursor: pointer;
  border-bottom: 1px dashed #1976d2;
  transition: all 0.15s ease;
}

:deep(.apa-citation:hover) {
  background-color: #1a1e29;
  color: #ffffff;
  border-bottom-color: #1a1e29;
}

/* 滑鼠移到 (Author et al., Year) 時浮現的 PMID 黑色懸浮窗 */
:deep(.apa-citation::after) {
  content: "📄 " attr(data-pmid);
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  background-color: #1a1e29;
  color: #63e6be;
  font-size: 12.5px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 6px;
  white-space: nowrap;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
  z-index: 3000;
  pointer-events: none;
  transition: all 0.2s ease;
}

:deep(.apa-citation:hover::after) {
  visibility: visible;
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* 底部完成橫幅特效 */
.completion-footer-banner {
  margin-top: 28px;
  padding: 14px 20px;
  background: linear-gradient(90deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 4px solid #1a1e29;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1e293b;
  font-size: 14.5px;
}

.footer-check {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #1a1e29;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}
</style>