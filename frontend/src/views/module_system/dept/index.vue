<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">SYSTEM / ORGANIZATION</p>
        <h1>部门管理</h1>
        <p class="heading-copy">维护组织层级、部门负责人和数据权限范围。搜索会保留父级路径与全部子部门。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">组织架构</el-tag>
        <el-button :loading="deptStore.loading" @click="loadData">
          <el-icon>
            <Refresh />
          </el-icon>刷新
        </el-button>
        <el-button v-permission="'module_system:dept:create'" type="primary" @click="openCreate()">
          <el-icon>
            <Plus />
          </el-icon>新增部门
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">当前部门</span>
          <strong>{{ visibleDepartments.length }}</strong>
          <small>{{ hasSearch ? '搜索结果节点' : '完整组织树节点' }}</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">顶级部门</span>
          <strong>{{ deptStore.deptTree.length }}</strong>
          <small>当前结果根节点</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">启用部门</span>
          <strong>{{ enabledCount }}</strong>
          <small>当前结果正常状态</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">下级部门</span>
          <strong>{{ childCount }}</strong>
          <small>当前结果非根节点</small>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div><span class="section-index">01</span><strong>组织树</strong></div>
          <span class="card-note">{{ hasSearch ? '已保留父级路径和子部门' : '完整部门层级' }}</span>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="loadData">
        <el-form-item label="部门名称">
          <el-input v-model="deptStore.searchName" clearable placeholder="搜索部门名称" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="deptStore.searchStatus" clearable placeholder="全部状态" class="status-field">
            <el-option value="0" label="启用" />
            <el-option value="1" label="禁用" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker v-model="deptStore.searchCreatedTime" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="开始时间" end-placeholder="结束时间" range-separator="至" class="date-field" />
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="loadData"><el-icon>
              <Search />
            </el-icon>查询</el-button>
          <el-button @click="handleResetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="deptStore.loading" :data="deptStore.deptTree" border stripe row-key="id"
        :default-expand-all="false" :indent="24" :tree-props="{ children: 'children' }" class="dept-table">
        <el-table-column type="index" label="#" width="58" align="center" fixed="left" />
        <el-table-column label="部门名称" min-width="220" fixed="left">
          <template #default="{ row }">
            <div class="dept-name-cell">
              <el-icon class="dept-icon">
                <OfficeBuilding />
              </el-icon>
              <strong>{{ row.name || '未命名部门' }}</strong>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="上级部门" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag v-if="!row.parent_id" type="info" effect="plain" size="small">顶级部门</el-tag>
            <span v-else>{{ row.parent_name || parentName(row.parent_id) || '未找到上级部门' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="部门编码" min-width="150" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.code || '—' }}</code></template>
        </el-table-column>
        <el-table-column prop="leader" label="负责人" width="120" show-overflow-tooltip />
        <el-table-column prop="phone" label="联系电话" width="140" show-overflow-tooltip />
        <el-table-column prop="email" label="邮箱" min-width="190" show-overflow-tooltip />
        <el-table-column prop="order" label="排序" width="76" align="center" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch v-permission="'module_system:dept:patch'" :model-value="row.status === '0'" inline-prompt
              active-text="启" inactive-text="禁" @change="(value) => handleStatusChange(row, value)" />
            <el-tag v-if="!hasPermission('module_system:dept:patch')" :type="row.status === '0' ? 'success' : 'danger'"
              effect="plain" size="small">{{ row.status === '0' ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" width="178" show-overflow-tooltip />
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_system:dept:create'" link type="primary"
              @click="openCreate(row)">新增子级</el-button>
            <el-button v-permission="'module_system:dept:update'" link type="primary"
              @click="openEdit(row)">编辑</el-button>
            <el-button v-permission="'module_system:dept:delete'" link type="danger"
              @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!deptStore.loading && !deptStore.deptTree.length" description="暂无部门数据" />
    </el-card>

    <DeptForm v-model="formVisible" :data="currentRow" :parent-id="currentParentId" :dept-tree="deptStore.allDeptTree"
      @submit="handleSubmit" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { OfficeBuilding, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import DeptForm from './components/DeptForm.vue'
import type { DeptForm as ApiDeptForm, DeptTable } from '@/api/module_system/dept'
import { hasPermission } from '@/directives/permission'
import { useDeptStore } from '@/store/dept'

defineOptions({ name: 'Dept' })

const deptStore = useDeptStore()
const formVisible = ref(false)
const currentRow = ref<DeptTable | null>(null)
const currentParentId = ref<number | null>(null)

const hasSearch = computed(() => Boolean(deptStore.searchName.trim() || deptStore.searchStatus || deptStore.searchCreatedTime.length))
const visibleDepartments = computed(() => flattenTree(deptStore.deptTree))
const enabledCount = computed(() => visibleDepartments.value.filter((row) => row.status === '0').length)
const childCount = computed(() => visibleDepartments.value.filter((row) => row.parent_id).length)
const parentNameMap = computed(() => {
  const map = new Map<number, string>()
  flattenTree(deptStore.allDeptTree).forEach((row) => { if (row.id && row.name) map.set(row.id, row.name) })
  return map
})

function flattenTree(nodes: DeptTable[], result: DeptTable[] = []) {
  nodes.forEach((node) => {
    result.push(node)
    if (node.children?.length) flattenTree(node.children, result)
  })
  return result
}

function parentName(parentId?: number | null) {
  return parentId ? parentNameMap.value.get(parentId) : undefined
}

async function loadData() {
  try {
    await deptStore.refreshDeptData()
  } catch (error) {
    console.error('获取部门失败:', error)
    ElMessage.error('获取部门失败')
  }
}

async function handleResetSearch() {
  deptStore.resetSearch()
  await loadData()
}

function openCreate(parent?: DeptTable) {
  currentRow.value = null
  currentParentId.value = parent?.id ?? null
  formVisible.value = true
}

function openEdit(row: DeptTable) {
  currentRow.value = { ...row }
  currentParentId.value = row.parent_id ?? null
  formVisible.value = true
}

async function handleSubmit(form: ApiDeptForm) {
  try {
    if (currentRow.value?.id) {
      await deptStore.updateDept(currentRow.value.id, form)
      ElMessage.success('部门修改成功')
    } else {
      await deptStore.createDept(form)
      ElMessage.success('部门创建成功')
    }
    formVisible.value = false
    currentRow.value = null
    currentParentId.value = null
  } catch (error) {
    console.error('保存部门失败:', error)
    ElMessage.error('保存部门失败')
  }
}

function countChildren(row: DeptTable) {
  return flattenTree(row.children || []).length
}

async function handleDelete(row: DeptTable) {
  if (!row.id) return
  const descendantCount = countChildren(row)
  const message = descendantCount
    ? `部门“${row.name}”下面还有 ${descendantCount} 个子部门，删除后所有子部门也会被删除，确定继续吗？`
    : `确定删除部门“${row.name}”吗？`
  try {
    await ElMessageBox.confirm(message, '删除部门', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' })
    await deptStore.deleteDept([row.id])
    ElMessage.success('部门已删除')
  } catch (error: any) {
    if (error === 'cancel' || error === 'close') return
    console.error('删除部门失败:', error)
    ElMessage.error('删除部门失败')
  }
}

async function handleStatusChange(row: DeptTable, value: string | number | boolean) {
  if (!row.id) return
  const status = Boolean(value) ? '0' : '1'
  try {
    await deptStore.updateDeptStatus([row.id], status)
    ElMessage.success(Boolean(value) ? '部门已启用' : '部门已禁用')
  } catch (error) {
    console.error('修改部门状态失败:', error)
    ElMessage.error('修改部门状态失败')
    await loadData()
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.admin-page {
  min-height: 100%;
  padding: 14px 4px 36px;
  color: var(--app-text);
}

.page-heading,
.card-heading,
.heading-actions,
.pagination-row {
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
.card-note {
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

.card-heading>div {
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

.status-field {
  width: 116px;
}

.date-field {
  width: 350px;
}

.dept-name-cell {
  display: inline-flex;
  gap: 9px;
  min-width: 0;
  min-height: 20px;
  height: 20px;
  line-height: 20px;
  vertical-align: middle;
}

.dept-icon {
  flex: 0 0 auto;
  color: var(--el-color-primary);
  font-size: 15px;
}

:deep(.el-table__body .el-table__cell) {
  padding: 4px 0;
}

:deep(.el-table__body .cell) {
  line-height: 20px;
  white-space: nowrap;
}

:deep(.el-table__expand-icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 20px;
  margin-right: 3px;
  vertical-align: middle;
}

:deep(.el-table__indent) {
  display: inline-block;
  height: 20px;
  vertical-align: middle;
}

code {
  color: var(--el-color-primary);
  font-family: var(--app-mono);
  font-size: 12px;
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

  .date-field {
    width: min(350px, 100%);
  }
}
</style>
