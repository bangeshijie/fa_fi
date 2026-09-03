<template>
  <section class="profile-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">个人中心</p>
      </div>
      <div class="heading-index">01 / PROFILE</div>
    </header>

    <div class="profile-grid">
      <section class="profile-card identity-card">
        <div class="card-heading">
          <div>

            <h2>头像与身份</h2>
          </div>
          <el-tag type="success" effect="plain">已登录</el-tag>
        </div>

        <div class="identity-content">
          <button class="avatar-picker" type="button" :disabled="avatarLoading" @click="openFilePicker">
            <img v-if="avatarPreview" :src="avatarPreview" alt="个人头像" />
            <span v-else class="avatar-initial">{{ initials }}</span>
            <span class="avatar-overlay">
              <el-icon>
                <Camera />
              </el-icon>
              {{ avatarLoading ? '上传中' : '更换头像' }}
            </span>
          </button>
          <input ref="fileInput" class="visually-hidden" type="file" accept="image/png,image/jpeg,image/webp"
            @change="handleAvatarChange" />

          <div class="identity-copy">
            <h3>{{ displayName }}</h3>
            <p>{{ authStore.info.username || '—' }}</p>
            <div class="identity-meta">
              <span>{{ authStore.info.dept?.name || '未设置部门' }}</span>
              <span class="meta-dot"></span>
              <span>
                <template v-if="authStore.info.roles?.length">
                  <template v-for="(role, index) in authStore.info.roles" :key="role.id">
                    <span v-if="index > 0">、</span>{{ role.name }}
                  </template>
                </template>
                <template v-else>未设置角色</template>
              </span>
            </div>
          </div>
        </div>

        <div class="upload-note">
          <el-icon>
            <InfoFilled />
          </el-icon>
          支持 JPG、PNG、WEBP，单张不超过 10MB
        </div>
      </section>

      <section class="profile-card form-card">
        <div class="card-heading">
          <div>
            <h2>基本资料</h2>
          </div>
          <span class="required-note">* 必填项</span>
        </div>

        <el-form ref="formRef" class="profile-form" :model="form" :rules="rules" label-position="top">
          <div class="form-row">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="性别" prop="gender">
              <el-select v-model="form.gender" placeholder="请选择性别" clearable>
                <el-option
                  v-for="item in sexOptions"
                  :key="item.dict_value"
                  :label="item.dict_label"
                  :value="item.dict_value"
                />
              </el-select>
            </el-form-item>
          </div>
          <div class="form-row">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机号" prop="mobile">
              <el-input v-model="form.mobile" placeholder="请输入手机号" />
            </el-form-item>
          </div>
          <el-form-item label="账号" class="readonly-field">
            <el-input :model-value="authStore.info.username || '—'" disabled />
          </el-form-item>

          <div class="form-actions">
            <span class="save-hint">资料变更会同步到右上角账户入口</span>
            <el-button type="primary" :loading="saving" @click="submitForm">保存修改</el-button>
          </div>
        </el-form>
      </section>
    </div>

    <section class="profile-card security-card">
      <div class="security-copy">

        <h2>登录安全</h2>

      </div>
      <el-button plain @click="openPasswordDialog">修改密码 <el-icon>
          <ArrowRight />
        </el-icon></el-button>
    </section>

    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="420px" :close-on-click-modal="false">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="88px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordSaving" @click="submitPassword">确认修改</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Camera, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

import { UserAPI, type CurrentUserFormState, type PasswordFormState } from '@/api/module_system/user'
import { useAuthStore } from '@/store/auth'
import { useDictOptions } from '@/hooks'
import { useObjectUrl } from '@/hooks'
import { resolveAssetUrl } from '@/utils'
import { getDefaultDictValue, USER_SEX_DICT_TYPE } from '@/utils/dict'

defineOptions({ name: 'Profile' })

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const fileInput = ref<HTMLInputElement>()
const saving = ref(false)
const avatarLoading = ref(false)
const { url: avatarPreview, setUrl: setAvatarPreview, setFilePreview } = useObjectUrl(resolveAssetUrl(authStore.info.avatar))
const passwordDialogVisible = ref(false)
const passwordSaving = ref(false)
const { options: sexOptions, load: loadSexDictOptions } = useDictOptions(USER_SEX_DICT_TYPE)

const form = reactive<CurrentUserFormState>({
  name: authStore.info.name || '',
  gender: authStore.info.gender,
  mobile: authStore.info.mobile || '',
  email: authStore.info.email || '',
  avatar: authStore.info.avatar || '',
})

const passwordForm = reactive<PasswordFormState>({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }],
}

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [{ required: true, min: 6, message: '新密码至少 6 位', trigger: 'blur' }],
  confirm_password: [{
    validator: (_rule, value, callback) => value === passwordForm.new_password ? callback() : callback(new Error('两次输入的密码不一致')),
    trigger: 'blur',
  }],
}

async function loadSexOptions() {
  try {
    await loadSexDictOptions()
    if (!form.gender) form.gender = getDefaultDictValue(sexOptions.value)
  } catch (error) {
    console.error('加载性别字典失败', error)
    ElMessage.error('性别选项加载失败，请刷新后重试')
  }
}

const displayName = computed(() => authStore.info.name || authStore.info.username || '用户')
const initials = computed(() => displayName.value.slice(0, 1).toUpperCase())

function openFilePicker() {
  fileInput.value?.click()
}

async function handleAvatarChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    ElMessage.error('请上传 JPG、PNG 或 WEBP 格式的图片')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('头像大小不能超过 10MB')
    return
  }

  setFilePreview(file)
  avatarLoading.value = true
  try {
    const body = new FormData()
    body.append('file', file)
    const response = await UserAPI.uploadCurrentUserAvatar(body)
    const avatarPath = response.data.data?.file_path
    if (!avatarPath) throw new Error('上传接口未返回头像路径')

    const updateResponse = await UserAPI.updateCurrentUserInfo({ avatar: avatarPath })
    const updatedUser = updateResponse.data.data
    authStore.setUserInfo(updatedUser)
    form.avatar = updatedUser?.avatar || avatarPath
    setAvatarPreview(resolveAssetUrl(updatedUser?.avatar || avatarPath))
    ElMessage.success('头像更新成功')
  } catch (error) {
    setAvatarPreview(resolveAssetUrl(authStore.info.avatar))
    ElMessage.error('头像上传失败，请稍后重试')
  } finally {
    avatarLoading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate()
  saving.value = true
  try {
    const response = await UserAPI.updateCurrentUserInfo({
      ...form,
      email: form.email?.trim() || undefined,
      mobile: form.mobile?.trim() || undefined,
      gender: form.gender || undefined,
      avatar: form.avatar || authStore.info.avatar,
    })
    authStore.setUserInfo(response.data.data)
    ElMessage.success('个人资料已保存')
  } finally {
    saving.value = false
  }
}

function openPasswordDialog() {
  passwordDialogVisible.value = true
}

async function submitPassword() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate()
  passwordSaving.value = true
  try {
    await UserAPI.changeCurrentUserPassword(passwordForm)
    ElMessage.success('密码修改成功，请重新登录')
    passwordDialogVisible.value = false
    await authStore.logout({ navigate: false })
    await router.replace({ path: '/login', query: { redirect: '/profile' } })
  } finally {
    passwordSaving.value = false
  }
}

onMounted(loadSexOptions)
</script>

<style scoped lang="scss">
.profile-page {
  min-height: 100%;
  padding: 14px 4px 36px;
  color: $industrial-text;
  font-family: var(--el-font-family);
}

.page-heading,
.card-heading,
.identity-content,
.form-actions,
.security-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-heading {
  padding: 6px 0 24px;
  border-bottom: 1px solid $industrial-border;
}

.eyebrow,
.section-index,
.heading-index {
  margin: 0;
  color: $industrial-signal;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  margin-top: 6px;
  font-size: clamp(30px, 4vw, 52px);
  font-weight: 700;
  letter-spacing: -.045em;
  line-height: 1;
}

.heading-copy {
  margin-top: 10px;
  color: $industrial-muted;
  font-size: 14px;
}

.heading-index {
  color: $industrial-muted;
  letter-spacing: .08em;
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(260px, .78fr) minmax(420px, 1.22fr);
  gap: 16px;
  margin-top: 16px;
}

.profile-card {
  border: 1px solid $industrial-border;
  background: $industrial-panel;
}

.identity-card,
.form-card {
  min-height: 370px;
  padding: 26px;
}

.card-heading {
  align-items: flex-start;
  padding-bottom: 20px;
  border-bottom: 1px solid $industrial-border;
}

h2 {
  margin-top: 6px;
  font-size: 19px;
  letter-spacing: -.02em;
}

.required-note {
  color: #8a929c;
  font-size: 12px;
}

.identity-content {
  align-items: flex-start;
  justify-content: flex-start;
  gap: 20px;
  padding: 34px 0 26px;
}

.avatar-picker {
  position: relative;
  flex: 0 0 116px;
  width: 116px;
  height: 116px;
  overflow: hidden;
  border: 0;
  border-radius: 0;
  background: $industrial-signal;
  color: #0b0c0a;
  cursor: pointer;
}

.avatar-picker img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initial {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  font-size: 48px;
  font-weight: 700;
}

.avatar-overlay {
  position: absolute;
  inset: auto 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px 4px;
  background: rgba(11, 12, 10, .86);
  font-size: 11px;
  opacity: 0;
  transition: opacity .2s ease;
}

.avatar-picker:hover .avatar-overlay,
.avatar-picker:focus-visible .avatar-overlay {
  opacity: 1;
}

.identity-copy {
  min-width: 0;
  padding-top: 8px;
}

.identity-copy h3 {
  font-size: 24px;
  letter-spacing: -.04em;
}

.identity-copy>p {
  margin-top: 6px;
  color: $industrial-muted;
  font-size: 13px;
}

.identity-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 24px;
  color: $industrial-text;
  font-size: 12px;
}

.meta-dot {
  width: 4px;
  height: 4px;
  border-radius: 0;
  background: $industrial-signal;
}

.upload-note {
  display: flex;
  align-items: center;
  gap: 7px;
  padding-top: 18px;
  border-top: 1px solid $industrial-border;
  color: $industrial-muted;
  font-size: 12px;
}

.upload-note .el-icon {
  color: $industrial-signal;
}

.profile-form {
  padding-top: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.profile-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.profile-form :deep(.el-form-item__label) {
  padding-bottom: 6px;
  color: $industrial-text;
  font-size: 12px;
  line-height: 1;
}

.profile-form :deep(.el-input__wrapper),
.profile-form :deep(.el-select__wrapper) {
  min-height: 40px;
  border-radius: 0;
  box-shadow: 0 0 0 1px $industrial-border inset;
}

.profile-form :deep(.el-input__wrapper.is-focus),
.profile-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px $industrial-signal inset;
}

.readonly-field :deep(.el-input__wrapper) {
  background: $industrial-panel-raised;
}

.form-actions {
  margin-top: 4px;
  padding-top: 20px;
  border-top: 1px solid $industrial-border;
}

.save-hint {
  color: $industrial-muted;
  font-size: 12px;
}

.form-actions :deep(.el-button--primary) {
  min-width: 112px;
  border-radius: 0;
  background: $industrial-signal;
  border-color: $industrial-signal;
}

.security-card {
  margin-top: 16px;
  padding: 22px 26px;
}

.security-copy p:last-child {
  margin-top: 8px;
  color: $industrial-muted;
  font-size: 13px;
}

.security-card :deep(.el-button) {
  border-radius: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .profile-page {
    padding-inline: 0;
  }

  .page-heading {
    align-items: flex-start;
  }

  .heading-index {
    display: none;
  }

  .identity-card,
  .form-card,
  .security-card {
    padding: 20px;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .form-actions,
  .security-card {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
  }
}
</style>
