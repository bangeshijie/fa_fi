import { onBeforeUnmount, ref, watch, type Ref } from 'vue'

export interface UsePollingOptions {
  /** 轮询间隔，单位为毫秒。 */
  interval?: number
  /** 可选的开关，为 false 时不会启动轮询。 */
  enabled?: Ref<boolean>
}

/**
 * 管理页面轮询定时器，并在组件卸载时自动清理。
 */
export function usePolling(task: () => void | Promise<void>, options: UsePollingOptions = {}) {
  const interval = options.interval ?? 30_000
  const running = ref(false)
  let timer: number | undefined

  function stop() {
    if (timer !== undefined) window.clearInterval(timer)
    timer = undefined
    running.value = false
  }

  function start() {
    if (options.enabled && !options.enabled.value) return
    stop()
    timer = window.setInterval(() => {
      void task()
    }, interval)
    running.value = true
  }

  function restart() {
    stop()
    start()
  }

  if (options.enabled) watch(options.enabled, restart)
  onBeforeUnmount(stop)

  return { running, start, stop, restart }
}
