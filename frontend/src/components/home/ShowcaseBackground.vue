<template>
  <!-- 图片网格轮播背景 -->
  <div class="showcase-background" :class="{ 'is-ready': isReady }">
    <div class="showcase-grid" :style="{ transform: `translateY(-${scrollOffset}px)` }">
      <div v-for="(image, index) in showcaseImages" :key="index" class="showcase-item">
        <img :src="`/assets/showcase/${image}`" :alt="`封面 ${index + 1}`" loading="eager" />
      </div>
    </div>
    <div class="showcase-overlay"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 图片展示背景组件
 *
 * 功能：
 * - 加载展示图片列表
 * - 无限循环滚动动画
 * - 毛玻璃遮罩效果
 * - 平滑淡入过渡
 */

// 展示图片列表
const showcaseImages = ref<string[]>([])

// 滚动偏移量
const scrollOffset = ref(0)

// 是否准备好显示
const isReady = ref(false)

// 滚动定时器
let scrollInterval: ReturnType<typeof setInterval> | null = null

/**
 * 预加载图片
 */
function preloadImages(images: string[]): Promise<void[]> {
  const promises = images.map(image => {
    return new Promise<void>((resolve) => {
      const img = new Image()
      img.onload = () => resolve()
      img.onerror = () => resolve() // 即使加载失败也继续
      img.src = `/assets/showcase/${image}`
    })
  })
  return Promise.all(promises)
}

/**
 * 加载展示图片列表
 */
async function loadShowcaseImages() {
  try {
    const response = await fetch('/assets/showcase_manifest.json')
    const data = await response.json()
    const originalImages = data.covers || []

    // 预加载前几张图片（可视区域内的）
    const preloadCount = Math.min(originalImages.length, 22) // 约2行
    await preloadImages(originalImages.slice(0, preloadCount))

    // 复制图片数组3次以实现无缝循环
    showcaseImages.value = [...originalImages, ...originalImages, ...originalImages]

    // 短暂延迟后显示，确保 DOM 渲染完成
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        isReady.value = true
      })
    })

    // 启动平滑滚动动画
    if (showcaseImages.value.length > 0) {
      startScrollAnimation(originalImages.length)
    }
  } catch (e) {
    console.error('加载展示图片失败:', e)
    isReady.value = true // 即使失败也显示
  }
}

/**
 * 启动滚动动画
 */
function startScrollAnimation(originalCount: number) {
  // 计算网格总高度（每行约180px：164px图片 + 16px间距）
  const rowHeight = 180
  const itemsPerRow = 11
  const totalRows = Math.ceil(originalCount / itemsPerRow)
  const sectionHeight = totalRows * rowHeight

  scrollInterval = setInterval(() => {
    scrollOffset.value += 1

    // 滚动到第二组末尾时重置到第一组开始位置
    if (scrollOffset.value >= sectionHeight) {
      scrollOffset.value = 0
    }
  }, 30) // 每30ms移动1px，实现流畅滚动
}

onMounted(() => {
  loadShowcaseImages()
})

onUnmounted(() => {
  if (scrollInterval) {
    clearInterval(scrollInterval)
  }
})
</script>

<style scoped>
/* 背景容器 */
.showcase-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  z-index: -1;
  overflow: hidden;
  opacity: 0;
  transition: opacity 0.6s ease-out;
}

.showcase-background.is-ready {
  opacity: 1;
}

/* 图片网格 */
.showcase-grid {
  display: grid;
  grid-template-columns: repeat(11, 1fr);
  gap: 16px;
  padding: 20px;
  width: 100%;
  will-change: transform;
}

/* 单个展示项 */
.showcase-item {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.showcase-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 毛玻璃遮罩层 */
.showcase-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.7) 0%,
    rgba(255, 255, 255, 0.65) 30%,
    rgba(255, 255, 255, 0.6) 100%
  );
  backdrop-filter: blur(2px);
}

/* 响应式布局 */
@media (max-width: 768px) {
  .showcase-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    padding: 12px;
  }
}
</style>
