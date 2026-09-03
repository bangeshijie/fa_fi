import { ref } from 'vue'

/**
 * 为异步操作提供统一的 loading 状态。
 *
 * 页面只需要关注请求本身，loading 的开启和收尾由 hook 统一处理，
 * 即使请求抛错也不会遗留 loading 状态。
 */
export function useAsyncLoading() {
  const loading = ref(false)

  async function run<T>(task: () => Promise<T>): Promise<T> {
    loading.value = true
    try {
      return await task()
    } finally {
      loading.value = false
    }
  }

  return { loading, run }
}

