<template>
  <div class="paper-row">
    <div class="row-left">
      <span class="index">{{ index }}.</span>
      <h5 class="paper-title" @click="$emit('view-details', paper)" title="點擊查看摘要細節">
        {{ paper.title }}
      </h5>
      <span class="model-badge">{{ paper.model }}</span>
    </div>
    <div class="row-right">
      <span class="citation">引用 {{ paper.citations }} 次</span>
      <button class="delete-btn" @click="$emit('remove-paper', paper.id)" title="從 Evidence Pool 中移除">X</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  index: Number,
  paper: Object
})
defineEmits(['view-details', 'remove-paper'])
</script>

<style scoped>
.paper-row {
  background-color: #ffffff; 
  border: 1px solid #ffffff;
  border-radius: 12px;
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s;
}
/* 滑鼠移上去時可以保留一點淺灰色的回饋感 */
.paper-row:hover {
  background-color: #f0f0f0;
}
.row-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}
.index { font-weight: bold; font-size: 16px; }
.paper-title {
  margin: 0;
  font-size: 16px;
  color: #333;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px; /* 避免標題過長破版 */
}
.paper-title:hover {
  color: var(--dark-color);
  text-decoration: underline;
}
.model-badge {
  background-color: #fff;
  border: 1px solid #ccc;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
}
.row-right {
  display: flex;
  align-items: center;
  gap: 24px;
}
.citation { color: #555; font-size: 14px; }
.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid #666;
  background-color: transparent;
  cursor: pointer;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}
.delete-btn:hover {
  background-color: #ffebee;
  color: #c62828;
  border-color: #c62828;
}
</style>