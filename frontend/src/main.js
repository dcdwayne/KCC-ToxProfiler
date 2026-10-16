// 這邊主要在建立 Vue 的應用程式！

// 載入 createApp 函式
import { createApp } from 'vue';

// 載入 根組件 App.vue 元件
// import 根組件名稱 from "組件檔案路徑";
import App from './App.vue';
import router from './router' // 引入 router


// 建立 Vue App 物件
const app = createApp(App);

// 掛載 App 到 HTML 標籤底下
app.use(router) // 使用 router
app.mount('#app'); // 對應方式採用，CSS選擇器