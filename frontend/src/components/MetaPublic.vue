<template>
  <div class="report-wrapper">
    <!-- 瀏覽器風格主題標籤頁 (無叉叉) -->
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

    <!-- 報告主視窗 -->
    <div class="report-view">
      <div class="report-header">
        <div class="header-left-meta">
          <span class="section-subtitle">PUBLIC HEALTH RISK SUMMARY / 民眾科普版評估報告</span>
          <h3 class="current-chapter-title" v-if="currentTab">{{ currentTab.full_title }}</h3>
        </div>

        <div class="header-right-actions">
          <!-- 若正在打字中，提供一鍵立即顯示全文按鈕 -->
          <button v-if="isTyping" class="skip-btn" @click="finishTypingImmediately">
            ⚡ 立即顯示全文
          </button>
          <!-- 打字結束後的完成特效徽章 -->
          <div v-if="isFinished" class="completion-badge">
            <span class="sparkle-icon">✨</span>
            <span>科普風險報告生成完畢</span>
          </div>
        </div>
      </div>

      <!-- 打字機渲染內容區 -->
      <div class="report-content">
        <div class="typewriter-body" v-html="displayedHtml"></div>
        <span v-if="isTyping" class="typing-cursor">▍</span>
      </div>

      <!-- 打字結束後底部的總結高亮特效框 -->
      <transition name="pop-fade">
        <div v-if="isFinished" class="completion-footer-banner">
          <div class="footer-check">✓</div>
          <div class="footer-text">
            <strong>本節結論已完整呈現：</strong>
            <span>{{ chemicalName }} 總體危害評級為 <strong>{{ hazardScore }} / 100</strong>，可點擊上方主題標籤頁切換閱讀其他章節。</span>
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
// 👇👇👇 【打字機速度調整區】可在此自由調整打字快慢 👇👇👇
// - TYPEWRITER_INTERVAL_MS: 每隔幾毫秒更新一次畫面 (預設 18 毫秒，數字越小越快)
// - CHARS_PER_TICK: 每次更新吐出幾個字元 (預設 3 個字，設為 1 最慢，設為 6 極快)
// =====================================================================
const TYPEWRITER_INTERVAL_MS = 18
const CHARS_PER_TICK = 3

const activeSubTabIdx = ref(0)
const displayedHtml = ref('')
const isTyping = ref(false)
const isFinished = ref(false)
let typingTimer = null

const currentTab = computed(() => {
  return props.tabs[activeSubTabIdx.value] || null
})

// 智慧型 HTML 打字機：遇到 HTML 標籤 (<...>) 時瞬間跳過標籤本體，只對可見文字做逐字打字
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

/* 瀏覽器式無叉叉標籤列 (參考圖片深色質感風格並融入系統配色) */
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
  padding: 10px 22px;
  border-radius: 10px 10px 0 0;
  font-size: 14.5px;
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
  min-height: 360px;
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
  letter-spacing: 1.5px;
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

/* 打字結束後的閃耀完成徽章特效 */
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
  color: #333;
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

/* 深度選擇器美化動態渲染的 HTML 段落與條列 */
:deep(.report-para) {
  margin: 0 0 14px 0;
  line-height: 1.85;
  color: #374151;
}

:deep(.sub-sec-title) {
  margin: 20px 0 10px 0;
  font-size: 17.5px;
  color: var(--dark-color);
  font-weight: 800;
}

:deep(.bullet-item),
:deep(.num-item) {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
  padding-left: 6px;
  line-height: 1.75;
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

/* 底部完成橫幅特效 */
.completion-footer-banner {
  margin-top: 28px;
  padding: 14px 20px;
  background: linear-gradient(90deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 4px solid var(--dark-color);
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
  background-color: var(--dark-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}
</style>