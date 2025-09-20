<template>
  <div
    class="action-button"
    :class="buttonClass"
    @touchstart.prevent="onStart($event)"
    @touchmove.prevent="onMove($event)"
    @touchend.prevent="onEnd($event)"
    @touchcancel.prevent="onCancel($event)"
    @mousedown="onStart($event)"
    @mousemove="onMove($event)"
    @mouseup="onEnd($event)"
    @mouseleave="onCancel($event)"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount, computed } from 'vue'

const props = defineProps({
  holdDuration: { type: Number, default: 600 },
  swipeThreshold: { type: Number, default: 40 }
})

const emit = defineEmits(['tap', 'hold', 'swipe'])

let startX = 0
let startY = 0
let startTime = 0
let moved = false
let holdTimer: number | null = null

const isHolding = ref(false)

const buttonClass = computed(() => ({
  holding: isHolding.value
}))

function getTouchPoint(e: TouchEvent | MouseEvent) {
  if ((e as TouchEvent).changedTouches && (e as TouchEvent).changedTouches.length) {
    const t = (e as TouchEvent).changedTouches[0]
    return { x: t.clientX, y: t.clientY }
  }
  const me = e as MouseEvent
  return { x: me.clientX, y: me.clientY }
}

function onStart(e: TouchEvent | MouseEvent) {
  const pt = getTouchPoint(e)
  startX = pt.x
  startY = pt.y
  startTime = Date.now()
  moved = false
  isHolding.value = false

  // 長按計時器
  holdTimer = window.setTimeout(() => {
    isHolding.value = true
    emit('hold')
    holdTimer = null
  }, props.holdDuration)
}

function onMove(e: TouchEvent | MouseEvent) {
  const pt = getTouchPoint(e)
  const dx = pt.x - startX
  const dy = pt.y - startY
  if (Math.hypot(dx, dy) > 10) moved = true
}

function onEnd(e: TouchEvent | MouseEvent) {
  const pt = getTouchPoint(e)
  const dx = pt.x - startX
  const dy = pt.y - startY
  const dt = Date.now() - startTime

  // 取消長按計時器
  if (holdTimer) {
    clearTimeout(holdTimer)
    holdTimer = null
  }

  if (isHolding.value) {
    // 已經觸發過 hold，不再觸發 tap 或 swipe
    isHolding.value = false
    return
  }

  // 判斷 swipe
  const absX = Math.abs(dx)
  const absY = Math.abs(dy)
  const threshold = props.swipeThreshold
  if (Math.max(absX, absY) >= threshold && dt < 1000) {
    const direction = absX > absY
      ? (dx > 0 ? 'right' : 'left')
      : (dy > 0 ? 'down' : 'up')
    emit('swipe', direction)
    return
  }

  // 否則視為 tap（短按、移動很小、時間短或沒有觸發 hold）
  if (!moved && dt < 500) {
    emit('tap')
  }
}

function onCancel() {
  if (holdTimer) {
    clearTimeout(holdTimer)
    holdTimer = null
  }
  isHolding.value = false
}

onBeforeUnmount(() => {
  if (holdTimer) clearTimeout(holdTimer)
})
</script>

<style scoped>
.action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  user-select: none;
  touch-action: none; /* 讓瀏覽器不要攔截滑動手勢 */
}
.action-button.holding {
  opacity: 0.85;
  transform: scale(0.98);
}
</style>
