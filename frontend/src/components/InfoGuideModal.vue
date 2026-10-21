<template>
  <!-- 反灰半透明背景遮罩 (點擊背景空白處亦可關閉) -->
  <transition name="modal-fade">
    <div v-if="isOpen" class="guide-overlay" @click.self="$emit('close')">
      <div class="guide-modal">
        <!-- 頂部深色標題列 -->
        <header class="guide-header">
          <div class="header-title-group">
            <span class="guide-icon">!</span>
            <div>
              <span class="guide-subtitle">{{ currentGuide.subtitle }}</span>
              <h3 class="guide-title">{{ currentGuide.title }}</h3>
            </div>
          </div>
          <button class="close-btn" @click="$emit('close')" title="關閉使用說明">✕</button>
        </header>

        <!-- 中間滾動內容區 -->
        <div class="guide-body">
          <p class="guide-intro">{{ currentGuide.intro }}</p>

          <!-- ================= 1. 首頁 (HomeView) 說明內容 ================= -->
          <template v-if="page === 'home'">
            <div class="step-card">
              <div class="step-badge">STEP 1</div>
              <div class="step-content">
                <h4>選擇目標化學物質 (Target Chemicals)</h4>
                <p>點選欲評估之化學物質（如：苯駢芘、丙烯醯胺、塑化劑、戴奧辛、全氟辛酸），系統將自動關聯資料庫中之 <strong>CAS 號碼</strong> 與所有<strong>化學同義詞/縮寫</strong>，確保文獻檢索不遺漏。</p>
              </div>
            </div>

            <div class="step-card">
              <div class="step-badge">STEP 2</div>
              <div class="step-content">
                <h4>設定初步條件搜尋 (Preliminary Filter)</h4>
                <ul class="guide-list">
                  <li><strong>出版年份</strong>：設定欲納入分析的文獻發表西元年份區間（如 2000 至 2026 年）。</li>
                  <li><strong>引用次數（單選）</strong>：設定文獻於 PubMed 被引用的最低門檻（至少被引用 <code>1</code>、<code>3</code>、<code>10</code> 或 <code>20</code> 次以上），過濾具學術影響力之研究。</li>
                  <li><strong>文獻類型（單選）</strong>：
                    <div class="sub-box">
                      <div><span class="tag-pill">Original Research</span> 納入原始實驗研究 (<code>Journal Article</code>)，自動排除綜述 (<code>Review</code>)、社論與勘誤。</div>
                      <div><span class="tag-pill">Review</span> 鎖定綜合性文獻回顧 (<code>Review</code> / <code>Systematic Review</code> / <code>Meta-Analysis</code>)。</div>
                      <div><span class="tag-pill">All</span> 涵蓋該化學物質所有原始研究與綜述文獻。</div>
                    </div>
                  </li>
                  <li><strong>期刊排名（多選）</strong>：依據 Scimago (SJR) 全球期刊排名資料庫，篩選 <code>Q1</code> ~ <code>Q4</code> 等級期刊。</li>
                </ul>
              </div>
            </div>

            <div class="step-card">
              <div class="step-badge">STEP 3</div>
              <div class="step-content">
                <h4>預覽數量與啟動 RAG 向量檢索</h4>
                <ul class="guide-list">
                  <li>點擊 <strong>「初步篩選成果」</strong> 可即時查詢符合當前條件的資料庫文獻總篇數。</li>
                  <li>確認篇數合適後，點擊底部 <strong>「確定送出篩選」</strong>，系統將針對入選文獻執行 <strong>語意分片 (Chunking)</strong>、<strong>Voyage-3 向量化 (Embedding)</strong> 以及 <strong>10 KCC 餘弦相似度召回與 Cross-Encoder 重排</strong>，並自動導向系統性文獻回顧頁面。</li>
                </ul>
              </div>
            </div>
          </template>

          <!-- ================= 2. 系統性文獻回顧 (SystematicReview) 說明內容 ================= -->
          <template v-else-if="page === 'review'">
            <div class="step-card">
              <div class="step-badge">功能 1</div>
              <div class="step-content">
                <h4>證據池檢視 (10 KCCs Evidence Pool)</h4>
                <p>右側 10 個按鈕對應 IARC 定義之<strong>「10 大致癌關鍵特徵 (Key Characteristics of Carcinogens)」</strong>。括號內數字代表通過 AI 語意召回與重排後，目前納入該機轉的文獻篇數，點擊按鈕即可切換檢視各機轉的文獻清單。</p>
              </div>
            </div>

            <div class="step-card">
              <div class="step-badge">功能 2</div>
              <div class="step-content">
                <h4>單一機轉進階篩選與「重新載入」(左側面板)</h4>
                <ul class="guide-list">
                  <li>左側篩選器專門針對<strong>「目前點選的 KC 類別」</strong>進行深度過濾，可篩選<strong>資料來源</strong>、<strong>適配度 (%)</strong>、<strong>出版年份</strong>、<strong>引用次數</strong>與<strong>期刊排名</strong>。</li>
                  <li>點擊 <strong>「送出篩選」</strong> 後，不符條件的文獻將從該 KC 證據池中剔除，並即時更新按鈕篇數。</li>
                  <li>點擊左下角 <strong>「重新載入」</strong>，可將該 KC 類別一鍵還原至初始召回的所有文獻狀態（恢復被篩選或手動刪除的文獻）。</li>
                </ul>
              </div>
            </div>

            <div class="step-card">
              <div class="step-badge">功能 3</div>
              <div class="step-content">
                <h4>文獻列表標籤、排序與人工精鍊刪除</h4>
                <ul class="guide-list">
                  <li><strong>實驗模型標籤與計分權重</strong>：
                    <span class="badge-demo cohort">cohort (人體流行病學: 10分)</span>
                    <span class="badge-demo invivo">in vivo (動物實驗: 7分)</span>
                    <span class="badge-demo invitro">in vitro (細胞實驗: 3分)</span>
                  </li>
                  <li><strong>多維度排序</strong>：右上角支援依「資料來源（權重高至低）」、「期刊排名（Q1 至 Q4）」或「適配度（% 高至低）」排序。</li>
                  <li><strong>專家手動剔除</strong>：點擊單篇文獻最右側的 <strong><code>X</code></strong>，可將該篇文獻從本機轉證據池中移除，不納入後續算分。</li>
                </ul>
              </div>
            </div>

            <div class="step-card">
              <div class="step-badge">功能 4</div>
              <div class="step-content">
                <h4>文獻摘要細節與 AI 可解釋性標記 (點擊文獻標題)</h4>
                <p>點擊任意文獻標題可彈出詳情視窗，檢視完整標題、前三位作者、機構單位與完整摘要。摘要中<strong>標記黃色螢光筆底色的句子</strong>代表與該 KCC 特徵高度配對，<strong>將滑鼠移至黃色句子上，即可浮現配對到的 KCC 關鍵片段與相似度分數</strong>。</p>
              </div>
            </div>
          </template>

          <!-- ================= 3. 統合分析 (MetaAnalysis) 說明內容 ================= -->
          <template v-else-if="page === 'meta'">
            <div class="step-card">
              <div class="step-badge">視圖 1</div>
              <div class="step-content">
                <h4>分析成果儀表板 (10 KCCs Weight of Evidence Dashboard)</h4>
                <ul class="guide-list">
                  <li><strong>總體危害分數 (Hazard Score)</strong>：右上角黑底徽章呈現綜合 10 大致癌機轉強度與廣度加權後的總分（0~100），並分為 <code>HIGH RISK (≥70)</code>、<code>MODERATE RISK (40~69)</code> 與 <code>LOW RISK (&lt;40)</code>。</li>
                  <li><strong>高影響力期刊篇數</strong>：各 KC 標題後方的括號數字如 <strong><code>(13)</code></strong> 代表發表於 <strong>Q1 / Q2 頂尖期刊</strong>的文獻篇數；卡片右上角則顯示該機轉納入的總文獻數。</li>
                  <li><strong>證據強度分級</strong>：依據實驗模型權重（Cohort / In Vivo / In Vitro）、期刊等級與適配度積分，自動評定為 <span class="badge-demo cohort">HIGH (STRONG)</span>、<span class="badge-demo invivo">MODERATE</span>、<span class="badge-demo invitro">WEAK</span> 或 <code>INADEQUATE</code>。</li>
                </ul>
              </div>
            </div>

            <div class="step-card">
              <div class="step-badge">視圖 2</div>
              <div class="step-content">
                <h4>民眾版本報告 (Public Health Summary)</h4>
                <p>當 AI 於背景完成生成後按鈕即自動解鎖。採用分頁標籤設計，將複雜毒理數據轉化為一般大眾易讀的三大主題：<strong>「1. 化學物質介紹」</strong>、<strong>「2. 主要暴露途徑與減毒行動」</strong>以及<strong>「3. KCC 分析結論與危害分數說明」</strong>（可點擊右上角「⚡ 立即顯示全文」略過打字動畫）。</p>
              </div>
            </div>

            <div class="step-card">
              <div class="step-badge">視圖 3</div>
              <div class="step-content">
                <h4>專家版本報告與 APA 7th 互動式引用 (Regulatory Toxicology Report)</h4>
                <ul class="guide-list">
                  <li>針對法規毒理專家設計四大核心章節標籤頁：<strong>「1. MoE 暴露邊際與劑量效應」</strong>、<strong>「2. Critical Effects 關鍵臨界效應」</strong>、<strong>「3. 10 KCCs 成果詳解（自動區分證據明確與科學知識缺口 Data Gaps）」</strong>與<strong>「4. 綜合危害分數與 WoE 定論」</strong>。</li>
                  <li><strong>互動式文獻溯源</strong>：內文引用全面採用 APA 7th 格式（如 <span class="apa-demo">(Bukowska et al., 2022)</span>），<strong>將滑鼠移至藍底引用標記上，即可直接浮現該文獻的原始 <code>PMID</code> 與發表期刊名稱</strong>。</li>
                </ul>
              </div>
            </div>
          </template>
        </div>

        <!-- 底部確認按鈕 -->
        <footer class="guide-footer">
          <button class="got-it-btn" @click="$emit('close')">我瞭解了</button>
        </footer>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  page: {
    type: String,
    default: 'home' // 'home' | 'review' | 'meta'
  }
})

defineEmits(['close'])

const GUIDE_META = {
  home: {
    subtitle: 'STEP 1 : PRELIMINARY LITERATURE RETRIEVAL',
    title: '首頁：文獻條件檢索與初步篩選使用說明',
    intro: '本頁面協助您鎖定目標化學物質，從 PubMed 毒理文獻庫中依據年份、引用數、文獻類型與期刊等級進行第一階段過濾，並啟動 AI 向量切片與 10 KCC 特徵配對流程。'
  },
  review: {
    subtitle: 'STEP 2 : SYSTEMATIC REVIEW & EXPERT CURATION',
    title: '系統性文獻回顧與專家精鍊使用說明',
    intro: '本頁面呈現經由 RAG 餘弦相似度召回與 Cross-Encoder 重排後的 10 大致癌關鍵特徵 (10 KCCs) 證據池，供專家檢視命中摘要片段並進行人工篩選精鍊。'
  },
  meta: {
    subtitle: 'STEP 3 : WEIGHT OF EVIDENCE & AI SYNTHESIS',
    title: '證據權重危害辨識統合分析使用說明',
    intro: '本頁面根據專家精鍊後的最終實證文獻池，量化計算 10 KCC 證據強度與總體危害分數 (Hazard Score)，並提供 AI 生成之「民眾科普版」與「專家法規版」雙軌評估報告。'
  }
}

const currentGuide = computed(() => {
  return GUIDE_META[props.page] || GUIDE_META.home
})
</script>

<style scoped>
/* 半透明反灰背景遮罩 */
.guide-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(27, 30, 41, 0.6);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2500;
  padding: 20px;
}

/* 彈出視窗本體 */
.guide-modal {
  background-color: #ffffff;
  width: 95%;
  max-width: 760px;
  max-height: 85vh;
  border-radius: 18px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

/* 頂部深色標題列 */
.guide-header {
  background-color: #1b1e29;
  color: #ffffff;
  padding: 20px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 4px solid #e25740;
}

.header-title-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.guide-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-color: #e25740;
  color: #ffffff;
  font-weight: 900;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-subtitle {
  font-size: 11px;
  letter-spacing: 1.2px;
  color: #94a3b8;
  font-weight: 800;
  display: block;
}

.guide-title {
  margin: 2px 0 0 0;
  font-size: 20px;
  font-weight: 800;
  color: #ffffff;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #cbd5e1;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #e25740;
  color: #ffffff;
}

/* 內容區域 */
.guide-body {
  padding: 24px 28px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.guide-intro {
  margin: 0 0 4px 0;
  font-size: 15px;
  line-height: 1.65;
  color: #334155;
  background-color: #f1f5f9;
  padding: 12px 16px;
  border-radius: 10px;
  border-left: 4px solid var(--dark-color);
  font-weight: 600;
}

.step-card {
  display: flex;
  gap: 16px;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.step-badge {
  background-color: var(--dark-color);
  color: #ffffff;
  font-size: 12px;
  font-weight: 900;
  padding: 6px 12px;
  border-radius: 8px;
  height: fit-content;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.step-content {
  flex: 1;
}

.step-content h4 {
  margin: 0 0 8px 0;
  font-size: 16.5px;
  color: #1b1e29;
  font-weight: 800;
}

.step-content p {
  margin: 0;
  font-size: 14.5px;
  line-height: 1.65;
  color: #475569;
}

.guide-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14.5px;
  line-height: 1.65;
  color: #475569;
}

.sub-box {
  margin-top: 6px;
  background-color: #f8fafc;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13.5px;
}

.tag-pill {
  display: inline-block;
  background-color: #1b1e29;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 6px;
}

.badge-demo {
  display: inline-block;
  color: #ffffff;
  font-size: 12px;
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 4px;
  margin: 0 4px;
}
.badge-demo.cohort { background-color: #e74c3c; }
.badge-demo.invivo { background-color: #f39c12; }
.badge-demo.invitro { background-color: #95a5a6; }

.apa-demo {
  background-color: #e3f2fd;
  color: #0d47a1;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 700;
  border-bottom: 1px dashed #1976d2;
}

/* 底部按鈕區 */
.guide-footer {
  padding: 14px 28px;
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.got-it-btn {
  background-color: #1b1e29;
  color: #ffffff;
  border: none;
  padding: 10px 28px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.got-it-btn:hover {
  background-color: var(--dark-color);
}

/* 彈窗淡入淡出動畫 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>