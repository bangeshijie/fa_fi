<template>
    <!-- 刷新按钮 -->
    <el-button type="primary" size="small" icon="Refresh" circle @click="updateRefsh" class="icon-btn"></el-button>

    <!-- 全屏按钮 -->
    <el-button type="primary" size="small" icon="FullScreen" circle @click="fullScreen" class="icon-btn"></el-button>

    <!-- 设置按钮（带弹出框） -->
    <el-popover placement="bottom" title="主题切换" :width="200" trigger="hover">
        <el-form>
            <el-form-item label="主题颜色" key="theme-color-item">
                <el-color-picker @change="setColor" v-model="color" size="default" show-alpha
                    :predefine="predefineColors" :teleported="false" />
            </el-form-item>
            <el-form-item label="暗黑模式" key="dark-mode-item">
                <el-switch @change="changeDark" v-model="dark" size="default" active-icon="Moon" inactive-icon="Sunny"
                    inline-prompt />
            </el-form-item>
        </el-form>

        <template #reference>
            <el-button type="primary" size="small" icon="Setting" circle class="icon-btn"></el-button>
        </template>
    </el-popover>

    <!-- 账户入口 -->
    <el-dropdown class="account-dropdown" trigger="click">
        <button class="account-trigger" type="button">
            <el-avatar :src="resolveAssetUrl(authStore.info.avatar) || undefined" :size="26">
                {{ (authStore.info.name || authStore.info.username || '用').slice(0, 1) }}
            </el-avatar>
            <span class="account-name">
                {{ authStore.info.name || authStore.info.username || '用户' }}
            </span>
            <el-icon class="el-icon--right">
                <arrow-down />
            </el-icon>
        </button>
        <template #dropdown>
            <el-dropdown-menu>
                <el-dropdown-item @click="goProfile">个人中心</el-dropdown-item>
                <el-dropdown-item @click="changepwd">修改密码</el-dropdown-item>
                <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
        </template>
    </el-dropdown>

    <!-- ================= 修改密码弹窗 ================= -->
    <el-dialog v-model="dialogVisible" title="修改密码" width="400px" :close-on-click-modal="false" @close="resetPwdForm"
        :teleported="true" append-to-body :z-index="20260302" top="15vh">
        <el-form ref="pwdFormRef" :model="pwdFormData" :rules="pwdRules" label-width="80px" size="default">
            <el-form-item label="旧密码" prop="oldPassword">
                <el-input v-model="pwdFormData.oldPassword" type="password" placeholder="请输入当前密码" show-password
                    autocomplete="off" />
            </el-form-item>

            <el-form-item label="新密码" prop="newPassword">
                <el-input v-model="pwdFormData.newPassword" type="password" placeholder="请输入新密码" show-password
                    autocomplete="off" />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
                <el-input v-model="pwdFormData.confirmPassword" type="password" placeholder="请再次输入新密码" show-password
                    autocomplete="off" />
            </el-form-item>
        </el-form>

        <template #footer>
            <span class="dialog-footer">
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="pwdLoading" @click="handlePwdSubmit">
                    确定
                </el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
// 定义组件名
defineOptions({
    name: 'Setting'
})

import { useRouter, useRoute } from 'vue-router';
import { ref, onMounted, reactive } from 'vue'
import useLayoutSettingStore from '@/store/layoutsetting';
import { validatePassword } from '@/utils';
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useTabsStore } from '@/store/tabs'
import { UserAPI } from '@/api/module_system/user'
import { useAuthStore } from '@/store/auth';
import { resolveAssetUrl } from '@/utils';

const layoutSettingStore = useLayoutSettingStore();
const tabsStore = useTabsStore()
const authStore = useAuthStore()
const $router = useRouter();
const $route = useRoute();

// 跳转个人中心
const goProfile = () => {
    $router.push('/profile')
}

// 刷新按钮点击回调
const updateRefsh = () => {
    tabsStore.refreshCurrentTab()
    layoutSettingStore.refresh = !layoutSettingStore.refresh
}

// 全屏按钮点击回调
const fullScreen = () => {
    let full = document.fullscreenElement;
    if (!full) {
        document.documentElement.requestFullscreen()
    } else {
        document.exitFullscreen();
    }
}

// ================= 修改密码相关 =================
const dialogVisible = ref(false)
const pwdLoading = ref(false)
const pwdFormRef = ref<FormInstance>()

const pwdFormData = reactive({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
    if (value === '') {
        callback(new Error('请再次输入密码'))
    } else if (value !== pwdFormData.newPassword) {
        callback(new Error('两次输入的密码不一致'))
    } else {
        callback()
    }
}

const pwdRules = reactive<FormRules>({
    oldPassword: [
        { required: true, message: '请输入旧密码', trigger: 'blur' },
        { validator: validatePassword, trigger: 'blur' }
    ],
    newPassword: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { validator: validatePassword, trigger: 'blur' }
    ],
    confirmPassword: [
        { required: true, validator: validateConfirmPassword, trigger: 'blur' }
    ]
})

const changepwd = () => {
    dialogVisible.value = true
}

const resetPwdForm = () => {
    if (pwdFormRef.value) {
        pwdFormRef.value.resetFields()
    }
    pwdFormData.oldPassword = ''
    pwdFormData.newPassword = ''
    pwdFormData.confirmPassword = ''
}

const handlePwdSubmit = async () => {
    if (!pwdFormRef.value) return

    try {
        await pwdFormRef.value.validate()
        pwdLoading.value = true

        const submitData = {
            old_password: pwdFormData.oldPassword,
            new_password: pwdFormData.newPassword,
            confirm_password: pwdFormData.confirmPassword
        }

        await UserAPI.changeCurrentUserPassword(submitData)
        ElMessage.success("密码修改成功，请重新登录")
        dialogVisible.value = false

        await authStore.logout()
        await $router.replace({
            path: '/login',
            query: {
                redirect: $route.fullPath
            }
        })

    } catch (error: any) {
        console.error("修改密码失败:", error)
    } finally {
        pwdLoading.value = false
    }
}

// 退出登录
const logout = async () => {
    try {
        await authStore.logout();
        await $router.replace({
            path: '/login',
            query: { redirect: $route.fullPath }
        });
    } catch (error) {
        console.error('退出失败:', error);
        ElMessage.error('退出失败');
    }
}

// ================= 主题切换相关 =================
const dark = ref<boolean>(localStorage.getItem('theme') === 'dark')
const color = ref('#246bfe')
const predefineColors = ref([
    '#23ADE5',
    '#1d55cb',
    '#FB7299',
    '#FF80AB',
    '#FEC400',
    '#8A2BE2',
    '#00D4AA'

])

const setColor = () => {
    const html = document.documentElement
    html.style.setProperty('--el-color-primary', color.value)
}

const applyTheme = () => {
    const html = document.documentElement
    const theme = dark.value ? 'dark' : 'light'
    html.classList.toggle('dark', dark.value)
    html.dataset.theme = theme
    localStorage.setItem('theme', theme)
    window.dispatchEvent(new CustomEvent('theme-change', { detail: { theme: dark.value ? 'dark' : 'light' } }))
}

onMounted(() => {
    applyTheme()
})

const changeDark = () => {
    applyTheme()
}
</script>

<style scoped lang="scss">
// ================= 图标按钮样式 =================
.icon-btn {
    // 基础样式 - 平时显示主题色
    background-color: transparent !important;
    border-color: transparent !important;
    color: var(--el-color-primary) !important; // 默认就是主题色
    font-size: 18px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    // 悬停效果：保持主题色 + 放大 1.1 倍 + 浅色背景
    &:hover {
        color: var(--el-color-primary) !important; // 保持主题色
        background-color: var(--app-menu-active) !important;
        transform: scale(1.1) !important; // 放大 1.1 倍
    }

    // 点击效果：缩小
    &:active {
        transform: scale(0.95) !important;
    }

    // 聚焦效果
    &:focus-visible {
        outline: 2px solid var(--el-color-primary);
        outline-offset: 2px;
    }
}

// Element Plus 的 primary 全局规则不能覆盖顶部快捷按钮的主题色。
.icon-btn.el-button--primary {
    color: var(--el-color-primary) !important;
}

.icon-btn.el-button--primary:hover {
    color: var(--el-color-primary) !important;
    transform: scale(1.1) !important;
}

// ================= 账户下拉菜单样式 =================
.account-dropdown {
    margin-right: 14px;
    margin-top: 0px;
}

.account-trigger {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    color: var(--el-text-color-primary);
    border: 1px solid transparent;
    border-radius: 2px;
    transition: border-color .2s ease, background-color .2s ease;
    cursor: pointer;
    background: transparent;

    &:hover,
    &:focus-visible {
        border-color: var(--el-color-primary);
        background: rgba(var(--el-color-primary-rgb, 36, 107, 254), 0.05);
    }
}

.account-name {
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
    color: var(--app-muted);
}

// ================= 修改密码弹窗样式 =================
.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

// 提升弹窗层级
:deep(.el-overlay) {
    z-index: 20260301 !important;
}

:deep(.el-dialog) {
    z-index: 20260302 !important;
    position: fixed !important;
}
</style>
