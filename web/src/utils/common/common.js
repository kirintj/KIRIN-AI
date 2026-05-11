import dayjs from 'dayjs'

/**
 * @desc  格式化时间
 * @param {(Object|string|number)} time
 * @param {string} format
 * @returns {string | null}
 */
export function formatDateTime(time = undefined, format = 'YYYY-MM-DD HH:mm:ss') {
  return dayjs(time).format(format)
}

export function formatDate(date = undefined, format = 'YYYY-MM-DD') {
  return formatDateTime(date, format)
}

/**
 * @desc  函数节流
 * @param {Function} fn
 * @param {Number} wait
 * @returns {Function}
 */
export function throttle(fn, wait) {
  let previous = 0

  return function (...args) {
    const now = +new Date()
    if (now - previous > wait) {
      fn.apply(this, args)
      previous = now
    }
  }
}

/**
 * @desc  函数防抖
 * @param {Function} func
 * @param {number} wait
 * @param {boolean} immediate
 * @return {*}
 */
export function debounce(method, wait, immediate) {
  let timeout
  return function (...args) {
    if (timeout) {
      clearTimeout(timeout)
    }
    if (immediate) {
      const callNow = !timeout
      timeout = setTimeout(() => {
        timeout = null
      }, wait)
      if (callNow) {
        method.apply(this, args)
      }
    } else {
      timeout = setTimeout(() => {
        method.apply(this, args)
      }, wait)
    }
  }
}
