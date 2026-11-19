<template>
    <section class="admin-page">
        <header class="page-heading">
            <div>
                <div class="heading-title-row">
                    <h2>菜单管理</h2>
                    <p class="eyebrow">SYSTEM / NAVIGATION</p>
                </div>
                <p class="heading-copy">维护系统导航、路由和权限节点。搜索会保留父级路径与下级菜单。</p>
            </div>
            <div class="heading-actions">
                <el-tag type="info" effect="plain">{{ currentClient === 'pc' ? 'PC端' : 'APP端' }}</el-tag>
                <el-button :loading="menuStore.loading" @click="loadData"><el-icon>
                        <Refresh />
                    </el-icon>刷新</el-button>
                <el-button v-permission="'module_system:menu:create'" type="primary" @click="openCreate()"><el-icon>
                        <Plus />
                    </el-icon>新增菜单</el-button>
            </div>
        </header>

        <el-row :gutter="12" class="summary-row">
            <el-col :xs="12" :sm="6"><el-card shadow="never" class="summary-card"><span
                        class="summary-label">当前节点</span><strong>{{ visibleMenus.length }}</strong><small>{{ hasSearch ?
                        '搜索结果节点' : '完整菜单树节点' }}</small></el-card></el-col>
            <el-col :xs="12" :sm="6"><el-card shadow="never" class="summary-card"><span class="summary-label">目录 /
                        菜单</span><strong>{{ routeNodeCount }}</strong><small>可生成导航的节点</small></el-card></el-col>
            <el-col :xs="12" :sm="6"><el-card shadow="never" class="summary-card"><span
                        class="summary-label">权限节点</span><strong>{{ permissionNodeCount
                        }}</strong><small>按钮和操作权限</small></el-card></el-col>
            <el-col :xs="12" :sm="6"><el-card shadow="never" class="summary-card"><span
                        class="summary-label">启用节点</span><strong>{{ enabledCount
                        }}</strong><small>当前结果正常状态</small></el-card></el-col>
        </el-row>

        <el-card shadow="never" class="content-card">
            <template #header>
                <div class="card-heading">
                    <div><span class="section-index">01</span><strong>导航树</strong></div>
                    <div class="heading-tools"><span class="card-note">{{ hasSearch ? '已保留父级路径和下级菜单' : '完整菜单层级'
                            }}</span><el-button text size="small" @click="handleExpandAll">{{ allExpanded ? '全部折叠' :
                            '全部展开' }}</el-button></div>
                </div>
            </template>

            <div class="client-switch">
                <span class="field-label">终端</span>
                <el-radio-group v-model="currentClient" size="small" @change="handleClientChange">
                    <el-radio-button label="pc">PC端</el-radio-button><el-radio-button label="app">APP端</el-radio-button>
                </el-radio-group>
            </div>

            <el-form :inline="true" class="search-bar" @submit.prevent="loadData">
                <el-form-item label="菜单名称"><el-input v-model="menuStore.searchName" clearable placeholder="搜索菜单名称"
                        @keyup.enter="loadData" /></el-form-item>
                <el-form-item label="路由地址"><el-input v-model="menuStore.searchRoutePath" clearable placeholder="搜索路由地址"
                        @keyup.enter="loadData" /></el-form-item>
                <el-form-item label="类型"><el-select v-model="menuStore.searchType" clearable placeholder="全部类型"
                        class="type-field"><el-option label="目录" :value="1" /><el-option label="菜单"
                            :value="2" /><el-option label="权限" :value="3" /><el-option label="外链"
                            :value="4" /></el-select></el-form-item>
                <el-form-item label="状态"><el-select v-model="menuStore.searchStatus" clearable placeholder="全部状态"
                        class="status-field"><el-option value="0" label="启用" /><el-option value="1"
                            label="禁用" /></el-select></el-form-item>
                <el-form-item class="search-actions"><el-button type="primary" @click="loadData"><el-icon>
                            <Search />
                        </el-icon>查询</el-button><el-button @click="handleResetSearch">重置</el-button></el-form-item>
            </el-form>

            <el-table ref="tableRef" v-loading="menuStore.loading" :data="menuStore.menuTree" row-key="id" border
                :default-expand-all="false" :indent="24" :tree-props="{ children: 'children' }" class="menu-table">
                <el-table-column type="index" label="#" width="58" align="center" fixed="left" />
                <el-table-column label="菜单名称" min-width="230" fixed="left"><template #default="{ row }">
                        <div class="menu-name-cell"><el-icon class="menu-icon">
                                <component :is="getIconComponent(row.icon)" />
                            </el-icon><strong>{{ row.name || '未命名菜单' }}</strong><el-tag v-if="row.hidden" type="info"
                                effect="plain" size="small">隐藏</el-tag></div>
                    </template></el-table-column>
                <el-table-column label="上级菜单" min-width="170" show-overflow-tooltip><template #default="{ row }"><el-tag
                            v-if="!row.parent_id" type="info" effect="plain" size="small">顶级菜单</el-tag><span v-else>{{
                                row.parent_name || '未找到上级菜单' }}</span></template></el-table-column>
                <el-table-column label="类型" width="90" align="center"><template #default="{ row }"><el-tag
                            :type="getTypeTag(row.type)" effect="plain" size="small">{{ getTypeName(row.type)
                            }}</el-tag></template></el-table-column>
                <el-table-column label="路由地址" min-width="190" show-overflow-tooltip><template
                        #default="{ row }"><code>{{ row.route_path || '—' }}</code></template></el-table-column>
                <el-table-column label="权限标识" min-width="210" show-overflow-tooltip><template
                        #default="{ row }"><code>{{ row.permission || '—' }}</code></template></el-table-column>
                <el-table-column label="组件路径" min-width="220" show-overflow-tooltip><template
                        #default="{ row }"><code>{{ row.component_path || '—' }}</code></template></el-table-column>
                <el-table-column prop="order" label="排序" width="70" align="center" />
                <el-table-column label="状态" width="100" align="center"><template #default="{ row }"><el-switch
                            v-permission="'module_system:menu:patch'" :model-value="row.status === '0'" inline-prompt
                            active-text="启" inactive-text="禁"
                            @change="(value) => handleStatusChange(row, value)" /><el-tag
                            v-if="!hasPermission('module_system:menu:patch')"
                            :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">{{ row.status
                            === '0' ? '启用' : '禁用' }}</el-tag></template></el-table-column>
                <el-table-column label="选项" width="120" align="center"><template #default="{ row }"><el-tag
                            v-if="row.type === 1 || row.type === 2" :type="row.keep_alive ? 'success' : 'info'"
                            effect="plain" size="small">{{ row.keep_alive ? '缓存' : '不缓存' }}</el-tag><span v-else
                            class="muted">—</span></template></el-table-column>
                <el-table-column label="操作" width="260" fixed="right" align="center"><template
                        #default="{ row }"><el-button v-if="row.type === 1 || row.type === 2"
                            v-permission="'module_system:menu:create'" link type="primary"
                            @click="openCreate(row)">新增子级</el-button><el-button
                            v-permission="'module_system:menu:update'" link type="primary"
                            @click="openEdit(row)">编辑</el-button><el-button v-permission="'module_system:menu:delete'"
                            link type="danger" @click="handleDelete(row)">删除</el-button></template></el-table-column>
            </el-table>
            <el-empty v-if="!menuStore.loading && !menuStore.menuTree.length" description="暂无菜单数据" />
        </el-card>

        <MenuForm v-model="formVisible" :data="currentRow" :parent-id="currentParentId"
            :menu-tree="menuStore.allMenuTree" @submit="handleSubmit" />
    </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { TableInstance, TagProps } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Menu, Plus, Refresh, Search } from '@element-plus/icons-vue'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import MenuForm from './components/MenuForm.vue'
import type { MenuForm as ApiMenuForm, MenuTable } from '@/api/module_system/menu'
import { hasPermission } from '@/directives/permission'
import { useMenuStore } from '@/store/menu'

defineOptions({ name: 'Menu' })

const menuStore = useMenuStore()
const tableRef = ref<TableInstance>()
const formVisible = ref(false)
const currentRow = ref<MenuTable | null>(null)
const currentParentId = ref<number | null>(null)
const allExpanded = ref(true)
const currentClient = computed({
    get: () => menuStore.currentClient,
    set: (value) => { menuStore.currentClient = value as 'pc' | 'app' },
})
const visibleMenus = computed(() => flattenTree(menuStore.menuTree))
const hasSearch = computed(() => Boolean(menuStore.searchName.trim() || menuStore.searchRoutePath.trim() || menuStore.searchType !== undefined || menuStore.searchStatus))
const routeNodeCount = computed(() => visibleMenus.value.filter((row) => row.type === 1 || row.type === 2 || row.type === 4).length)
const permissionNodeCount = computed(() => visibleMenus.value.filter((row) => row.type === 3).length)
const enabledCount = computed(() => visibleMenus.value.filter((row) => row.status === '0').length)

function flattenTree(nodes: MenuTable[], result: MenuTable[] = []) { nodes.forEach((node) => { result.push(node); if (node.children?.length) flattenTree(node.children, result) }); return result }
async function loadData() { try { await menuStore.refreshMenuData() } catch (error) { console.error('获取菜单失败:', error); ElMessage.error('获取菜单失败') } }
async function handleResetSearch() { menuStore.clearMenuManagementState(); await loadData() }
async function handleClientChange(value: string | number | boolean | undefined) { if (value === 'pc' || value === 'app') await menuStore.setClient(value) }
function handleExpandAll() { const table = tableRef.value; if (!table) return; flattenTree(menuStore.menuTree).forEach((row) => table.toggleRowExpansion(row, !allExpanded.value)); allExpanded.value = !allExpanded.value }
function openCreate(parent?: MenuTable) { currentRow.value = null; currentParentId.value = parent?.id ?? null; formVisible.value = true }
function openEdit(row: MenuTable) { currentRow.value = { ...row }; currentParentId.value = row.parent_id ?? null; formVisible.value = true }
async function handleSubmit(form: ApiMenuForm) { try { if (currentRow.value?.id) { await menuStore.updateMenu(currentRow.value.id, form); ElMessage.success('菜单修改成功') } else { await menuStore.createMenu(form); ElMessage.success('菜单创建成功') }; formVisible.value = false; currentRow.value = null; currentParentId.value = null } catch (error) { console.error('保存菜单失败:', error); ElMessage.error('保存菜单失败') } }
function countChildren(row: MenuTable) { return flattenTree(row.children || []).length }
async function handleDelete(row: MenuTable) { if (!row.id) return; const count = countChildren(row); const message = count ? `菜单“${row.name}”下面还有 ${count} 个下级节点，确定继续删除吗？` : `确定删除菜单“${row.name}”吗？`; try { await ElMessageBox.confirm(message, '删除菜单', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }); await menuStore.deleteMenu([row.id]); ElMessage.success('菜单已删除') } catch (error: any) { if (error === 'cancel' || error === 'close') return; console.error('删除菜单失败:', error); ElMessage.error('删除菜单失败') } }
async function handleStatusChange(row: MenuTable, value: string | number | boolean) { const enabled = Boolean(value); try { await menuStore.updateMenuStatus(row, enabled ? '0' : '1'); ElMessage.success(enabled ? '菜单已启用' : '菜单已禁用') } catch (error) { console.error('修改菜单状态失败:', error); ElMessage.error('修改菜单状态失败'); await loadData() } }
function getTypeName(type?: number) { return ({ 1: '目录', 2: '菜单', 3: '权限', 4: '外链' } as Record<number, string>)[type || 0] || '未知' }
function getTypeTag(type?: number): TagProps['type'] { return ({ 1: 'warning', 2: 'primary', 3: 'success', 4: 'info' } as Record<number, TagProps['type']>)[type || 0] }
function getIconComponent(name?: string) { if (!name) return Menu; return (ElementPlusIconsVue as Record<string, unknown>)[name] || Menu }

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
.heading-tools,
.client-switch {
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

.heading-copy,
.card-note,
.muted {
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

.card-heading>div:first-child {
    display: flex;
    align-items: center;
    gap: 10px;
}

.heading-tools {
    gap: 12px;
}

.client-switch {
    gap: 12px;
    margin-bottom: 12px;
}

.field-label {
    color: var(--app-muted);
    font-size: 12px;
}

.search-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0 12px;
    margin-bottom: 4px;
}

.type-field,
.status-field {
    width: 112px;
}

.menu-name-cell {
    display: inline-flex;
    gap: 8px;
    min-width: 0;
    min-height: 20px;
    height: 20px;
    line-height: 20px;
    vertical-align: middle;
}

.menu-name-cell strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.menu-icon {
    flex: 0 0 auto;
    color: var(--el-color-primary);
    font-size: 15px;
}

code {
    color: var(--el-color-primary);
    font-family: var(--app-mono);
    font-size: 12px;
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

.menu-name-cell :deep(.el-tag) {
    height: 20px;
    line-height: 18px;
}

@media (max-width: 760px) {
    .page-heading {
        align-items: flex-start;
        flex-direction: column;
    }

    .heading-actions {
        justify-content: flex-start;
    }
}
</style>
