import { marked } from 'marked'
import hljs from 'highlight.js'
import { markedHighlight } from 'marked-highlight'
import DOMPurify from 'dompurify'
import { nextTick } from 'vue'

marked.use(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value
        } catch {
          // fall through to highlightAuto
        }
      }
      return hljs.highlightAuto(code).value
    },
  })
)

const renderer = new marked.Renderer()
const originalCode = renderer.code.bind(renderer)

renderer.code = function (code, language, escaped) {
  const lang = language || ''
  const langLabel = lang ? `<span class="hm-code-lang">${lang}</span>` : ''
  const copyBtn = `<button class="hm-code-copy-btn" data-action="copy">复制</button>`
  const codeHtml = originalCode(code, language, escaped)
  return `<div class="hm-code-block"><div class="hm-code-header">${langLabel}${copyBtn}</div>${codeHtml}</div>`
}

marked.setOptions({ renderer })

let copyHandlerAttached = false
let copyHandler = null

function ensureCopyHandler() {
  if (copyHandlerAttached) return
  copyHandlerAttached = true
  copyHandler = (e) => {
    const btn = e.target.closest('[data-action="copy"]')
    if (!btn) return
    const block = btn.closest('.hm-code-block')
    const code = block?.querySelector('code')
    if (code) {
      navigator.clipboard.writeText(code.textContent).then(() => {
        btn.textContent = '已复制'
        setTimeout(() => {
          btn.textContent = '复制'
        }, 1500)
      })
    }
  }
  document.addEventListener('click', copyHandler)
}

export function cleanupCopyHandler() {
  if (copyHandler) {
    document.removeEventListener('click', copyHandler)
    copyHandler = null
    copyHandlerAttached = false
  }
}

const purifyConfig = {
  ADD_TAGS: ['button'],
  ADD_ATTR: ['data-action'],
}

export function useMarkdown() {
  ensureCopyHandler()

  const sanitize = (html) => DOMPurify.sanitize(html, purifyConfig)

  const formatMessage = (text, role) => {
    if (!text) return ''
    if (role === 'user') {
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
    }
    try {
      return sanitize(marked(text))
    } catch (e) {
      console.warn('Markdown渲染失败:', e)
      return sanitize(text.replace(/\n/g, '<br>'))
    }
  }

  const formatMarkdown = (text) => {
    if (!text) return ''
    try {
      return sanitize(marked(text))
    } catch (e) {
      console.warn('Markdown渲染失败:', e)
      return sanitize(text.replace(/\n/g, '<br>'))
    }
  }

  const scrollToBottom = (selector) => {
    nextTick(() => {
      const container = document.querySelector(selector)
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    })
  }

  const safeFormatMessage = (text, role) => {
    if (!text) return ''
    if (role === 'user') {
      return escapeHtml(text).replace(/\n/g, '<br>')
    }
    return formatMessage(text, role)
  }

  const escapeHtml = (str) => {
    const div = document.createElement('div')
    div.textContent = str
    return div.innerHTML
  }

  return { formatMessage, formatMarkdown, scrollToBottom, safeFormatMessage }
}
