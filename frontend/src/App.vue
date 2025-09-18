<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useApi } from './composables/useApi'
import { useTTS } from './composables/useTTS'
import { usePermissions } from './composables/usePermissions'
import { useCamera } from './composables/useCamera'

type HealthState = 'idle' | 'loading' | 'ok' | 'error'

const capturedImageUrl = ref<string | null>(null)
const { videoEl, cameraReady, cameraError, startCamera, stopCamera, captureFrame } = useCamera()
const cameraActivated = ref(false)
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
// Shopping mode state
const shoppingMode = ref(false)
let currentWish = ''
let wishDebounceTimer: ReturnType<typeof setTimeout> | null = null
// TTS / live region for accessibility
const liveMessage = ref<string>('')
// TTS composable
const { ttsReady, pickZhVoice, ensureTtsUnlocked, speakText } = useTTS()

// Recognition restart/backoff state
let restartAttempts = 0
const maxRestartAttempts = 6
const { micPermission, cameraPermission, refreshPermissionsFromDevices, checkMicPermission, checkCameraPermission, cleanupPermissionWatchers } = usePermissions()

// API helpers
const { checkBackendHealth: apiCheckHealth, analyze } = useApi()

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
    // On many mobile browsers, Permissions API for microphone is unreliable
    // Mark mic as granted when recognition actually starts
    micPermission.value = 'granted'
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

      // Keyword detection: shopping mode and related commands
      try {
        const text = final.trim()
        // 開啟逛街模式
        if (!shoppingMode.value && (text.includes('開啟逛街模式') || text.includes('開始逛街模式'))) {
          shoppingMode.value = true
          cameraActivated.value = true
          // start camera and immediately take photo and notify backend with action=open
          startCamera({ cameraPermissionRef: cameraPermission, refreshPermissionsFromDevices }).then(() => {
            setTimeout(() => {
              takePhotoAndSend('open', null)
            }, 500)
          })
        }

        // Detect user wants (start collecting after keyword 我想要)
        if (shoppingMode.value && text.includes('我想要')) {
          const idx = text.indexOf('我想要')
          const after = text.slice(idx + 3).trim()
          if (after) {
            currentWish += (currentWish ? ' ' : '') + after
          }
          if (wishDebounceTimer) clearTimeout(wishDebounceTimer)
          wishDebounceTimer = setTimeout(() => {
            if (currentWish.trim()) {
              takePhotoAndSend('shopping', currentWish.trim())
            }
            currentWish = ''
            wishDebounceTimer = null
          }, 1200)
        }

        // 結束逛街模式
        if (shoppingMode.value && (text.includes('結束逛街模式') || text.includes('離開逛街模式'))) {
          takePhotoAndSend('close', null)
          shoppingMode.value = false
          currentWish = ''
          if (wishDebounceTimer) { clearTimeout(wishDebounceTimer); wishDebounceTimer = null }
          stopCamera()
        }

        // 保留原先開啟拍照模式關鍵字
        if (!cameraActivated.value && text.includes('開啟拍照模式')) {
          cameraActivated.value = true
          startCamera({ cameraPermissionRef: cameraPermission, refreshPermissionsFromDevices })
        }
      } catch {}
      
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
    
    // Robust restart: only restart if requested; use backoff to avoid busy-loop failures
    if (shouldKeepRecognizing) {
      restartAttempts = Math.min(maxRestartAttempts, restartAttempts + 1)
      const backoffMs = Math.min(200 * Math.pow(2, restartAttempts - 1), 5000)
      setTimeout(() => {
        try {
          recognition.start()
          // success: reset attempts
          restartAttempts = 0
        } catch (e) {
          console.warn('restart recognition failed', e)
        }
      }, backoffMs)
    }
  }
}

function onTtsUnlockClick() {
  try {
    ensureTtsUnlocked()
    if (ttsReady.value) liveMessage.value = '語音已啟用'
  } catch {}
}

async function takePhoto() {
  try {
    const frame = await captureFrame()
    if (!frame) return
    if (capturedImageUrl.value) URL.revokeObjectURL(capturedImageUrl.value)
    capturedImageUrl.value = frame.url
    await checkBackendHealth()
  } catch (e) {
    console.error('takePhoto failed', e)
  }
}

function backToCapture() {
  if (capturedImageUrl.value) URL.revokeObjectURL(capturedImageUrl.value)
  capturedImageUrl.value = null
  health.value = 'idle'
}

// helper: take photo blob and send to backend /gemini/analyze with action
async function takePhotoAndSend(action: string, text: string | null) {
  try {
    const frame = await captureFrame()
    if (!frame) return

    // update captured preview
    if (capturedImageUrl.value) URL.revokeObjectURL(capturedImageUrl.value)
    capturedImageUrl.value = frame.url

    health.value = 'loading'
    try {
      const data = await analyze(action, text, frame.blob)
      health.value = 'ok'
      console.log('analyze result', data)
      // announce result for accessibility
      const spoken = typeof data?.result === 'string' ? data.result : JSON.stringify(data.result)
      liveMessage.value = spoken
      speakText(spoken)
    } catch (e) {
      console.error('analyze failed', e)
      health.value = 'error'
      const errMsg = '伺服器回應失敗'
      liveMessage.value = errMsg
      speakText(errMsg)
    }
  } catch (e) {
    console.error('takePhotoAndSend failed', e)
  }
}

onMounted(() => {
  // Prepare TTS voices
  if ('speechSynthesis' in window) {
    try {
      pickZhVoice()
      window.speechSynthesis.onvoiceschanged = () => pickZhVoice()
    } catch {}
  }
  // Auto-start continuous speech recognition loop
  if (recognitionSupported.value) {
    shouldKeepRecognizing = true
    try {
      recognition.start()
    } catch (e) {
      setTimeout(() => {
        try { recognition.start() } catch {}
      }, 200)
    }
  }

  // Check microphone permission state
  checkMicPermission()
  // Check camera permission state
  checkCameraPermission()
  // Best-effort: try to infer permissions by checking labeled devices (works after first grant)
  setTimeout(() => { refreshPermissionsFromDevices() }, 300)
})

onBeforeUnmount(() => {
  stopCamera()
  cleanupPermissionWatchers()
})

function toggleRecognition() {
  if (!recognitionSupported.value) return
  if (micPermission.value === 'denied') {
    alert('麥克風權限被拒絕，請至瀏覽器設定開啟麥克風權限')
    return
  }
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
  try {
    const status = await apiCheckHealth()
    health.value = status === 'ok' ? 'ok' : 'error'
  } catch (e) {
    health.value = 'error'
  }
}

// checkMicPermission, checkCameraPermission provided by composable
</script>

<template>
  <main class="min-h-full grid grid-rows-[1fr_auto]">
    <!-- Live region for screen readers: announce API/TTS results -->
    <div class="sr-only" aria-live="polite">{{ liveMessage }}</div>
    <section class="p-4 pb-2 flex items-center justify-center">
      <div class="w-full max-w-sm">
        <!-- Speech transcript area -->
        <div class="mb-4">
          <div class="w-full rounded-2xl bg-neutral-100 dark:bg-neutral-900 p-4 text-center">
            <p class="text-sm opacity-80">語音辨識</p>
            <p class="mt-2 text-base break-words" aria-live="polite">{{ transcript || '尚未辨識到語音' }}</p>
            <p class="mt-2 text-xs opacity-70">
              麥克風權限：
              <span :class="{
                'text-green-600': micPermission==='granted',
                'text-red-600': micPermission==='denied',
                'text-blue-600': micPermission==='prompt',
              }">
                {{ micPermission === 'unsupported' ? '未知/不支援' : micPermission === 'granted' ? '已允許' : micPermission === 'denied' ? '已拒絕' : '等待授權' }}
              </span>
            </p>
            <p class="mt-1 text-xs opacity-70">
              相機權限：
              <span :class="{
                'text-green-600': cameraPermission==='granted',
                'text-red-600': cameraPermission==='denied',
                'text-blue-600': cameraPermission==='prompt',
              }">
                {{ cameraPermission === 'unsupported' ? '未知/不支援' : cameraPermission === 'granted' ? '已允許' : cameraPermission === 'denied' ? '已拒絕' : '等待授權' }}
              </span>
            </p>
          </div>
        </div>
        <div v-if="cameraActivated" class="relative">
          <div class="aspect-[3/4] overflow-hidden rounded-2xl bg-neutral-200 dark:bg-neutral-800">
            <video ref="videoEl" playsinline muted class="w-full h-full object-cover"></video>
          </div>
          <p v-if="!cameraReady && !cameraError" class="absolute inset-0 grid place-items-center text-sm opacity-80">
            正在開啟相機…
          </p>
          <p v-if="cameraError" class="mt-2 text-sm text-red-600">{{ cameraError }}</p>
        </div>
        <div v-else class="aspect-[3/4] rounded-2xl bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-center p-4">
          <p class="text-sm opacity-80">語音偵測中… 說「開啟拍照模式」以啟用相機</p>
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

      <!-- One-time TTS unlock for mobile browsers -->
      <button
        v-if="!ttsReady"
        class="col-span-3 mt-2 h-12 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200/70 dark:border-neutral-700 text-base active:scale-[0.98]"
        aria-label="啟用語音輸出"
        @click="onTtsUnlockClick"
      >
        啟用語音輸出（若手機沒有說話請先點我）
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
        v-if="cameraActivated"
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
