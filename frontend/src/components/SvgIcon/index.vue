<template>
  <svg class="svg-icon" :style="{ width, height }">
    <use :xlink:href="prefix + name" :fill="color"></use>
  </svg>
</template>

<script setup lang="ts">
defineOptions({
  name: 'SvgIcon'
})

const {
  name,
  prefix = '#icon-',
  color = '',
  width = '16px',
  height = '16px'
} = defineProps<{
  name: string
  prefix?: string
  color?: string
  width?: string
  height?: string
}>()
</script>

<style lang="scss" scoped>
.svg-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  vertical-align: middle;

  // 默认继承父级颜色
  fill: currentColor;
}
</style>