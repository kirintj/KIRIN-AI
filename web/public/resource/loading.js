/**
 * 初始化加载效果的svg格式logo
 * @param {string} id - 元素id
 */
 function initSvgLogo(id) {
  const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">
  <!-- 定义渐变 -->
  <defs>
    <!-- 外圆环渐变（不变） -->
    <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#bbd0f5" />
      <stop offset="25%" stop-color="#bbd0f5" />
      <stop offset="50%" stop-color="#f5ccd4" />
      <stop offset="75%" stop-color="#fce49d" />
      <stop offset="100%" stop-color="#fce49d" />
    </linearGradient>
    <!-- 内部主圆渐变【优化版：过渡更自然】 -->
    <linearGradient id="mainCircleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="20%" stop-color="#3a80f1" />
      <stop offset="28%" stop-color="#6378ee" />
      <stop offset="42%" stop-color="#8a7dea" />
      <stop offset="55%" stop-color="#b884e3" />
      <stop offset="68%" stop-color="#d88d9d" />
      <stop offset="89%" stop-color="#fdb046" />
      <stop offset="100%" stop-color="#fdb046" />
    </linearGradient>
  </defs>

  <!-- 外圆环 -->
  <circle cx="250" cy="250" r="210" fill="none" stroke="url(#ringGradient)" stroke-width="20" />
  <!-- 中间白色圆环背景 -->
  <circle cx="250" cy="250" r="200" fill="#ffffff" />
  <!-- 内部主圆 -->
  <circle cx="250" cy="250" r="180" fill="url(#mainCircleGradient)" />

</svg>`
  const appEl = document.querySelector(id)
  const div = document.createElement('div')
  div.innerHTML = svgStr
  if (appEl) {
    appEl.appendChild(div)
  }
}

function addThemeColorCssVars() {
  const key = '__THEME_COLOR__'
  const defaultColor = '#F4511E'
  const themeColor = window.localStorage.getItem(key) || defaultColor
  const cssVars = `--primary-color: ${themeColor}`
  document.documentElement.style.cssText = cssVars
}

addThemeColorCssVars()

initSvgLogo('#loadingLogo')
