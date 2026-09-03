<template>
    <el-popover v-model:visible="visible" placement="bottom-start" :width="420" trigger="click">
        <template #reference>
            <el-input :model-value="modelValue" readonly placeholder="请选择图标" clearable @clear="handleClear">
                <template #prefix>
                    <el-icon v-if="currentIcon">
                        <component :is="currentIcon" />
                    </el-icon>
                </template>

                <template #suffix>
                    <el-icon>
                        <ArrowDown />
                    </el-icon>
                </template>
            </el-input>
        </template>

        <div class="icon-select">
            <el-input v-model="keyword" clearable placeholder="搜索图标，例如：user / menu / setting" class="icon-search">
                <template #prefix>
                    <el-icon>
                        <Search />
                    </el-icon>
                </template>
            </el-input>

            <el-scrollbar height="300px">
                <div class="icon-grid">
                    <div v-for="icon in filteredIcons" :key="icon.name" class="icon-item" :class="{
                        active: modelValue === icon.name,
                    }" @click="handleSelect(icon.name)">
                        <el-icon :size="22">
                            <component :is="icon.component" />
                        </el-icon>

                        <span>
                            {{ icon.name }}
                        </span>
                    </div>
                </div>
            </el-scrollbar>
        </div>
    </el-popover>
</template>

<script setup lang="ts">
import {
    computed,
    ref,
} from "vue";

import * as ElementPlusIconsVue from "@element-plus/icons-vue";

import {
    ArrowDown,
    Search,
} from "@element-plus/icons-vue";

const props = defineProps<{
    modelValue?: string;
}>();

const emit = defineEmits<{
    (
        e: "update:modelValue",
        value: string
    ): void;

    (
        e: "change",
        value: string
    ): void;
}>();

const visible = ref(false);

const keyword = ref("");

/**
 * Element Plus 全部图标
 */
const allIcons = Object.entries(
    ElementPlusIconsVue
)
    .filter(
        ([name, component]) =>
            name !== "ArrowDown" &&
            name !== "Search" &&
            !!component
    )
    .map(
        ([name, component]) => ({
            name,
            component,
        })
    );

/**
 * 搜索过滤
 */
const filteredIcons = computed(() => {
    const text =
        keyword.value
            .trim()
            .toLowerCase();

    if (!text) {
        return allIcons;
    }

    return allIcons.filter(
        item =>
            item.name
                .toLowerCase()
                .includes(text)
    );
});

/**
 * 当前图标组件
 */
const currentIcon = computed(() => {
    if (!props.modelValue) {
        return undefined;
    }

    return (
        ElementPlusIconsVue as Record<
            string,
            unknown
        >
    )[props.modelValue];
});

/**
 * 选择图标
 */
function handleSelect(
    name: string
) {
    emit(
        "update:modelValue",
        name
    );

    emit(
        "change",
        name
    );

    visible.value = false;
}

/**
 * 清空
 */
function handleClear() {
    emit(
        "update:modelValue",
        ""
    );

    emit(
        "change",
        ""
    );
}
</script>

<style scoped lang="scss">
.icon-select {
    width: 100%;
}

.icon-search {
    margin-bottom: 12px;
}

.icon-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
    padding: 4px;
}

.icon-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    height: 70px;

    border: 1px solid transparent;
    border-radius: 6px;

    cursor: pointer;

    transition:
        background-color 0.15s,
        border-color 0.15s;

    &:hover {
        background-color: var(--el-fill-color-light);
    }

    &.active {
        border-color: var(--el-color-primary);
        background-color: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
    }

    span {
        width: 100%;
        margin-top: 6px;

        overflow: hidden;

        text-align: center;
        text-overflow: ellipsis;
        white-space: nowrap;

        font-size: 12px;
    }
}
</style>