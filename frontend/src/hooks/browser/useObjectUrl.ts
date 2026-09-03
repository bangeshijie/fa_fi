import { onBeforeUnmount, ref } from 'vue'

function revokeIfObjectUrl(value: string) {
  if (value.startsWith('blob:')) URL.revokeObjectURL(value)
}

/**
 * 管理由 File 创建的临时预览地址，避免页面卸载或替换预览时泄漏 Blob URL。
 */
export function useObjectUrl(initialValue = '') {
  const url = ref(initialValue)

  function setUrl(value: string) {
    revokeIfObjectUrl(url.value)
    url.value = value
  }

  function setFilePreview(file: File) {
    setUrl(URL.createObjectURL(file))
    return url.value
  }

  function release() {
    revokeIfObjectUrl(url.value)
  }

  onBeforeUnmount(release)

  return { url, setUrl, setFilePreview, release }
}

