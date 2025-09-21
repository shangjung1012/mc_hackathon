<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
    <!-- 登入頁面 -->
    <LoginView v-if="!isLoggedIn" @login-success="handleLoginSuccess" />
    
    <!-- 主應用程式 -->
    <div v-else class="w-full min-h-screen">
      <!-- 使用者資訊欄 -->
      <div class="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <span class="text-white font-medium text-sm">
                {{ currentUser?.username?.charAt(0).toUpperCase() || 'U' }}
              </span>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                {{ currentUser?.username || '使用者' }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                視覺助理
              </p>
            </div>
          </div>
          <button
            @click="handleLogout"
            class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
          >
            登出
          </button>
        </div>
      </div>
      
      <!-- 相機模式 -->
      <div v-if="cameraMode" class="w-full min-h-screen flex flex-col">
      <!-- 相機預覽區域 -->
      <div class="flex flex-col items-center justify-center bg-black py-8">
        <div class="relative w-full max-w-2xl mx-auto">
          <video 
            ref="videoElement"
            class="w-full h-auto rounded-lg shadow-lg max-h-96"
            autoplay
            muted
            playsinline
          ></video>
          <div v-if="isListening" class="absolute top-4 right-4 flex items-center space-x-2 bg-black bg-opacity-50 text-white px-3 py-2 rounded-full">
            <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span class="text-sm">語音識別中...</span>
          </div>
          <div v-if="lastCommand" class="absolute bottom-4 left-4 bg-black bg-opacity-50 text-white px-3 py-2 rounded-lg">
            <span class="text-sm">指令: {{ lastCommand }}</span>
          </div>
        </div>
      </div>
      
      <!-- 照片預覽區域 -->
      <div v-if="latestPhoto" class="bg-gray-100 dark:bg-gray-800 p-6 flex-1">
        <div class="max-w-4xl mx-auto">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 text-center">
            最新照片
          </h3>
          <div class="flex justify-center">
            <img 
              :src="latestPhoto.dataUrl" 
              :alt="`照片拍攝於 ${latestPhoto.timestamp.toLocaleString()}`"
              class="max-w-full h-auto rounded-lg shadow-lg"
            />
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 text-center mt-3">
            拍攝時間: {{ latestPhoto.timestamp.toLocaleString() }}
          </p>
        </div>
      </div>
      
      <!-- 控制按鈕 -->
      <div class="bg-white dark:bg-gray-900 p-4 flex justify-center">
        <button 
          @click="exitCameraMode"
          class="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          退出拍照模式
        </button>
      </div>
    </div>

      <!-- 錄音模式 -->
      <div v-else class="text-center max-w-2xl mx-auto px-4">
      <!-- 錄音按鈕：支援 tap/hold/swipe -->
      <ActionButton
        class="w-48 h-48 rounded-full transition-all duration-300 transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-opacity-50 flex items-center justify-center"
        :holdDuration="600"
        :swipeThreshold="40"
        @tap="onActionTap"
        @hold="onActionHold"
        @swipe="onActionSwipe"
        :aria-label="isRecording ? '停止錄音' : '開始錄音'"
      >
        <div :class="[
          'flex items-center justify-center h-full w-full rounded-full',
          isRecording ? 'bg-red-500 hover:bg-red-600 focus:ring-red-300 shadow-lg shadow-red-200' : 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-300 shadow-lg shadow-blue-200'
        ]">
          <div v-if="!isRecording" class="w-0 h-0 border-l-[24px] border-l-white border-t-[18px] border-t-transparent border-b-[18px] border-b-transparent ml-2"></div>
          <div v-else class="w-8 h-8 bg-white rounded-sm"></div>
        </div>
      </ActionButton>
      
      <!-- 狀態文字 -->
      <p v-if="isRecording" class="mt-6 text-lg font-medium text-gray-700 dark:text-gray-300">
        錄音中... 點擊停止
      </p>
      
      <!-- 錄音時間顯示 -->
      <p v-if="isRecording" class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        錄音時間: {{ formatTime(recordingTime) }}
      </p>

      <!-- 語音識別狀態 -->
      <div v-if="speechRecognitionSupported" class="mt-4">
        <div v-if="isListening" class="flex items-center justify-center space-x-2 text-green-600 dark:text-green-400">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-sm">語音識別中...</span>
        </div>
      </div>

      <!-- 語音轉文字結果 -->
      <div v-if="transcriptText" class="mt-6 text-center">
        <p class="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{{ transcriptText }}</p>
        <div v-if="isListening && interimText" class="mt-2 text-sm text-gray-500 dark:text-gray-400 italic">
          即時識別: {{ interimText }}
        </div>
      </div>
      
      <!-- 錯誤訊息 -->
      <p v-if="error" class="mt-4 text-red-500 text-sm">
        {{ error }}
      </p>

      <!-- 語音識別不支援提示 -->
      <div v-if="!speechRecognitionSupported" class="mt-4 p-3 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
        <p class="text-sm text-yellow-800 dark:text-yellow-200">
          此瀏覽器不支援語音識別功能，僅能錄音
        </p>
      </div>
      
      <!-- 處理狀態面板 -->
      <div class="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-left text-sm text-gray-700 dark:text-gray-300">
        <div class="font-medium mb-2">處理狀態</div>
  <div>流程階段: <strong>{{ processState }}</strong></div>
  <div>最後一次 swipe: <strong>{{ lastSwipeDirection || 'none' }}</strong></div>
  <div>是否有快取照片: <strong>{{ hasCachedPhoto() ? '是' : '否' }}</strong></div>
        <div>照片是否已標記為上傳: <strong>{{ lastPhotoUploaded ? '是' : '否' }}</strong></div>
        <div>請求是否已發送: <strong>{{ requestSent ? '是' : '否' }}</strong></div>
        <div>是否收到回覆: <strong>{{ responseReceived ? '是' : '否' }}</strong></div>
        <div v-if="processState === 'ready-to-speak'" class="text-blue-500">使用 Web Speech API 備用方案</div>
        <div v-if="responseError" class="text-red-500">錯誤: {{ responseError }}</div>
        <div class="mt-2 text-xs text-gray-500">最近狀態訊息: {{ lastCommand }}</div>
      </div>
      
      <!-- 音訊播放按鈕 -->
      <div v-if="processState === 'ready-to-play' && audioElement" class="mt-4 flex justify-center">
        <button 
          @click="playAudio"
          class="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
          </svg>
          <span>播放回應音訊</span>
        </button>
      </div>
      
    </div>
    </div>  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick } from 'vue'
import ActionButton from './components/ActionButton.vue'
import LoginView from './views/LoginView.vue'
import { useSpeechToText, type SpeechRecognitionResult } from './services/speechToText'
import { useCamera, type PhotoCaptureResult } from './services/cameraService'
import { useVoiceCommand } from './services/voiceCommandService'
import { useAuth, type User } from './services/authService'
import { useAPI, type GeminiAnalyzeRequest } from './services/useAPI'
import { useTextToSpeech } from './services/textToSpeech'

// 登入狀態
const auth = useAuth()
const isLoggedIn = ref(false)
const currentUser = ref<User | null>(null)

// API 服務
const api = useAPI()

// TTS 服務
const tts = useTextToSpeech()

const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingTime = ref(0)
const error = ref('')
const recordingInterval = ref<number | null>(null)
const sessionTranscript = ref('')
const lastSwipeDirection = ref<string | null>(null) // 'up' | 'down' | null
const lastPhotoCache = ref<PhotoCaptureResult | null>(null)
const lastPhotoUploaded = ref(false)
const processState = ref<string>('idle') // 'idle'|'deciding'|'preparing'|'uploading'|'waiting'|'playing'|'done'|'error'
const requestSent = ref(false)
const responseReceived = ref(false)
const responseError = ref<string | null>(null)
const audioElement = ref<HTMLAudioElement | null>(null)
const audioUrl = ref<string | null>(null)

const hasCachedPhoto = () => !!lastPhotoCache.value

// 語音轉文字相關狀態
const speechToText = useSpeechToText()
const speechRecognitionSupported = ref(false)
const isListening = ref(false)
const transcriptText = ref('')
const interimText = ref('')

// 相機相關狀態
const cameraMode = ref(false)
const videoElement = ref<HTMLVideoElement | null>(null)
const camera = useCamera()
const lastCommand = ref('')
const latestPhoto = ref<PhotoCaptureResult | null>(null)

// 語音指令相關狀態
const voiceCommand = useVoiceCommand()

// 格式化時間顯示
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 處理登入成功
const handleLoginSuccess = (user: User) => {
  currentUser.value = user
  isLoggedIn.value = true
}

// 處理登出
const handleLogout = () => {
  auth.logout()
  currentUser.value = null
  isLoggedIn.value = false
  
  // 清理所有狀態
  transcriptText.value = ''
  interimText.value = ''
  sessionTranscript.value = ''
  lastCommand.value = ''
  latestPhoto.value = null
  lastPhotoCache.value = null
  lastPhotoUploaded.value = false
  processState.value = 'idle'
  requestSent.value = false
  responseReceived.value = false
  responseError.value = null
  lastSwipeDirection.value = null
  
  // 停止所有正在進行的操作
  if (isRecording.value) {
    stopRecording()
  }
  if (cameraMode.value) {
    exitCameraMode()
  }
  if (isListening.value) {
    speechToText.stopListening()
  }
}

// 初始化登入狀態
const initializeAuth = async () => {
  if (auth.isLoggedIn()) {
    // 先嘗試從本地緩存獲取使用者資料
    const cachedUser = auth.getCachedUser()
    if (cachedUser) {
      currentUser.value = cachedUser
      isLoggedIn.value = true
    }
    
    // 然後嘗試從 API 獲取最新資料
    try {
      const user = await auth.getCurrentUser()
      if (user) {
        currentUser.value = user
        isLoggedIn.value = true
      } else if (!cachedUser) {
        // 如果沒有緩存且無法從 API 獲取，清除登入狀態
        auth.logout()
        isLoggedIn.value = false
      }
    } catch (error) {
      console.error('初始化登入狀態失敗:', error)
      if (!cachedUser) {
        auth.logout()
        isLoggedIn.value = false
      }
    }
  }
}

// 初始化語音轉文字
const initializeSpeechToText = () => {
  speechRecognitionSupported.value = speechToText.isSupported()
  
  if (speechRecognitionSupported.value) {
    speechToText.setCallbacks({
      onResult: (result: SpeechRecognitionResult) => {
      if (result.isFinal) {
        // 不累加，每次錄音都重新設定顯示文字
        transcriptText.value = result.transcript
        interimText.value = ''
          
        // 累積本次錄音 session 的 transcript（用於後續處理）
        sessionTranscript.value += result.transcript + ' '

        // 處理語音指令
        handleVoiceCommand(result.transcript)
        } else {
          interimText.value = result.transcript
        }
      },
      onError: (errorMsg: string) => {
        error.value = errorMsg
      },
      onStart: () => {
        isListening.value = true
      },
      onEnd: () => {
        isListening.value = false
      },
      onNoMatch: () => {
        // 可以選擇是否顯示無匹配訊息
      }
    })
  }
}

// 開始錄音
const startRecording = async () => {
  try {
    error.value = ''
    
    // 重置顯示文字，每次錄音都重新開始
    transcriptText.value = ''
    interimText.value = ''
    sessionTranscript.value = ''
    
    // Try Permissions API first to give clearer guidance on mobile
    try {
      const perms = (navigator as any).permissions
      if (perms && perms.query) {
        try {
          const status = await perms.query({ name: 'microphone' } as any)
          if (status.state === 'denied') {
            error.value = '麥克風權限已被拒絕，請到瀏覽器設定允許本網站使用麥克風'
            console.warn('Microphone permission denied')
            return
          }
          // if 'prompt' or 'granted', continue to request getUserMedia
        } catch (e) {
          // Permissions API may not support 'microphone' on some browsers; ignore
          console.debug('Permissions API microphone query not available or failed', e)
        }
      }
    } catch (e) {
      console.debug('Permissions API not available', e)
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    mediaRecorder.value = new MediaRecorder(stream)
    
    mediaRecorder.value.onstop = () => {
      // 停止所有音軌
      stream.getTracks().forEach(track => track.stop())
    }
    
    mediaRecorder.value.start()
    isRecording.value = true
    recordingTime.value = 0
    
    // 開始語音識別
    if (speechRecognitionSupported.value) {
      // 確保語音識別實例正確初始化
      try {
        speechToText.startListening()
      } catch (error) {
        console.warn('語音識別啟動失敗，嘗試重新初始化:', error)
        // 如果啟動失敗，重新初始化並重試
        speechToText.reinitialize()
        setTimeout(() => {
          speechToText.startListening()
        }, 100)
      }
    }
    
    // 開始計時
    recordingInterval.value = window.setInterval(() => {
      recordingTime.value++
    }, 1000)
    
  } catch (err) {
    // Provide more actionable messages for mobile Chrome
    const msg = (err && (err as any).name) ? (err as any).name : String(err)
    if (msg === 'NotAllowedError' || msg === 'SecurityError') {
      error.value = '麥克風權限被拒絕：請在瀏覽器或系統設定中允許麥克風使用（需 HTTPS）'
    } else if (msg === 'NotFoundError' || msg === 'OverconstrainedError') {
      error.value = '未找到麥克風裝置，請確認裝置有可用的麥克風'
    } else if (msg === 'NotReadableError') {
      error.value = '無法讀取麥克風，請確認其他應用程式未占用麥克風'
    } else {
      error.value = '無法訪問麥克風，請檢查權限設定與瀏覽器設定'
    }
    console.error('錄音錯誤:', err)
  }
}

// 停止錄音
const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false
    
    // 停止語音識別
    if (speechRecognitionSupported.value) {
      speechToText.stopListening()
    }
    
    if (recordingInterval.value) {
      clearInterval(recordingInterval.value)
      recordingInterval.value = null
    }
    // 錄音停止後處理：將 sessionTranscript 與照片上傳
    void processAfterRecording(sessionTranscript.value)
  }
}

// 切換錄音狀態
const toggleRecording = () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    // 開始新的 session transcript
    sessionTranscript.value = ''
    startRecording()
  }
}

// ActionButton 事件處理
const onActionTap = () => {
  toggleRecording()
}

const onActionHold = () => {
  // 長按在桌面上模擬向上滑，啟動自動拍照（方便測試）
  lastSwipeDirection.value = 'up'
  void autoCaptureForSwipe('up')
}

const onActionSwipe = (direction: string) => {
  lastCommand.value = `swipe: ${direction}`
  // record swipe direction so subsequent recording uses correct scenario
  lastSwipeDirection.value = direction
  // 每次上/下/任意 swipe 都自動開啟相機拍照並回到主畫面
  void autoCaptureForSwipe(direction)
  // 保留左右滑示例回饋文字
  switch (direction) {
    case 'left':
      lastCommand.value = '向左滑 — previous (未實作)'
      break
    case 'right':
      lastCommand.value = '向右滑 — next (未實作)'
      break
  }

  setTimeout(() => (lastCommand.value = ''), 2000)
}

// 處理語音指令
const handleVoiceCommand = (transcript: string) => {
  const match = voiceCommand.matchCommand(transcript)
  if (match) {
    lastCommand.value = match.matchedText
    console.log('語音指令匹配:', match)
    
    switch (match.command.action) {
      case 'camera_mode':
        enterCameraMode()
        break
      case 'take_photo':
        if (cameraMode.value) {
          takePhoto()
        }
        break
      case 'close_camera':
        if (cameraMode.value) {
          exitCameraMode()
        }
        break
    }
    
    // 清除指令顯示
    setTimeout(() => {
      lastCommand.value = ''
    }, 3000)
  }
}

// 進入相機模式
const enterCameraMode = async () => {
  try {
    error.value = ''
    cameraMode.value = true
    
    await nextTick()
    
    if (videoElement.value) {
      await camera.initialize(videoElement.value)
    }
    
    // 開始語音識別
    if (speechRecognitionSupported.value) {
      speechToText.startListening()
    }
  } catch (err) {
    error.value = '無法啟動相機模式'
    console.error('相機模式啟動失敗:', err)
    cameraMode.value = false
  }
}

// 退出相機模式
const exitCameraMode = () => {
  cameraMode.value = false
  camera.stop()
  
  // 停止語音識別
  if (speechRecognitionSupported.value) {
    speechToText.stopListening()
  }
  
  // 清除照片預覽
  latestPhoto.value = null
}

// 拍照
const takePhoto = async () => {
  try {
    const photo = await camera.capturePhoto()
    if (photo) {
      console.log('拍照成功:', photo)

      // 保存最新照片並快取（尚未上傳）
      latestPhoto.value = photo
      lastPhotoCache.value = photo
      lastPhotoUploaded.value = false

      // 顯示拍照成功提示
      lastCommand.value = '拍照成功！'
      setTimeout(() => {
        lastCommand.value = ''
      }, 2000)
    }
  } catch (err) {
    console.error('拍照失敗:', err)
    error.value = '拍照失敗'
  }
}

// play a short beep sound (use WebAudio or simple Audio) for feedback
function playBeep() {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.type = 'sine'
    o.frequency.value = 880
    g.gain.value = 0.05
    o.connect(g)
    g.connect(ctx.destination)
    o.start()
    setTimeout(() => {
      o.stop()
      try { ctx.close() } catch (e) {}
    }, 150)
  } catch (e) {
    // fallback: use simple Audio with a small base64 beep (optional)
    console.warn('WebAudio not available for beep', e)
  }
}

// Play audio with user interaction
const playAudio = async () => {
  if (!audioElement.value) {
    console.error('No audio element available')
    return
  }

  try {
    processState.value = 'playing'
    await audioElement.value.play()
    processState.value = 'done'
    console.log('音訊播放完成')
  } catch (error) {
    console.error('音訊播放失敗:', error)
    processState.value = 'error'
    responseError.value = `播放失敗: ${String(error)}`
  }
}

// 使用 Web Speech API 朗讀文字（TTS 失敗時的備用方案）
const speakWithWebAPI = async (text: string): Promise<void> => {
  try {
    console.log('使用 Web Speech API 備用方案朗讀:', text)
    processState.value = 'playing'
    
    // 使用與 LoginView 相同的 TTS 服務
    await tts.speak(text)
    
    console.log('Web Speech API 朗讀完成')
    processState.value = 'done'
  } catch (error) {
    console.error('Web Speech API 朗讀失敗:', error)
    processState.value = 'error'
    responseError.value = `語音合成失敗: ${String(error)}`
    throw error
  }
}

// Auto open camera, capture photo and play beep for swipe events, then go back to main view
async function autoCaptureForSwipe(_direction: string) {
  try {
    error.value = ''
    cameraMode.value = true
    await nextTick()
    if (videoElement.value) {
      await camera.initialize(videoElement.value)
    }
    // wait for video to receive first frames (avoid capturing a black frame)
    const video = videoElement.value
    if (video) {
      const start = Date.now()
      const timeout = 2000 // ms
      // If browser supports requestVideoFrameCallback use it once
      if ((video as any).requestVideoFrameCallback) {
        await new Promise<void>((resolve) => {
          try {
            ;(video as any).requestVideoFrameCallback(() => resolve())
          } catch (e) {
            // fallback to animation frame loop
            const check = () => {
              if (video.videoWidth > 0 && video.videoHeight > 0 && video.readyState >= 2) return resolve()
              if (Date.now() - start > timeout) return resolve()
              requestAnimationFrame(check)
            }
            check()
          }
        })
      } else {
        await new Promise<void>((resolve) => {
          const check = () => {
            if (video.videoWidth > 0 && video.videoHeight > 0 && video.readyState >= 2) return resolve()
            if (Date.now() - start > timeout) return resolve()
            requestAnimationFrame(check)
          }
          check()
        })
      }
      // short stabilization delay
      await new Promise((r) => setTimeout(r, 100))
    }
    playBeep()
    const photo = await camera.capturePhoto()
    if (photo) {
      latestPhoto.value = photo
      lastPhotoCache.value = photo
      lastPhotoUploaded.value = false
      // 播放成功提示
      lastCommand.value = '拍照完成，返回主畫面'
      setTimeout(() => (lastCommand.value = ''), 1500)
    }
  } catch (err) {
    console.error('auto capture failed', err)
    error.value = '拍照失敗'
  } finally {
    // 確保回到主畫面
    camera.stop()
    cameraMode.value = false
    // 清除 video element
    await nextTick()
  }
}



// 初始化
void initializeAuth()
initializeSpeechToText()

// 清理資源
onUnmounted(() => {
  if (recordingInterval.value) {
    clearInterval(recordingInterval.value)
  }
  speechToText.destroy()
  camera.destroy()
  voiceCommand.destroy()
  tts.destroy()
  
  // Clean up audio resources
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }
})

// helper: downscale dataUrl to maxWidth (preserves aspect ratio). returns Blob
function downscaleDataUrl(dataUrl: string, maxWidth: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const ratio = img.width > maxWidth ? maxWidth / img.width : 1
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(img.width * ratio)
      canvas.height = Math.round(img.height * ratio)
      const ctx = canvas.getContext('2d')
      if (!ctx) return reject(new Error('無法取得 canvas context'))
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      canvas.toBlob((blob) => {
        if (blob) resolve(blob)
        else reject(new Error('toBlob 失敗'))
      }, 'image/jpeg', 0.8)
    }
    img.onerror = (e) => reject(e)
    img.src = dataUrl
  })
}

// Upload logic per the three scenarios
async function processAfterRecording(transcript: string) {
  if (!transcript || transcript.trim().length === 0) {
    console.log('無錄音文字，跳過上傳')
    return
  }

  // 重新獲取使用者資訊
  try {
    const user = await auth.getCurrentUser()
    if (user) {
      currentUser.value = user
      console.log('使用者資訊已更新:', user.username)
    }
  } catch (error) {
    console.warn('重新獲取使用者資訊失敗:', error)
  }

  // Decide scenario
  processState.value = 'deciding'
  responseError.value = null
  responseReceived.value = false
  requestSent.value = false

  let system_instruction = ''
  let photoToSend: Blob | null = null

  if (lastSwipeDirection.value === 'up') {
    // scenario 1: detailed precise answer + high res
    system_instruction = '請詳細且精準地回答以下內容，提供具體步驟與完整說明。'
    if (lastPhotoCache.value) {
      photoToSend = await downscaleDataUrl(lastPhotoCache.value.dataUrl, 1920)
    }
  } else if (lastSwipeDirection.value === 'down') {
    // scenario 2: short fast answer + lower res
    system_instruction = '請簡短快速地回答，重點即可。'
    if (lastPhotoCache.value) {
      photoToSend = await downscaleDataUrl(lastPhotoCache.value.dataUrl, 640)
    }
  } else {
    // no swipe before recording
    if (lastPhotoCache.value) {
      // attach previous photo (even if already uploaded before) but use scenario 2 behavior
      system_instruction = '請簡短快速地回答，重點即可。'
      photoToSend = await downscaleDataUrl(lastPhotoCache.value.dataUrl, 640)
    } else {
      // no photo ever taken -> only text
      system_instruction = '請簡短快速地回答，重點即可。'
      photoToSend = null
    }
  }

  // 使用 API 服務調用 Gemini 分析
  try {
    processState.value = 'preparing'
    
    const request: GeminiAnalyzeRequest = {
      text: transcript,
      system_instruction,
      image: photoToSend || undefined
    }

    lastCommand.value = '上傳並合成語音中...'
    processState.value = 'uploading'
    requestSent.value = true

    const response = await api.analyzeAndSpeak(request)

    if (!response.success) {
      throw new Error(response.error || 'API 調用失敗')
    }

    // We expect audio/wav stream
    processState.value = 'waiting'
    const res = response.data!
    const contentType = res.headers.get('content-type') || ''
    console.debug('Response Content-Type:', contentType)

    // If backend didn't return audio, read text for diagnostics
    if (!contentType.includes('audio')) {
      const text = await res.text().catch(() => null)
      console.error('Expected audio but got:', contentType, text)
      
      // 嘗試解析 JSON 回應，可能是 TTS 失敗的備用方案
      try {
        const jsonResponse = JSON.parse(text || '{}')
        if (jsonResponse.fallback_mode && jsonResponse.text) {
          console.log('TTS 失敗，使用 Web Speech API 備用方案')
          responseReceived.value = true
          processState.value = 'ready-to-speak'
          
          // 使用 Web Speech API 朗讀文字
          await speakWithWebAPI(jsonResponse.text)
          processState.value = 'done'
          lastCommand.value = '使用備用語音合成完成'
          setTimeout(() => (lastCommand.value = ''), 2000)
          return
        }
      } catch (parseError) {
        console.debug('無法解析為 JSON，繼續原有錯誤處理')
      }
      
      responseError.value = `後端回傳非音訊 (content-type=${contentType})：${text ? text.substring(0,200) : '無內容'}`
      processState.value = 'error'
      return
    }

    const blob = await res.blob()
    responseReceived.value = true
    console.debug('Received blob:', { size: blob.size, type: blob.type })
    processState.value = 'playing'

    // Store audio for user-triggered playback
    try {
      const url = URL.createObjectURL(blob)
      const audio = new Audio()
      audio.src = url
      audio.crossOrigin = 'anonymous'
      audio.preload = 'auto'

      // Store audio element for user interaction
      audioElement.value = audio
      audioUrl.value = url
      processState.value = 'ready-to-play'
      
      // Show play button instead of auto-playing
      console.log('音訊已準備就緒，等待用戶點擊播放')
    } catch (e) {
      console.error('音訊載入失敗', e)
      processState.value = 'error'
      responseError.value = `音訊載入失敗: ${String(e)}`
    }

  lastCommand.value = '完成'
    // mark photo as uploaded if we sent one
    if (photoToSend && lastPhotoCache.value) {
      lastPhotoUploaded.value = true
    }
    // 清理 swipe flag
    lastSwipeDirection.value = null
    setTimeout(() => (lastCommand.value = ''), 2000)
    return { ok: true }
  } catch (err: any) {
    console.error('上傳或合成語音失敗:', err)
    responseError.value = String(err)
    processState.value = 'error'
    lastCommand.value = '上傳或合成失敗'
    setTimeout(() => (lastCommand.value = ''), 3000)
  }
}
</script>
