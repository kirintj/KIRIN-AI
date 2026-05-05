import { marked } from 'marked'
import hljs from 'highlight.js'
import { markedHighlight } from 'marked-highlight'
import { nextTick } from 'vue'

const copyBtnIdPrefix = 'hm-code-copy-'
let copyBtnCounter = 0

marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(code, { language: lang }).value } catch {}
    }
    return hljs.highlightAuto(code).value
  },
}))

const renderer = new marked.Renderer()
const originalCode = renderer.code.bind(renderer)

renderer.code = function (code, language, escaped) {
  const lang = language || ''
  const id = `${copyBtnIdPrefix}${copyBtnCounter++}`
  const langLabel = lang ? `<span class="hm-code-lang">${lang}</span>` : ''
  const copyBtn = `<button class="hm-code-copy-btn" data-code-id="${id}" onclick="(function(btn){var el=btn.parentElement.querySelector('code');if(el){navigator.clipboard.writeText(el.textContent).then(function(){btn.textContent='已复制';setTimeout(function(){btn.textContent='复制'},1500)})}})(this)">复制</button>`
  const codeHtml = originalCode(code, language, escaped)
  return `<div class="hm-code-block" id="${id}"><div class="hm-code-header">${langLabel}${copyBtn}</div>${codeHtml}</div>`
}

marked.setOptions({ renderer })

export function useMarkdown() {
  const formatMessage = (text, role) => {
    if (!text) return ''
    if (role === 'user') {
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
    }
    return marked(text)
  }

  const formatMarkdown = (text) => {
    if (!text) return ''
    return marked(text)
  }

  const scrollToBottom = (selector) => {
    nextTick(() => {
      const container = document.querySelector(selector)
      if (container) container.scrollTop = container.scrollHeight
    })
  }

  return { formatMessage, formatMarkdown, scrollToBottom }
}
