# Elemento 14 - Card Performance Analytics

## O que é
Card de analytics com título "Performance Analytics", badge "Live", métricas (Total Views 24.5K, Conversions 1.2K), gráfico de barras e botão "View Details". Fundo com glow em gradiente ao hover.

## HTML

```html
<div class="card-analytics">
  <div class="glow-bg"></div>
  <div class="inner">
    <div class="header">
      <div class="header-left">
        <div class="icon-box">
          <svg>...</svg>
        </div>
        <h3>Performance Analytics</h3>
      </div>
      <span class="badge"><span class="badge-dot"></span> Live</span>
    </div>
    <div class="stats-grid">
      <div class="stat-box">
        <p class="stat-label">Total Views</p>
        <p class="stat-value">24.5K</p>
        <span class="stat-change">+12.3%</span>
      </div>
      <div class="stat-box">...</div>
    </div>
    <div class="chart-area">
      <div class="chart-bars">
        <div class="chart-bar"><div class="chart-bar-fill" style="height: 60%;"></div></div>
        <!-- mais barras -->
      </div>
    </div>
    <div class="footer">
      <div class="footer-text">Last 7 days</div>
      <button class="view-btn">View Details</button>
    </div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/cards.css` (classes: `.card-analytics`, `.stat-box`, `.chart-bar`, `.view-btn`)
