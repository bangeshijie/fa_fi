<template>
  <div v-if="tabsStore.tabs.length" class="tabs-container">
    <div class="tabs-scroll" role="tablist" aria-label="页面标签">
      <button v-for="tab in tabsStore.tabs" :key="tab.path" type="button" class="tab-item"
        :class="{ active: activeTab === tab.path, affix: tab.affix }" role="tab" :aria-selected="activeTab === tab.path"
        @click="handleTabClick(tab.path)" @contextmenu.stop.prevent="handleContextMenu($event, tab)">
        <el-icon v-if="tab.icon" class="tab-icon">
          <component :is="tab.icon" />
        </el-icon>
        <span class="tab-title">{{ tab.title || tab.name || '未命名' }}</span>
        <el-icon v-if="tab.affix" class="tab-affix-icon" title="固定标签">
          <Flag />
        </el-icon>
        <el-icon v-if="isClosable(tab.path)" class="tab-close" title="关闭"
          @click.stop="handleTabRemove(tab.path, $event)">
          <Close />
        </el-icon>
      </button>
    </div>

    <div class="tabs-actions">
      <el-button text class="action-button" title="刷新当前页面" @click="handleRefreshCurrent">
        <el-icon>
          <Refresh />
        </el-icon>
      </el-button>
      <el-dropdown trigger="click" @command="handleDropdownCommand">
        <el-button text class="action-button" title="标签页操作">
          <el-icon>
            <More />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="refreshCurrent">刷新当前</el-dropdown-item>
            <el-dropdown-item command="refreshAll">刷新所有</el-dropdown-item>
            <el-dropdown-item command="closeAll" divided>关闭所有</el-dropdown-item>
            <el-dropdown-item command="closeOther">关闭其他</el-dropdown-item>
            <el-dropdown-item command="closeRight">关闭右侧</el-dropdown-item>
            <el-dropdown-item command="closeLeft">关闭左侧</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>

  <teleport to="body">
    <div v-if="contextMenuVisible" class="context-menu-overlay" @click="closeContextMenu" />
    <div v-if="contextMenuVisible" class="context-menu" :style="contextMenuStyle" @click.stop @contextmenu.stop.prevent>
      <button type="button" class="context-menu-item" @click="handleContextMenuAction('refresh')">
        <el-icon>
          <Refresh />
        </el-icon><span>刷新</span>
      </button>
      <button type="button" class="context-menu-item" @click="handleContextMenuAction('affix')">
        <el-icon>
          <Flag />
        </el-icon><span>{{ contextMenuTab?.affix ? '取消固定' : '固定' }}</span>
      </button>
      <div class="context-menu-divider" />
      <button type="button" class="context-menu-item" :disabled="!isClosable(contextMenuTab?.path || '')"
        @click="handleContextMenuAction('close')">
        <el-icon>
          <Close />
        </el-icon><span>关闭</span>
      </button>
      <button type="button" class="context-menu-item" @click="handleContextMenuAction('closeOther')">
        <el-icon>
          <Close />
        </el-icon><span>关闭其他</span>
      </button>
      <button type="button" class="context-menu-item" @click="handleContextMenuAction('closeLeft')">
        <el-icon>
          <Close />
        </el-icon><span>关闭左侧</span>
      </button>
      <button type="button" class="context-menu-item" @click="handleContextMenuAction('closeRight')">
        <el-icon>
          <Close />
        </el-icon><span>关闭右侧</span>
      </button>
      <div class="context-menu-divider" />
      <button type="button" class="context-menu-item" @click="handleContextMenuAction('closeAll')">
        <el-icon>
          <Close />
        </el-icon><span>关闭所有</span>
      </button>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, Flag, More, Refresh } from '@element-plus/icons-vue'

import { useTabsStore, type TabItem } from '@/store/tabs'

defineOptions({ name: 'TabsView' })

const tabsStore = useTabsStore()
const router = useRouter()
const route = useRoute()

const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuTab = ref<TabItem | null>(null)

const activeTab = computed(() => tabsStore.activeTab || route.path)
const contextMenuStyle = computed(() => ({
  left: `${contextMenuX.value}px`,
  top: `${contextMenuY.value}px`,
}))

watch(
  () => route.path,
  (newPath) => {
    if (tabsStore.activeTab !== newPath) tabsStore.setActiveTab(newPath)
  },
  { immediate: true },
)

const tabOperations = {
  refreshTab(path: string) {
    tabsStore.refreshTab(path)
  },
  refreshCurrent() {
    tabsStore.refreshCurrentTab()
  },
  refreshAll() {
    tabsStore.refreshAllTabs()
  },
  closeTab(path: string) {
    if (!isClosable(path)) return
    const shouldNavigate = path === route.path
    tabsStore.removeTab(path)
    if (shouldNavigate) router.push(tabsStore.activeTab || '/home')
  },
  closeOther(path = activeTab.value) {
    tabsStore.closeOtherTabs(path)
    if (path !== route.path) router.push(path)
  },
  closeAll() {
    router.push(tabsStore.closeAllTabs() || '/home')
  },
  closeLeft(path = activeTab.value) {
    tabsStore.closeLeft(path)
    if (path !== route.path) router.push(path)
  },
  closeRight(path = activeTab.value) {
    tabsStore.closeRight(path)
    if (path !== route.path) router.push(path)
  },
  toggleAffix(path: string) {
    tabsStore.toggleAffix(path)
  },
}

function handleContextMenu(event: MouseEvent, tab: TabItem) {
  const menuWidth = 188
  const menuHeight = 352
  contextMenuX.value = Math.max(8, Math.min(event.clientX, window.innerWidth - menuWidth - 8))
  contextMenuY.value = Math.max(8, Math.min(event.clientY, window.innerHeight - menuHeight - 8))
  contextMenuTab.value = tab
  contextMenuVisible.value = true
}

function closeContextMenu() {
  contextMenuVisible.value = false
  contextMenuTab.value = null
}

function handleContextMenuAction(action: string) {
  const path = contextMenuTab.value?.path
  if (!path) return

  switch (action) {
    case 'refresh': tabOperations.refreshTab(path); break
    case 'affix': tabOperations.toggleAffix(path); break
    case 'close': tabOperations.closeTab(path); break
    case 'closeOther': tabOperations.closeOther(path); break
    case 'closeLeft': tabOperations.closeLeft(path); break
    case 'closeRight': tabOperations.closeRight(path); break
    case 'closeAll': tabOperations.closeAll(); break
  }
  closeContextMenu()
}

function handleDropdownCommand(command: string | number | object) {
  const commandMap: Record<string, () => void> = {
    refreshCurrent: tabOperations.refreshCurrent,
    refreshAll: tabOperations.refreshAll,
    closeAll: tabOperations.closeAll,
    closeOther: tabOperations.closeOther,
    closeRight: tabOperations.closeRight,
    closeLeft: tabOperations.closeLeft,
  }
  commandMap[String(command)]?.()
}

function handleTabClick(path: string) {
  if (path !== route.path) router.push(path)
}

function handleRefreshCurrent() {
  tabOperations.refreshCurrent()
}

function handleTabRemove(path: string, event: Event) {
  event.stopPropagation()
  tabOperations.closeTab(path)
}

function isClosable(path: string) {
  if (path === '/home') return false
  return !tabsStore.tabs.find((tab) => tab.path === path)?.affix
}

onMounted(() => {
  document.addEventListener('click', closeContextMenu)
  window.addEventListener('resize', closeContextMenu)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeContextMenu)
  window.removeEventListener('resize', closeContextMenu)
})
</script>

<style scoped lang="scss">
.tabs-container {
  display: flex;
  align-items: center;
  min-height: 30px;
  height: 50%;
  padding: 0 14px;
  border-bottom: 1px solid var(--app-border);
  background: var(--app-page-bg);
}

.tabs-scroll {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  gap: 6px;
  overflow-x: auto;
  padding: 3px 0;
  scrollbar-width: thin;
  scrollbar-color: var(--app-border) transparent;
}

.tab-item {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 5px;
  height: 26px;
  max-width: 190px;
  padding: 0 9px;
  border: 1px solid var(--app-border);
  border-radius: 0;
  background: var(--app-surface);
  color: var(--app-muted);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  white-space: nowrap;
  user-select: none;
  transition: color .18s ease, border-color .18s ease, background-color .18s ease;

  &:hover {
    border-color: var(--el-color-primary);
    color: var(--el-color-primary);
    background: var(--app-surface-raised);
  }

  &.active {
    border-color: var(--el-color-primary) !important;
    background: var(--app-surface-raised);
    color: var(--el-color-primary) !important;
    box-shadow: inset 0 -2px 0 var(--el-color-primary);
  }
}

.tab-icon,
.tab-affix-icon,
.tab-close {
  flex: 0 0 auto;
}

.tab-affix-icon {
  color: var(--el-color-primary) !important;
  font-size: 12px;
}

.tab-title {
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-close {
  color: currentColor;
  font-size: 12px;
  opacity: .55;
  transition: opacity .18s ease, transform .18s ease;

  &:hover {
    opacity: 1;
    transform: scale(1.1);
  }
}

.tabs-actions {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 2px;
  margin-left: 10px;
  padding-left: 8px;
  border-left: 1px solid var(--app-border);
}

.action-button {
  width: 28px;
  height: 28px;
  padding: 0 !important;
  border-radius: 0 !important;
  color: var(--el-color-primary) !important;
  transition: transform .18s ease, color .18s ease, background-color .18s ease;

  &:hover {
    background: var(--app-menu-hover) !important;
    color: var(--el-color-primary) !important;
    transform: scale(1.1);
  }
}

.context-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: transparent;
}

.context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 188px;
  padding: 5px 0;
  border: 1px solid var(--app-border);
  border-radius: 0;
  background: var(--app-surface);
  box-shadow: 0 8px 24px rgba(16, 24, 18, .12);
  animation: context-menu-in .12s ease-out;
}

.context-menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 10px;
  padding: 8px 14px;
  border: 0;
  background: transparent;
  color: var(--app-text);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  text-align: left;
  transition: background-color .16s ease, color .16s ease;

  .el-icon {
    color: var(--app-muted);
  }

  &:hover:not(:disabled) {
    background: var(--app-menu-hover);
    color: var(--el-color-primary);

    .el-icon {
      color: var(--el-color-primary);
    }
  }

  &:disabled {
    color: var(--app-muted);
    cursor: not-allowed;
    opacity: .55;
  }
}

.context-menu-divider {
  height: 1px;
  margin: 5px 9px;
  background: var(--app-border);
}

@keyframes context-menu-in {
  from {
    opacity: 0;
    transform: translateY(-3px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
