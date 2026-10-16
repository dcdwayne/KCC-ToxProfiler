<template>
  <div class="report-view">
    <div class="report-header">
      <span class="section-subtitle">SCIENTIFIC SYNTHESIS / CONCLUSION</span>
    </div>
    <div class="report-content">
      <h3>Toxicological Assessment of Benzo[a]pyrene (BaP)</h3>
      <p>
        <strong>Benzo[a]pyrene</strong> is a classic, high-potency carcinogen that meets the majority of the 10 Key Characteristics (KCC) defined by the IARC framework. Based on the provided literature, there is <strong>Strong</strong> evidence for its metabolic activation into electrophilic metabolites (KCC 1), specifically via the <strong>CYP450 system</strong> (PMID: 9542332). This activation leads to the formation of stable <strong>DNA adducts</strong> and significant DNA damage (KCC 2)...
      </p>
      <p class="conclusion">
        <strong>Conclusion:</strong> BaP is a definitive carcinogenic hazard with a score of <strong>96/100</strong>, acting primarily through genotoxicity, metabolic activation, and oxidative damage.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* 與 Public 共用相同的報告外觀 */
.report-view {
  background-color: #fff; border: 1px solid #e0e0e0; border-left: 4px solid var(--dark-color); padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.section-subtitle { font-size: 12px; font-weight: bold; color: #888; letter-spacing: 1.5px; text-transform: uppercase; display: block; margin-bottom: 20px;}
.report-content p { line-height: 1.8; color: #444; font-size: 15px; margin-bottom: 16px; }
.conclusion { margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; }
</style>