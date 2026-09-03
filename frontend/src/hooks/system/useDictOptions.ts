import { ref } from 'vue'

import { fetchDictOptions, type DictOption } from '@/utils/dict'

/**
 * 加载并保存当前页面使用的字典选项状态。
 * 字典数据的具体请求和排序规则仍由 utils/dict 负责。
 */
export function useDictOptions(dictType: string) {
  const options = ref<DictOption[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      options.value = await fetchDictOptions(dictType)
      return options.value
    } finally {
      loading.value = false
    }
  }

  return { options, loading, load }
}
