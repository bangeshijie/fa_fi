<!-- src/views/error/NotFoundLayout.vue -->
<template>


    <!-- 主体 -->
    <div class="error-body">
        <div class="error-container">
            <!-- 左侧 404 数字 -->
            <div class="error-number">
                <span class="digit">4</span>
                <span class="digit zero">
                    <el-icon :size="100" color="#409EFF">
                        <WarningFilled />
                    </el-icon>
                </span>
                <span class="digit">4</span>
            </div>

            <!-- 右侧信息 -->
            <div class="error-message">
                <h2>哎呀！页面走丢了</h2>
                <p>
                    您访问的页面不存在，请确认网址是否正确。
                    <br />
                    如需帮助，请联系系统管理员。
                </p>

                <div class="actions">
                    <el-button type="primary" size="large" @click="goHome">
                        <el-icon>
                            <HomeFilled />
                        </el-icon>
                        返回首页
                    </el-button>
                    <el-button size="large" @click="goBack">
                        <el-icon>
                            <Back />
                        </el-icon>
                        返回上一页
                    </el-button>
                </div>

                <!-- 快捷链接 -->
                <div class="quick-links">
                    <el-text type="info" size="small">快速导航：</el-text>
                    <el-link type="primary" never>帮助中心</el-link>
                    <el-divider direction="vertical" />
                    <el-link type="primary" never>技术支持</el-link>
                    <el-divider direction="vertical" />
                    <el-link type="primary" never>意见反馈</el-link>
                </div>
            </div>
        </div>
    </div>



</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { WarningFilled, HomeFilled, Back } from '@element-plus/icons-vue'

defineOptions({
    name: 'NotFoundLayout'
})

const router = useRouter()

const goHome = () => router.push('/')
const goBack = () => router.back()
</script>

<style scoped lang="scss">
.error-body {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 240px;
}

.error-container {
    display: flex;
    align-items: center;
    gap: 80px;
    max-width: 1200px;
    width: 100%;
}

.error-number {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-shrink: 0;

    .digit {
        font-size: 160px;
        font-weight: 700;
        line-height: 1;
        color: var(--el-color-primary);
        opacity: 0.8;

        &.zero {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 140px;
            height: 140px;
            background: rgba(64, 158, 255, 0.08);
            border-radius: 50%;
            border: 4px solid rgba(64, 158, 255, 0.15);
        }
    }
}

.error-message {
    flex: 1;

    h2 {
        font-size: 36px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 16px 0;
    }

    p {
        font-size: 16px;
        line-height: 1.8;
        color: var(--el-text-color-secondary);
        margin: 0 0 32px 0;
    }

    .actions {
        display: flex;
        gap: 16px;
        margin-bottom: 32px;

        .el-button {
            padding: 12px 32px;
        }
    }

    .quick-links {
        display: flex;
        align-items: center;
        gap: 8px;

        .el-divider {
            margin: 0;
        }
    }
}



@media (max-width: 768px) {


    .error-body {
        padding: 160px;
    }

    .error-container {
        flex-direction: column;
        gap: 30px;
    }

    .error-number .digit {
        font-size: 80px;

        &.zero {
            width: 70px;
            height: 70px;

            .el-icon {
                font-size: 40px !important;
            }
        }
    }

    .error-message {
        text-align: center;

        h2 {
            font-size: 28px;
        }

        .actions {
            flex-direction: column;
            align-items: center;

            .el-button {
                width: 100%;
                max-width: 300px;
            }
        }

        .quick-links {
            justify-content: center;
            flex-wrap: wrap;
        }
    }
}
</style>