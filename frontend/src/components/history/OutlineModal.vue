<template>
  <!-- 大纲查看模态框 -->
  <div v-if="visible && pages" class="outline-modal-overlay" @click="$emit('close')">
    <div class="outline-modal-content" @click.stop>
      <div class="outline-modal-header">
        <h3>完整大纲</h3>
        <button class="close-icon" @click="$emit('close')">×</button>
      </div>
      <div class="outline-modal-body">
        <div v-for="(page, idx) in pages" :key="idx" class="outline-page-card">
          <div class="outline-page-card-header">
            <span class="page-badge">P{{ idx + 1 }}</span>
            <span class="page-type-badge" :class="page.type">{{ getPageTypeName(page.type) }}</span>
            <span class="word-count">{{ page.content.length }} 字</span>
          </div>
          <div class="outline-page-card-content">{{ page.content }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 大纲查看模态框组件
 *
 * 以卡片形式展示大纲的每一页内容，包含：
 * - 页码标识
 * - 页面类型（封面/内容/总结）
 * - 字数统计
 * - 完整内容
 */

// 定义页面类型
interface Page {
  type: 'cover' | 'content' | 'summary'
  content: string
}

// 定义 Props
defineProps<{
  visible: boolean
  pages: Page[] | null
}>()

// 定义 Emits
defineEmits<{
  (e: 'close'): void
}>()

/**
 * 获取页面类型的中文名称
 */
function getPageTypeName(type: string): string {
  const names: Record<string, string> = {
    cover: '封面',
    content: '内容',
    summary: '总结'
  }
  return names[type] || '内容'
}
</script>

<style scoped>
/* 模态框遮罩层 */
.outline-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

/* 模态框内容容器 */
.outline-modal-content {
  background: white;
  width: 100%;
  max-width: 800px;
  max-height: 85vh;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

/* 模态框头部 */
.outline-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.outline-modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

/* 关闭按钮 */
.close-icon {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  line-height: 1;
  transition: color 0.2s;
}

.close-icon:hover {
  color: #333;
}

/* 模态框主体（可滚动） */
.outline-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  background: #f9fafb;
}

/* 大纲页面卡片 */
.outline-page-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.outline-page-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #d1d5db;
}

.outline-page-card:last-child {
  margin-bottom: 0;
}

/* 卡片头部 */
.outline-page-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid #e5e7eb;
}

/* 页码标识 */
.page-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 24px;
  padding: 0 8px;
  background: var(--primary, #ff2442);
  color: white;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
}

/* 页面类型标识 */
.page-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: #e9ecef;
  color: #6c757d;
}

.page-type-badge.cover {
  background: #e3f2fd;
  color: #1976d2;
}

.page-type-badge.content {
  background: #f3e5f5;
  color: #7b1fa2;
}

.page-type-badge.summary {
  background: #e8f5e9;
  color: #388e3c;
}

/* 字数统计 */
.word-count {
  margin-left: auto;
  font-size: 11px;
  color: #999;
}

/* 卡片内容 */
.outline-page-card-content {
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .outline-modal-overlay {
    padding: 20px;
  }

  .outline-modal-content {
    max-height: 90vh;
  }

  .outline-modal-header {
    padding: 16px 20px;
  }

  .outline-modal-body {
    padding: 16px 20px;
  }
}
</style>
