import { createApp } from 'vue'
import App from './App.vue'

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// @ts-ignore
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// Load the project theme after Element Plus so the project tokens win.
import '@/styles/index.scss'

import globalComponent from '@/components/index'
import { router } from '@/router/index'
import pinia from '@/store/index'

// 引入路由鉴权文件
import './router/permission'
// 注册自定义指令
import registerDirectives
    from './directives'

const app = createApp(App)

app.use(ElementPlus, { locale: zhCn })
app.use(pinia)
app.use(globalComponent)
app.use(router)

// 注册全局指令
registerDirectives(app)

app.mount('#app')
