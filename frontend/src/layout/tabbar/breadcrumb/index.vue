<template>
    <div class="breadcrumb-container">
        <!-- 左侧折叠按钮 -->
        <el-icon class="toggle-icon" :size="20" @click="toggleFold">
            <component :is="LayoutSettingStore.fold ? Fold : Expand" />
        </el-icon>

        <!-- 面包屑导航 -->
        <el-breadcrumb :separator-icon="ArrowRight" class="custom-breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">
                <el-icon>
                    <HomeFilled />
                </el-icon>
                <span>首页</span>
            </el-breadcrumb-item>

            <template v-for="(item, index) in route.matched" :key="index">
                <el-breadcrumb-item v-if="item.meta?.title" :to="item.path">
                    <el-icon v-if="item.meta?.icon" :size="14">
                        <component :is="item.meta.icon" />
                    </el-icon>
                    <span class="title-text">{{ item.meta.title }}</span>
                </el-breadcrumb-item>
            </template>
        </el-breadcrumb>
    </div>
</template>

<script setup lang="ts">
import { ArrowRight, Expand, Fold, HomeFilled } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import useLayoutSettingStore from '@/store/layoutsetting'

defineOptions({
    name: 'Breadcrumb'
})

const route = useRoute()
const LayoutSettingStore = useLayoutSettingStore()

const toggleFold = () => {
    LayoutSettingStore.fold = !LayoutSettingStore.fold
}
</script>

<style scoped lang="scss">
.breadcrumb-container {
    display: flex;
    align-items: center;
    height: 100%;
    width: 100%;


    .toggle-icon {
        margin-right: 10px;
        cursor: pointer;
        flex-shrink: 0;
        color: var(--app-muted);
        transition: all 0.3s;

        &:hover {
            color: $base-hover-color;
        }
    }

    .custom-breadcrumb {
        flex: 1;
        min-width: 0;




        :deep(.el-breadcrumb__item) {
            display: inline-flex;
            align-items: center;

            .el-breadcrumb__inner {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                color: var(--app-muted);

                .el-icon {
                    display: inline-flex;
                    align-items: center;
                    vertical-align: middle;
                    color: var(--app-muted);
                }

                .title-text {
                    vertical-align: middle;
                    color: var(--app-muted);
                }

                &:hover {
                    color: $base-hover-color;
                }
            }
        }

        :deep(.el-breadcrumb__separator) {
            margin: 0 6px;
        }
    }
}
</style>