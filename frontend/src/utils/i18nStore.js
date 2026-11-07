// frontend/src/utils/i18nStore.js
import { reactive, computed } from 'vue'

export const i18nState = reactive({
  // 'zh' 代表繁體中文介面，'en' 代表英文介面 (預設記憶於 localStorage)
  lang: localStorage.getItem('kcc_lang') || 'zh'
})

export const isEn = computed(() => i18nState.lang === 'en')

export const toggleLang = () => {
  i18nState.lang = i18nState.lang === 'zh' ? 'en' : 'zh'
  localStorage.setItem('kcc_lang', i18nState.lang)
}

export const setLang = (targetLang) => {
  if (targetLang === 'zh' || targetLang === 'en') {
    i18nState.lang = targetLang
    localStorage.setItem('kcc_lang', targetLang)
  }
}

/**
 * 核心雙語切換函式：在 template 或 script 中呼叫 t('中文內容', 'English Content')
 * 會隨右上角語言按鈕點擊自動即時切換！
 */
export const t = (zhText, enText) => {
  return i18nState.lang === 'en' ? enText : zhText
}

// 五大化學物質顯示名稱對照 (內部傳給 API 維持中文鍵值，畫面依語言顯示中/英)
const CHEMICAL_EN_MAP = {
  '苯駢芘': 'Benzo[a]pyrene',
  '丙烯醯胺': 'Acrylamide',
  '塑化劑': 'DEHP (Phthalates)',
  '戴奧辛': 'TCDD (Dioxin)',
  '全氟辛酸': 'PFOA'
}

export const translateChemical = (chemZh) => {
  if (i18nState.lang === 'en') {
    return CHEMICAL_EN_MAP[chemZh] || chemZh
  }
  return chemZh
}

// 四大 RBAC 角色顯示名稱對照
const ROLE_EN_MAP = {
  '系統管理者': 'System Admin',
  '專家': 'Expert',
  '會員': 'Member',
  '訪客': 'Guest'
}

export const translateRole = (roleZh) => {
  if (i18nState.lang === 'en') {
    return ROLE_EN_MAP[roleZh] || roleZh
  }
  return roleZh
}