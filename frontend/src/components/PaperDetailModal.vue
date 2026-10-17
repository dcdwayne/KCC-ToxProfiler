<template>
<div class="modal-overlay" @click.self="$emit('close')">
  <div class="modal-content">
    <div class="modal-header">
      <h4>{{ paper.title }}</h4>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
    <div class="modal-body">
      <div class="meta-info">
        <span class="badge">PMID: {{ paper.id }}</span>
        <span class="badge">模型: {{ paper.model }}</span>
        <span class="badge">引用次數: {{ paper.citations }}</span>
      </div>
      <h5>摘要 (Abstract)：</h5>
      <p class="abstract-text">{{ paper.abstract }}</p>
    </div>
  </div>
</div>

<!-- PaperDetailModal.vue 摘要渲染概念預覽 -->
<!--<div class="abstract-container">-->
  <!-- 依照 chunk_index 順序把片段拼回整篇摘要 -->
  <!--
  <span 
    v-for="chunk in paper.chunks" 
    :key="chunk.chunk_index"
    :class="{ 'kcc-matched-highlight': chunk.matched_kccs && chunk.matched_kccs.length > 0 }"
  >
    {{ chunk.chunk_text }}{{ ' ' }}
  -->
    <!-- 當滑鼠 Hover 到有命中的片段時，浮現對應的 KCC 關鍵片段 -->
    <!--
    <span v-if="chunk.matched_kccs && chunk.matched_kccs.length > 0" class="kcc-hover-tooltip">
      <div v-for="match in chunk.matched_kccs" :key="match.kcc_code">
        <strong>🎯 {{ match.kcc_code }} (相似度: {{ (match.similarity * 100).toFixed(1) }}%)</strong><br/>
        {{ match.query_text }}
      </div>
    </span>
  </span>
</div>
-->
</template>

<script setup>
defineProps({
  paper: Object
})
defineEmits(['close'])
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background-color: #fff;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
}
.modal-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.modal-header h4 { margin: 0; font-size: 18px; color: #333; padding-right: 20px; line-height: 1.4; }
.close-btn {
  background: none; border: none; font-size: 28px; cursor: pointer; color: #999;
  line-height: 1; padding: 0;
}
.close-btn:hover { color: #333; }
.modal-body {
  padding: 20px;
  overflow-y: auto;
}
.meta-info {
  display: flex; gap: 12px; margin-bottom: 20px;
}
.badge {
  background-color: var(--light-color); color: var(--dark-color);
  padding: 4px 12px; border-radius: 4px; font-size: 13px; font-weight: bold;
}
.modal-body h5 { margin: 0 0 12px 0; color: #555; }
.abstract-text { margin: 0; line-height: 1.6; color: #444; font-size: 15px; }
</style>