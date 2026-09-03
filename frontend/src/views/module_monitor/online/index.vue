<template>
  <section class="online-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">MONITOR / ONLINE</p>
        <h1>在线用户</h1>
        <p class="heading-copy">查看当前 Redis 会话，支持按账号、IP 和登录位置筛选。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="success" effect="plain">实时会话</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button v-permission="'module_monitor:online:delete'" type="danger" plain :disabled="!total"
          @click="handleClear">
          <el-icon><Delete /></el-icon>
          清除全部
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">在线会话</span>
          <strong>{{ total }}</strong>
          <small>Redis 当前记录</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">当前页用户</span>
          <strong>{{ rows.length }}</strong>
          <small>当前分页结果</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">管理账号</span>
          <strong>{{ adminCount }}</strong>
          <small>当前页超级管理员</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">移动端</span>
          <strong>{{ mobileCount }}</strong>
          <small>当前页移动登录</small>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div>
            <span class="section-index">01</span>
            <strong>会话列表</strong>
          </div>
          <span class="card-note">{{ lastUpdated ? `更新于 ${lastUpdated}` : '尚未刷新' }}</span>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="用户">
          <el-input v-model="query.name" clearable placeholder="姓名或用户名" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="IP 地址">
          <el-input v-model="query.ipaddr" clearable placeholder="请输入 IP" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="登录位置">
          <el-input v-model="query.login_location" clearable placeholder="请输入位置" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border stripe class="online-table" row-key="session_id">
        <el-table-column label="用户" min-width="180" fixed="left">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="30" :src="resolveAssetUrl(row.avatar) || undefined" class="user-avatar">
                {{ (row.name || row.user_name || '用').slice(0, 1) }}
              </el-avatar>
              <div>
                <strong>{{ row.name || '—' }}</strong>
                <span>{{ row.user_name || '—' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="端类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.login_type === '移动端' ? 'warning' : 'primary'" effect="plain" size="small">
              {{ row.login_type || 'PC端' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_super_admin" type="danger" effect="plain" size="small">超级管理员</el-tag>
            <span v-else class="muted-text">普通用户</span>
          </template>
        </el-table-column>
        <el-table-column prop="ipaddr" label="IP 地址" min-width="145" show-overflow-tooltip />
        <el-table-column prop="login_location" label="登录位置" min-width="140" show-overflow-tooltip />
        <el-table-column label="设备" min-width="190" show-overflow-tooltip>
          <template #default="{ row }">
            {{ [row.os, row.browser].filter(Boolean).join(' / ') || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="login_time" label="登录时间" width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_monitor:online:delete'" link type="danger" @click="handleKick(row)">
              强制下线
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import OnlineAPI, { type OnlinePageQuery, type OnlineUser } from '@/api/module_monitor/online'
import { useAsyncLoading, usePolling } from '@/hooks'
import { resolveAssetUrl } from '@/utils'

defineOptions({ name: 'MonitorOnline' })

const rows = ref<OnlineUser[]>([])
const total = ref(0)
const lastUpdated = ref('')
const { loading, run } = useAsyncLoading()
const query = reactive<OnlinePageQuery>({
  page_no: 1,
  page_size: 10,
})

const adminCount = computed(() => rows.value.filter((row) => row.is_super_admin).length)
const mobileCount = computed(() => rows.value.filter((row) => row.login_type === '移动端').length)

async function loadData() {
  await run(async () => {
    const response = await OnlineAPI.listOnline({ ...query })
    const result = response.data.data
    rows.value = result?.items || []
    total.value = result?.total || 0
    lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  })
}

function handleSearch() {
  query.page_no = 1
  return loadData()
}

function handleReset() {
  query.name = undefined
  query.ipaddr = undefined
  query.login_location = undefined
  query.page_no = 1
  return loadData()
}

async function handleKick(row: OnlineUser) {
  await ElMessageBox.confirm(`确定要让 ${row.name || row.user_name} 下线吗？`, '强制下线', {
    type: 'warning',
    confirmButtonText: '确定下线',
    cancelButtonText: '取消',
  })
  await OnlineAPI.deleteOnline(row.session_id)
  ElMessage.success('已强制下线')
  await loadData()
}

async function handleClear() {
  await ElMessageBox.confirm('这会清除所有在线会话，确定继续吗？', '清除全部在线用户', {
    type: 'warning',
    confirmButtonText: '确定清除',
    cancelButtonText: '取消',
  })
  await OnlineAPI.clearOnline()
  ElMessage.success('在线会话已清除')
  await loadData()
}

const { start: startRefresh } = usePolling(loadData, { interval: 30_000 })
onMounted(() => {
  void loadData()
  startRefresh()
})
</script>

<style scoped lang="scss">
.online-page {
  min-height: 100%;
  padding: 14px 4px 36px;
  color: var(--app-text);
}

.page-heading,
.card-heading,
.heading-actions,
.pagination-row,
.user-cell {
  display: flex;
  align-items: center;
}

.page-heading {
  justify-content: space-between;
  gap: 24px;
  padding: 6px 0 24px;
  border-bottom: 1px solid var(--app-border);
}

.eyebrow,
.section-index {
  margin: 0;
  color: var(--el-color-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
}

h1 {
  margin: 8px 0 0;
  font-size: clamp(28px, 4vw, 46px);
  letter-spacing: -.045em;
  line-height: 1;
}

.heading-copy,
.card-note,
.muted-text {
  color: var(--app-muted);
}

.heading-copy {
  margin: 12px 0 0;
  font-size: 13px;
}

.heading-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.summary-row {
  margin: 16px 0;
}

.summary-card {
  min-height: 112px;
}

.summary-label,
.summary-card small {
  display: block;
  color: var(--app-muted);
}

.summary-label {
  font-size: 12px;
}

.summary-card strong {
  display: block;
  margin: 8px 0 4px;
  color: var(--el-color-primary);
  font-size: 30px;
  line-height: 1;
}

.summary-card small {
  font-size: 11px;
}

.content-card {
  margin-top: 16px;
}

.card-heading {
  justify-content: space-between;
  gap: 16px;
}

.card-heading > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0 12px;
  margin-bottom: 4px;
}

.user-cell {
  gap: 10px;
}

.user-cell > div {
  display: grid;
  gap: 3px;
}

.user-cell span {
  color: var(--app-muted);
  font-size: 12px;
}

.user-avatar {
  flex: 0 0 auto;
  background: var(--el-color-primary);
  color: var(--el-bg-color);
}

.pagination-row {
  justify-content: flex-end;
  padding-top: 16px;
}

@media (max-width: 760px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .heading-actions {
    justify-content: flex-start;
  }

  .online-table {
    width: 100%;
  }
}
</style>
