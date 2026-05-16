import { marked } from 'marked'
import hljs from 'highlight.js'
import { markedHighlight } from 'marked-highlight'
import DOMPurify from 'dompurify'
import { nextTick } from 'vue'
import i18n from '~/i18n'

const t = i18n.global.t

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

renderer.code = function (token) {
  const lang = token.lang || ''
  const displayLang = lang
    ? lang.toUpperCase()
    : /<span[\s>]/.test(token.text)
      ? 'CODE'
      : 'TEXT'

  const langLabel = `<span class="hm-code-lang">${displayLang}</span>`
  const copyIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
  const copyBtn = `<button class="hm-code-copy-btn" data-action="copy">${copyIcon}</button>`
  const expandIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>'
  const expandBtn = `<button class="hm-code-expand-btn" data-action="expand">${expandIcon}</button>`
  const codeHtml = originalCode(token)
  return `<div class="hm-code-block"><div class="hm-code-header">${langLabel}<div class="hm-code-actions">${copyBtn}${expandBtn}</div></div>${codeHtml}</div>`
}

marked.use({ renderer })

let copyHandlerAttached = false
let copyHandler = null

const copySvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
const checkSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>'

function ensureCopyHandler() {
  if (copyHandlerAttached) return
  copyHandlerAttached = true
  copyHandler = (e) => {
    const copyBtn = e.target.closest('[data-action="copy"]')
    if (copyBtn) {
      const block = copyBtn.closest('.hm-code-block')
      const code = block?.querySelector('code')
      if (code) {
        navigator.clipboard.writeText(code.textContent).then(() => {
          copyBtn.innerHTML = checkSvg
          copyBtn.classList.add('copied')
          setTimeout(() => {
            copyBtn.innerHTML = copySvg
            copyBtn.classList.remove('copied')
          }, 1500)
        })
      }
      return
    }
    const expandBtn = e.target.closest('[data-action="expand"]')
    if (expandBtn) {
      const block = expandBtn.closest('.hm-code-block')
      if (block) {
        block.classList.toggle('expanded')
      }
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
  ADD_TAGS: ['button', 'svg', 'polyline', 'path', 'rect'],
  ADD_ATTR: ['data-action', 'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'points', 'd', 'x', 'y', 'width', 'height', 'rx', 'xmlns'],
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
      console.warn(t('common.messages.markdown_render_failed'), e)
      return sanitize(text.replace(/\n/g, '<br>'))
    }
  }

  const formatMarkdown = (text) => {
    if (!text) return ''
    try {
      return sanitize(marked(text))
    } catch (e) {
      console.warn(t('common.messages.markdown_render_failed'), e)
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
