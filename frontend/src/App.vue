<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

type HealthState = 'idle' | 'loading' | 'ok' | 'error'

const capturedImageUrl = ref<string | null>(null)
const videoEl = ref<HTMLVideoElement | null>(null)
let mediaStream: MediaStream | null = null
const cameraReady = ref(false)
const cameraError = ref<string | null>(null)
const health = ref<HealthState>('idle')
// Speech recognition state
const recognizing = ref(false)
const transcript = ref<string>('')
const subtitles = ref<string[]>([])
const recognitionSupported = ref<boolean>(typeof window !== 'undefined' && (!!(window as any).SpeechRecognition || !!(window as any).webkitSpeechRecognition))
let recognition: any = null
let shouldKeepRecognizing = false
let debounceTimer: ReturnType<typeof setTimeout> | null = null
let pendingFinalText = ''

if (recognitionSupported.value) {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  recognition = new SpeechRecognition()
  // try to enable continuous; some implementations ignore it
  recognition.continuous = true
  recognition.lang = 'zh-TW'
  recognition.interimResults = true
  recognition.maxAlternatives = 1

  recognition.onstart = () => {
    recognizing.value = true
  }

  recognition.onresult = (event: any) => {
    let interim = ''
    let final = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const res = event.results[i]
      if (res.isFinal) final += res[0].transcript
      else interim += res[0].transcript
    }
    
    // Update transcript with both final and interim for full display
    if (final.trim()) {
      transcript.value = (transcript.value + ' ' + final).trim()
      pendingFinalText = final.trim()
      
      // Debounce subtitle updates - only add to subtitles after text is stable
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        if (pendingFinalText.trim()) {
          subtitles.value.push(pendingFinalText.trim())
          pendingFinalText = ''
        }
      }, 700)
    }
    
    // Show interim results only in transcript, not in subtitles
    if (interim.trim()) {
      // Don't modify transcript with interim to avoid duplication
      // Just let user see interim in real-time without adding to history
    }
  }

  recognition.onerror = (e: any) => {
    console.error('Speech recognition error', e)
  }

  recognition.onend = () => {
    recognizing.value = false
    
    // Flush any pending final text immediately when recognition ends
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    if (pendingFinalText.trim()) {
      subtitles.value.push(pendingFinalText.trim())
      pendingFinalText = ''
    }
    
    // If user requested continuous recognition, restart after a small delay
    if (shouldKeepRecognizing) {
      setTimeout(() => {
        try {
          recognition.start()
        } catch (e) {
          // some browsers may throw if start called immediately; ignore and try again later
          console.warn('restart recognition failed', e)
        }
      }, 200)
    }
  }
}

async function startCamera() {
  try {
    cameraError.value = null
    // Request back camera when available
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 1706 } },
      audio: false,
    })
    if (videoEl.value) {
      videoEl.value.srcObject = mediaStream
      await videoEl.value.play()
      cameraReady.value = true
    }
  } catch (e: any) {
    cameraError.value = e?.message || '無法開啟相機（需要 HTTPS 或權限）'
    cameraReady.value = false
  }
}

function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop())
    mediaStream = null
  }
  cameraReady.value = false
}

async function takePhoto() {
  if (!videoEl.value) return
  try {
    const video = videoEl.value
    const canvas = document.createElement('canvas')
    const vw = video.videoWidth || 1080
    const vh = video.videoHeight || 1440
    canvas.width = vw
    canvas.height = vh
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, vw, vh)
    const blob: Blob | null = await new Promise(resolve => canvas.toBlob(b => resolve(b), 'image/jpeg', 0.9))
    if (!blob) return
    if (capturedImageUrl.value) URL.revokeObjectURL(capturedImageUrl.value)
    const url = URL.createObjectURL(blob)
    if (navigator.vibrate) navigator.vibrate(10)
    capturedImageUrl.value = url
    checkBackendHealth()
  } catch (e) {
    console.error('takePhoto failed', e)
  }
}

function backToCapture() {
  if (capturedImageUrl.value) URL.revokeObjectURL(capturedImageUrl.value)
  capturedImageUrl.value = null
  health.value = 'idle'
}

onMounted(() => {
  if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
    startCamera()
  } else {
    cameraError.value = '此裝置或瀏覽器不支援相機存取'
  }
})

onBeforeUnmount(() => {
  stopCamera()
})

function toggleRecognition() {
  if (!recognitionSupported.value) return
  if (recognizing.value) {
    // user requested stop
    shouldKeepRecognizing = false
    
    // Clean up debounce timer and flush pending text
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    if (pendingFinalText.trim()) {
      subtitles.value.push(pendingFinalText.trim())
      pendingFinalText = ''
    }
    
    recognition.stop()
  } else {
    // user requested start; enable keep-alive behavior
    shouldKeepRecognizing = true
    try {
      recognition.start()
    } catch (e) {
      console.warn('recognition start error', e)
      // sometimes recognition needs a tiny delay before starting
      setTimeout(() => {
        try { recognition.start() } catch (e) { console.warn('second start failed', e) }
      }, 200)
    }
  }
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
        <!-- Speech transcript area -->
        <div class="mb-4">
          <div class="w-full rounded-2xl bg-neutral-100 dark:bg-neutral-900 p-4 text-center">
            <p class="text-sm opacity-80">語音辨識</p>
            <p class="mt-2 text-base break-words" aria-live="polite">{{ transcript || '尚未辨識到語音' }}</p>
          </div>
        </div>
        <div class="relative">
          <div class="aspect-[3/4] overflow-hidden rounded-2xl bg-neutral-200 dark:bg-neutral-800">
            <video ref="videoEl" playsinline muted class="w-full h-full object-cover"></video>
          </div>
          <p v-if="!cameraReady && !cameraError" class="absolute inset-0 grid place-items-center text-sm opacity-80">
            正在開啟相機…
          </p>
          <p v-if="cameraError" class="mt-2 text-sm text-red-600">{{ cameraError }}</p>
        </div>

        <template v-if="capturedImageUrl">
          <div class="mt-3">
            <img :src="capturedImageUrl" alt="captured" class="w-full rounded-2xl object-cover aspect-[3/4]" />
          </div>
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
            <div class="flex items-center gap-2">
              <button class="h-10 px-4 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200/70 dark:border-neutral-700 active:scale-[0.98]" @click="checkBackendHealth">
                重新檢查
              </button>
              <button class="h-10 px-3 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200/70 dark:border-neutral-700 active:scale-[0.98]" @click="backToCapture">
                清除截圖
              </button>
            </div>
          </div>
        </template>
      </div>
    </section>

    <nav class="sticky bottom-0 p-4 grid grid-cols-3 gap-3">
      <!-- Large microphone button for accessibility -->
      <button
        class="col-span-3 h-20 rounded-full bg-red-600 text-white text-2xl shadow-md active:scale-[0.98] flex items-center justify-center"
        :aria-pressed="recognizing"
        :aria-label="recognitionSupported ? (recognizing ? '停止語音辨識' : '啟動語音辨識') : '語音辨識不支援'"
        :disabled="!recognitionSupported"
        @click="toggleRecognition"
      >
        <span v-if="!recognitionSupported">🎤 不支援</span>
        <span v-else>
          <span v-if="recognizing">停&nbsp;止</span>
          <span v-else>開始偵測</span>
        </span>
      </button>

      <!-- Live region for screen readers (visually hidden) -->
      <div class="sr-only" aria-live="polite">{{ recognizing ? '麥克風已開啟' : '麥克風已關閉' }}</div>

      <!-- Subtitle sliding window (overlay at bottom) -->
      <div aria-hidden="false" class="col-span-3 pointer-events-none">
        <div class="subtitle-window fixed left-1/2 transform -translate-x-1/2 bottom-36 w-full max-w-2xl px-4">
          <div class="space-y-2">
            <div v-for="(s, idx) in subtitles.slice(-5)" :key="idx" class="subtitle-item">
              {{ s }}
            </div>
          </div>
        </div>
      </div>

      <button
        class="col-span-3 h-14 rounded-full bg-blue-600 text-white text-lg shadow-md active:scale-[0.98] disabled:opacity-60"
        aria-label="拍照"
        :disabled="!cameraReady || !!cameraError"
        @click="takePhoto"
      >
        拍照
      </button>
    </nav>
  </main>
  
</template>

<style scoped>
.subtitle-window {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  z-index: 60;
}
.subtitle-window .space-y-2 {
  display: flex;
  flex-direction: column-reverse;
  gap: 0.5rem;
  align-items: center;
}
.subtitle-item {
  background: rgba(0,0,0,0.75);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 1.125rem;
  line-height: 1.2;
  max-width: 90%;
  text-align: center;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  pointer-events: none;
  animation: slideInUp 360ms cubic-bezier(.22,.9,.31,1) both;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
