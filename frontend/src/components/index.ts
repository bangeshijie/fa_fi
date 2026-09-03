import type { App, Component } from 'vue'
import SvgIcon from './SvgIcon/index.vue'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 项目全局组件映射
const globalComponents: Record<string, Component> = {
  SvgIcon,
}

export default {
  install(app: App) {
    // 注册项目全局组件
    Object.entries(globalComponents).forEach(([name, component]) => {
      app.component(name, component)
    })

    // 注册 Element Plus 图标组件
    Object.entries(ElementPlusIconsVue).forEach(([name, component]) => {
      app.component(name, component)
    })
  },
}