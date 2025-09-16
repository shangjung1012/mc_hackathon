<script setup lang="ts">
import { ref } from 'vue'

type HealthState = 'idle' | 'loading' | 'ok' | 'error'

const fileInput = ref<HTMLInputElement | null>(null)
const capturedImageUrl = ref<string | null>(null)
const health = ref<HealthState>('idle')

function openCameraPicker() {
  fileInput.value?.click()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (navigator.vibrate) navigator.vibrate(10)
  capturedImageUrl.value = URL.createObjectURL(file)
  checkBackendHealth()
}

function backToCapture() {
  if (capturedImageUrl.value) URL.revokeObjectURL(capturedImageUrl.value)
  capturedImageUrl.value = null
  health.value = 'idle'
}

async function checkBackendHealth() {
  health.value = 'loading'
  const host = window.location.hostname || '127.0.0.1'
  const url = `http://${host}:8000/health`
  try {
    const res = await fetch(url, { method: 'GET' })
    if (!res.ok) throw new Error(String(res.status))
    const data = await res.json()
    health.value = data?.status === 'ok' ? 'ok' : 'error'
  } catch (e) {
    health.value = 'error'
  }
}
</script>

<template>
  <main class="min-h-full grid grid-rows-[1fr_auto]">
    <section class="p-4 pb-2 flex items-center justify-center">
      <div class="w-full max-w-sm">
        <template v-if="!capturedImageUrl">
          <div class="aspect-[3/4] rounded-2xl bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-center p-4">
            <p class="text-sm opacity-80">點擊下方按鈕開啟相機（不需 HTTPS）</p>
          </div>
        </template>
        <template v-else>
          <img :src="capturedImageUrl" alt="captured" class="w-full rounded-2xl object-cover aspect-[3/4]" />
          <div class="mt-3 rounded-xl border border-neutral-200/70 dark:border-neutral-700 p-3 flex items-center justify-between bg-neutral-50 dark:bg-neutral-900">
            <div>
              <p class="text-sm opacity-70">後端健康檢查</p>
              <p class="text-base font-medium" :class="{
                'text-blue-600': health==='loading',
                'text-green-600': health==='ok',
                'text-red-600': health==='error',
              }">
                {{ health === 'idle' ? '尚未檢查' : health === 'loading' ? '檢查中…' : health === 'ok' ? '連線正常' : '連線失敗' }}
              </p>
            </div>
            <button class="h-10 px-4 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200/70 dark:border-neutral-700 active:scale-[0.98]" @click="checkBackendHealth">
              重新檢查
            </button>
          </div>
        </template>
      </div>
    </section>

    <nav class="sticky bottom-0 p-4 grid grid-cols-3 gap-3">
      <button
        v-if="capturedImageUrl"
        class="col-span-1 h-14 rounded-xl bg-neutral-100 dark:bg-neutral-800 border border-neutral-200/70 dark:border-neutral-700 active:scale-[0.98]"
        aria-label="返回"
        @click="backToCapture"
      >
        ⬅️
      </button>

      <button
        v-else
        class="col-span-3 h-14 rounded-full bg-blue-600 text-white text-lg shadow-md active:scale-[0.98]"
        aria-label="拍照"
        @click="openCameraPicker"
      >
        拍照
      </button>

      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        capture="environment"
        class="hidden"
        @change="onFileChange"
      />
    </nav>
  </main>
  
</template>

<style scoped>
</style>
