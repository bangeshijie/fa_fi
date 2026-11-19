<template>

  <!-- ====== 头部区域 ====== -->
  <header class="home-header">
    <div class="home-header__left">

      <h2>{{ greetings() }} {{ displayName }}</h2>
      <p>
        <el-icon>
          <Check />
        </el-icon>
        当前账号可访问 <strong>{{ accessiblePageCount }}</strong> 个页面，工作区状态正常。
      </p>
    </div>
    <div class="home-header__right">
      <div class="home-date">
        <span>今日日期</span>
        <strong>{{ currentDate }}</strong>
      </div>
      <div class="home-status">
        <span class="home-status__indicator"></span>
        <span>系统运行中</span>
      </div>
    </div>
  </header>

  <!-- ====== 核心卡片 ====== -->
  <el-row :gutter="16" class="home-row">
    <el-col :xs="24" :lg="15">
      <el-card class="hero-card" shadow="never">
        <div class="hero-card__top">
          <span class="hero-card__label">
            <el-icon>
              <Monitor />
            </el-icon>
            运营工作台
          </span>
          <el-tag type="success" effect="plain" size="small">● 在线</el-tag>
        </div>
        <h2>
          引导信息<br />
        </h2>
        <p>从左侧导航进入销售、报表和基础数据模块；从右上角打开个人中心，维护账户资料和头像。</p>

      </el-card>
    </el-col>

    <el-col :xs="24" :lg="9">
      <el-card class="account-card" shadow="never">
        <template #header>
          <div class="card-heading">
            <span><el-icon>
                <UserFilled />
              </el-icon> 账户概览</span>

          </div>
        </template>
        <div class="account-row">
          <el-avatar :size="48" :src="resolveAssetUrl(authStore.info.avatar)" class="account-avatar">
            {{ initials }}
          </el-avatar>
          <div class="account-row__body">
            <strong>{{ displayName }}</strong>
            <span>{{ authStore.info.username || '—' }}</span>
          </div>
          <el-button link type="primary" @click="goProfile">查看资料 →</el-button>
        </div>
        <el-descriptions :column="2" size="small" class="account-details" border>
          <el-descriptions-item label="部门">
            <el-icon>
              <OfficeBuilding />
            </el-icon>
            {{ authStore.info.dept?.name || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-icon>
              <Stamp />
            </el-icon>
            <template v-if="authStore.info.roles?.length">
              <template v-for="(role, index) in authStore.info.roles" :key="role.id">
                <span v-if="index > 0">、</span>{{ role.name }}
              </template>
            </template>
            <span v-else>—</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </el-col>
  </el-row>

  <!-- ====== 指标卡片 ====== -->
  <el-row :gutter="16" class="home-row">
    <el-col v-for="metric in metrics" :key="metric.label" :xs="12" :md="6">
      <el-card class="metric-card" shadow="never">
        <div class="metric-card__icon">{{ metric.icon }}</div>
        <span class="metric-card__label">{{ metric.label }}</span>
        <el-statistic v-if="typeof metric.value === 'number'" :value="metric.value"
          :value-style="{ color: 'var(--el-text-color-primary)' }" />
        <strong v-else class="metric-value">{{ metric.value }}</strong>
        <small class="metric-card__note">{{ metric.note }}</small>
      </el-card>
    </el-col>
  </el-row>




</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { greetings, resolveAssetUrl } from '@/utils'
import type { AppRouteRecord } from '@/types/router'

defineOptions({ name: 'Home' })

const router = useRouter()
const authStore = useAuthStore()

// ====== 计算属性 ======
const displayName = computed(() => authStore.info.name || authStore.info.username || '用户')
const initials = computed(() => displayName.value.slice(0, 1).toUpperCase())

const currentDate = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
}).format(new Date()).replace(/\//g, '.')

// ====== 路由相关 ======
function flattenRoutes(routes: AppRouteRecord[], target: AppRouteRecord[] = []) {
  routes.forEach((route) => {
    if (route.children?.length) flattenRoutes(route.children, target)
    else if (route.path !== '/home' && !route.meta?.hidden && route.meta?.title) {
      target.push(route)
    }
  })
  return target
}

const accessiblePages = computed(() => flattenRoutes(authStore.routeList))
const accessiblePageCount = computed(() => accessiblePages.value.length)



// ====== 指标数据 ======
const metrics = computed(() => [
  { label: '当前会话', value: '在线', note: '访问状态', icon: '🔵' },
  { label: '可访问页面', value: accessiblePageCount.value, note: '按当前权限', icon: '📄' },
  { label: '当前角色', value: authStore.info.roles?.length || 0, note: '账号角色数', icon: '🎯' },
  {
    label: '最近登录',
    value: authStore.info.last_login ? String(authStore.info.last_login).slice(0, 10) : '—',
    note: '系统记录',
    icon: '🕐',
  },
])

// ====== 方法 ======
function goProfile() { router.push('/profile') }

</script>

<style scoped lang="scss">
// ============================================================
//  头部
// ============================================================
.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 16px 0 24px;
  border-bottom: 1px solid $industrial-border;

  &__left {
    flex: 1;
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 24px;
    padding-left: 24px;
    border-left: 1px solid $industrial-border;
  }
}



@keyframes pulse-dot {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.3;
    transform: scale(0.7);
  }
}

.home-header p {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  color: $industrial-muted;
  font-size: 13px;

  strong {
    color: $industrial-signal;
    font-weight: 600;
  }
}

.home-date {
  text-align: right;

  span {
    display: block;
    color: $industrial-muted;
    font-size: 11px;
    letter-spacing: 0.04em;
  }

  strong {
    display: block;
    margin-top: 4px;
    font-size: 16px;
    font-weight: 500;
  }
}

.home-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 100px;
  background: rgba(198, 255, 74, 0.08);
  color: $industrial-signal;
  font-size: 12px;

  &__indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: $industrial-signal;
    animation: pulse-dot 1.8s ease-in-out infinite;
  }
}

// ============================================================
//  3. 通用卡片样式
// ============================================================
.home-row {
  margin: 16px 0;

  .el-col {
    display: flex;

    .el-card {
      width: 100%;
      display: flex;
      flex-direction: column;

      :deep(.el-card__body) {
        flex: 1;
      }
    }
  }
}

.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 600;

  .el-icon {
    margin-right: 6px;
  }
}

.card-code {
  color: $industrial-signal;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
}


// ============================================================
//  5. 账户卡片
// ============================================================
.account-card {
  .account-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 10px 0 20px;
    border-bottom: 1px solid $industrial-border;
  }

  .account-avatar {
    background: rgba(198, 255, 74, 0.15);
    color: $industrial-signal;
    font-weight: 600;
  }

  .account-row__body {
    flex: 1;
    min-width: 0;

    strong {
      display: block;
      font-size: 15px;
    }

    span {
      display: block;
      margin-top: 2px;
      color: $industrial-muted;
      font-size: 12px;
    }
  }

  .account-details {
    margin-top: 16px;

    :deep(.el-descriptions__label) {
      display: flex;
      align-items: center;
      gap: 4px;
      color: $industrial-muted;
      font-weight: 400;
    }
  }
}

// ============================================================
//  6. 指标卡片
// ============================================================
.metric-card {
  min-height: 120px;
  transition: border-color 0.2s;

  &:hover {
    border-color: $industrial-signal;
  }

  &__icon {
    font-size: 20px;
    line-height: 1;
  }

  &__label {
    display: block;
    margin-top: 10px;
    color: $industrial-muted;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  &__note {
    display: block;
    margin-top: 2px;
    color: rgba($industrial-muted, 0.5);
    font-size: 11px;
  }

  :deep(.el-statistic) {
    margin: 8px 0 2px;

    .el-statistic__content {
      font-size: 26px;
      font-weight: 600;
    }
  }

  .metric-value {
    display: block;
    margin: 8px 0 2px;
    font-size: 26px;
    font-weight: 600;
  }
}


// ============================================================

// ============================================================
//  10. 响应式
// ============================================================
@media (max-width: 820px) {
  .home-header {
    flex-direction: column;
    align-items: flex-start;

    &__right {
      width: 100%;
      padding-left: 0;
      border-left: 0;
      padding-top: 12px;
      border-top: 1px solid $industrial-border;
      justify-content: space-between;
    }
  }

  .notice-card :deep(.el-card__body) {
    flex-direction: column;
    align-items: flex-start;
  }

  .notice-card__content {
    white-space: normal;
  }
}

@media (max-width: 480px) {
  .home-header__right {
    flex-wrap: wrap;
    gap: 8px;
  }

  .home-status {
    font-size: 11px;
    padding: 4px 12px;
  }

  .home-date strong {
    font-size: 14px;
  }
}
</style>
