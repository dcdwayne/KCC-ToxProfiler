<template>
  <transition name="pin-fade">
    <div
      v-if="visible"
      ref="tooltipEl"
      class="global-pin-tooltip"
      :class="{ 'is-pinned': pinned }"
      :style="{ top: `${pos.top}px`, left: `${pos.left}px` }"
      @click.stop
    >
      <!-- 頂部狀態與關閉按鈕列 -->
      <div class="gpt-header">
        <span class="gpt-badge">
          {{ pinned ? t('📌 已固定（可直接反白選取複製）', '📌 Pinned (Select text to copy)') : t('💡 點擊此標籤可固定視窗', '💡 Click to pin tooltip') }}
        </span>

        <button
          v-if="pinned"
          type="button"
          class="gpt-close-btn"
          @click="unpinAndHide"
          title="關閉固定視窗"
        >
          ✕
        </button>
      </div>

      <!-- 可自由反白選取複製的真實 DOM 文字區 -->
      <div class="gpt-content">
        {{ contentText }}
      </div>
    </div>
  </transition>
</template>

<script setup>
import { t } from '../utils/i18nStore'
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'

const visible = ref(false)
const pinned = ref(false)
const contentText = ref('')
const activeTarget = ref(null)
const tooltipEl = ref(null)

const pos = reactive({ top: 0, left: 0 })

// 偵測畫面上的目標元素（支援 APA 引用 .apa-citation 與 文獻回顧黃色匹配片段）
const findTooltipTarget = (el) => {
  if (!el || !el.closest) return null
  return el.closest(
    '.apa-citation, [data-pmid], [data-tooltip], [data-kcc-match], .highlight-sentence, .matched-sentence, .kcc-highlight, mark[title], span[data-match-info]'
  )
}

// 取出目標元素的提示文字
const extractTooltipText = (target) => {
  if (!target) return ''
  if (target.getAttribute('data-Title-moved')) {
    return target.getAttribute('data-pin-tip') || ''
  }
  const titleAttr = target.getAttribute('title')
  if (titleAttr) {
    target.setAttribute('data-pin-tip', titleAttr)
    target.setAttribute('data-Title-moved', '1')
    target.removeAttribute('title')
    return titleAttr
  }
  const dataPmid = target.getAttribute('data-pmid')
  if (dataPmid) return `📄 ${dataPmid}`

  const dataTip =
    target.getAttribute('data-tooltip') ||
    target.getAttribute('data-kcc-match') ||
    target.getAttribute('data-match-info')
  if (dataTip) return dataTip

  const childTip = target.querySelector('.tooltip-text, .kcc-tooltip, .match-tooltip, .chunk-tooltip')
  if (childTip) return childTip.innerText.trim()

  return ''
}

const updatePosition = (target) => {
  const rect = target.getBoundingClientRect()
  const boxWidth = 320
  let left = rect.left + rect.width / 2 - boxWidth / 2
  left = Math.max(12, Math.min(left, window.innerWidth - boxWidth - 12))

  let top = rect.top - 12
  if (top < 110) {
    top = rect.bottom + 10
  } else {
    top = rect.top - 86
  }

  pos.left = left
  pos.top = Math.max(10, top)
}

const handleMouseOver = (e) => {
  if (pinned.value) return
  const target = findTooltipTarget(e.target)
  if (!target) return

  const text = extractTooltipText(target)
  if (!text) return

  activeTarget.value = target
  contentText.value = text
  updatePosition(target)
  visible.value = true
}

const handleMouseOut = (e) => {
  if (pinned.value) return
  const target = findTooltipTarget(e.target)
  if (!target) return
  const related = e.relatedTarget
  if (tooltipEl.value && tooltipEl.value.contains(related)) return
  if (activeTarget.value && activeTarget.value.contains(related)) return
  visible.value = false
  activeTarget.value = null
}

const handleDocumentClick = (e) => {
  if (tooltipEl.value && tooltipEl.value.contains(e.target)) {
    return
  }

  const target = findTooltipTarget(e.target)
  if (target) {
    const text = extractTooltipText(target)
    if (text) {
      e.stopPropagation()
      if (pinned.value && activeTarget.value === target) {
        unpinAndHide()
      } else {
        if (activeTarget.value) activeTarget.value.classList.remove('pinned-highlight-active')
        activeTarget.value = target
        activeTarget.value.classList.add('pinned-highlight-active')
        contentText.value = text
        updatePosition(target)
        visible.value = true
        pinned.value = true
      }
      return
    }
  }

  if (pinned.value || visible.value) {
    unpinAndHide()
  }
}

const unpinAndHide = () => {
  if (activeTarget.value) {
    activeTarget.value.classList.remove('pinned-highlight-active')
  }
  pinned.value = false
  visible.value = false
  activeTarget.value = null
}

onMounted(() => {
  document.addEventListener('mouseover', handleMouseOver, true)
  document.addEventListener('mouseout', handleMouseOut, true)
  document.addEventListener('click', handleDocumentClick, true)
  window.addEventListener('scroll', () => {
    if (pinned.value && activeTarget.value) {
      updatePosition(activeTarget.value)
    } else if (!pinned.value) {
      visible.value = false
    }
  }, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('mouseover', handleMouseOver, true)
  document.removeEventListener('mouseout', handleMouseOut, true)
  document.removeEventListener('click', handleDocumentClick, true)
})
</script>

<style scoped>
.global-pin-tooltip {
  position: fixed;
  width: 320px;
  max-width: 92vw;
  background-color: #1a1e29;
  color: #ffffff;
  border: 1.5px solid #38bdf8;
  border-radius: 12px;
  padding: 10px 14px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
  z-index: 9999;
  pointer-events: none;
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.global-pin-tooltip.is-pinned {
  pointer-events: auto;
  border: 2px solid #f6d32d;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.45);
}

.gpt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding-bottom: 6px;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.gpt-badge {
  font-size: 11px;
  font-weight: 800;
  color: #94a3b8;
}

.global-pin-tooltip.is-pinned .gpt-badge {
  color: #f6d32d;
}

.gpt-close-btn {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  border: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 11px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.gpt-close-btn:hover {
  background-color: #ef4444;
}

.gpt-content {
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
  color: #63e6be;
  user-select: text !important;
  -webkit-user-select: text !important;
  cursor: text;
  word-break: break-word;
}

.pin-fade-enter-active,
.pin-fade-leave-active {
  transition: opacity 0.15s ease;
}
.pin-fade-enter-from,
.pin-fade-leave-to {
  opacity: 0;
}
</style>