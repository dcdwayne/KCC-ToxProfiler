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