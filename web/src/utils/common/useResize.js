export function useResize(el, cb) {
  const observer = new ResizeObserver((entries) => {
    cb(entries[0].contentRect)
  })
  observer.observe(el)
  return observer
}

const install = (app) => {
  const observerMap = new WeakMap()

  app.directive('resize', {
    mounted(el, binding) {
      const observer = useResize(el, binding.value)
      observerMap.set(el, observer)
    },
    beforeUnmount(el) {
      observerMap.get(el)?.disconnect()
      observerMap.delete(el)
    },
  })
}

useResize.install = install
