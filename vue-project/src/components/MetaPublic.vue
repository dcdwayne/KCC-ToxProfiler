<template>
  <div class="report-view">
    <div class="report-header">
      <span class="section-subtitle">SCIENTIFIC SYNTHESIS / CONCLUSION</span>
    </div>
    <div class="report-content">
      <h3>大眾版風險摘要：苯駢芘 (BaP)</h3>
      <p>
        苯駢芘 (BaP) 是一種極強的致癌物質，廣泛存在於燒烤食物與汽車廢氣中。根據最新的科學文獻分析，我們發現它具備高度的基因毒性，會直接破壞人體細胞的 DNA...
      </p>
      <p class="conclusion">
        <strong>Conclusion:</strong> BaP is a definitive carcinogenic hazard with a score of <strong>96/100</strong>, acting primarily through genotoxicity, metabolic activation, and oxidative damage.
      </p>
    </div>
  </div>
</template>

<style scoped>
.report-view {
  background-color: #fff;
  border: 1px solid #e0e0e0;
  border-left: 4px solid var(--dark-color);
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.section-subtitle {
  font-size: 12px; font-weight: bold; color: #888; letter-spacing: 1.5px; text-transform: uppercase; display: block; margin-bottom: 20px;
}
.report-content p { line-height: 1.8; color: #444; font-size: 15px; margin-bottom: 16px; }
.conclusion { margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; }
</style>