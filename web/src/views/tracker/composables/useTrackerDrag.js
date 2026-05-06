import { ref } from 'vue'

export function useTrackerDrag(onDrop) {
  const dragAppId = ref(null)
  const dragOverStatus = ref(null)

  const onCardDragStart = (appId) => {
    dragAppId.value = appId
  }

  const onCardDragEnd = () => {
    dragAppId.value = null
    dragOverStatus.value = null
  }

  const onColDragOver = (e, status) => {
    e.preventDefault()
    dragOverStatus.value = status
  }

  const onColDragLeave = () => {
    dragOverStatus.value = null
  }

  const onColDrop = async (status) => {
    if (dragAppId.value && dragOverStatus.value) {
      await onDrop(dragAppId.value, status)
    }
    dragAppId.value = null
    dragOverStatus.value = null
  }

  return {
    dragAppId,
    dragOverStatus,
    onCardDragStart,
    onCardDragEnd,
    onColDragOver,
    onColDragLeave,
    onColDrop,
  }
}
