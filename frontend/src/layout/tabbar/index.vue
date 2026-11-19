<!-- layout/tabbar/index.vue -->
<script setup lang="ts">
import Breadcrumb from './breadcrumb/index.vue'
import Setting from './setting/index.vue'
import TabsView from './tabview/index.vue'

defineOptions({
    name: 'Tabbar'
})
</script>

<template>
    <div class="tabbar-wrapper">
        <div class="tabbar">
            <!-- 顶部左边 -->
            <div class="tabbar_left">
                <!-- 顶部左边面包屑 -->
                <Breadcrumb />
            </div>

            <!-- 顶部右边 -->
            <div class="tabbar_right">
                <Setting />
            </div>
        </div>

        <!-- 标签页组件 -->
        <TabsView />
    </div>
</template>

<style scoped lang="scss">
.tabbar-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.tabbar {
    width: 100%;
    height: 70%;
    display: flex;
    justify-content: space-between;
    flex-shrink: 0;

}

.tabbar_left {
    display: flex;
    align-items: center;
    margin-left: 20px;
}

.tabbar_right {
    display: flex;
    align-items: center;
}
</style>