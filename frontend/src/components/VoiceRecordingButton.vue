<template>
  <div class="flex flex-col items-center">
    <!-- 錄音按鈕 -->
    <button
      @click="toggleRecording"
      :disabled="disabled"
      :class="[
        'w-32 h-32 rounded-full transition-all duration-300 transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-opacity-50 flex items-center justify-center',
        isRecording 
          ? 'bg-red-500 hover:bg-red-600 focus:ring-red-300 shadow-lg shadow-red-200' 
          : 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-300 shadow-lg shadow-blue-200',
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      ]"
      :aria-label="isRecording ? '停止錄音' : '開始錄音'"
    >
      <!-- 三角形播放圖標 -->
      <div v-if="!isRecording" class="w-0 h-0 border-l-[24px] border-l-white border-t-[18px] border-t-transparent border-b-[18px] border-b-transparent ml-2"></div>
      <!-- 正方形停止圖標 -->
      <div v-else class="w-8 h-8 bg-white rounded-sm"></div>
    </button>

    <!-- 狀態文字 -->
    <p v-if="isRecording" class="mt-4 text-lg font-medium text-gray-700 dark:text-gray-300">
      錄音中... 點擊停止
    </p>
    <p v-else-if="!disabled" class="mt-4 text-sm text-gray-600 dark:text-gray-400">
      點擊開始錄音
    </p>

    <!-- 錄音時間顯示 -->
    <p v-if="isRecording" class="mt-2 text-sm text-gray-500 dark:text-gray-400">
      錄音時間: {{ formatTime(recordingTime) }}
    </p>

    <!-- 錯誤訊息 -->
    <p v-if="error" class="mt-4 text-red-500 text-sm text-center max-w-xs">
      {{ error }}
    </p>

    <!-- 移動設備權限指引 -->
    <div v-if="showMobileGuidance" class="mt-4 p-3 bg-blue-50 dark:bg-blue-900 rounded-lg text-sm text-blue-800 dark:text-blue-200">
      <p class="font-medium mb-2">📱 移動設備使用指引：</p>
      <ul class="text-left space-y-1">
        <li>• 確保使用 HTTPS 訪問（安全連接）</li>
        <li>• 點擊錄音按鈕後允許麥克風權限</li>
        <li>• 如被拒絕，請到瀏覽器設定中允許麥克風</li>
        <li>• 建議使用 Chrome 或 Safari 瀏覽器</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  disabled?: boolean
  onRecordingStart?: () => void
  onRecordingStop?: () => void
  onTranscript?: (transcript: string) => void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  recordingStart: []
  recordingStop: []
  transcript: [transcript: string]
  error: [error: string]
}>()

const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingTime = ref(0)
const error = ref('')
const recordingInterval = ref<number | null>(null)
const speechRecognition = ref<any>(null)
const isListening = ref(false)
const showMobileGuidance = ref(false)

// 格式化時間顯示
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 初始化語音識別
const initializeSpeechRecognition = () => {
  if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
    error.value = '此瀏覽器不支援語音識別功能'
    return false
  }

  try {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    speechRecognition.value = new SpeechRecognition()
    
    speechRecognition.value.lang = 'zh-TW'
    speechRecognition.value.continuous = true
    speechRecognition.value.interimResults = true
    speechRecognition.value.maxAlternatives = 1

    speechRecognition.value.onstart = () => {
      console.log('🎤 語音識別開始')
      isListening.value = true
    }

    speechRecognition.value.onresult = (event: any) => {
      const result = event.results[event.resultIndex]
      const transcript = result[0].transcript
      const isFinal = result.isFinal

      console.log('🎤 VoiceRecordingButton 語音識別結果:', { transcript, isFinal })

      if (isFinal) {
        console.log('✅ 發送最終轉文字結果:', transcript)
        emit('transcript', transcript)
      }
    }

    speechRecognition.value.onerror = (event: any) => {
      isListening.value = false
      let errorMessage = '語音識別發生錯誤'

      switch (event.error) {
        case 'no-speech':
          errorMessage = '沒有檢測到語音，請重試'
          break
        case 'audio-capture':
          errorMessage = '無法訪問麥克風'
          break
        case 'not-allowed':
          errorMessage = '麥克風權限被拒絕'
          break
        case 'network':
          errorMessage = '網路連線錯誤'
          break
        case 'service-not-allowed':
          errorMessage = '語音服務不可用'
          break
        case 'bad-grammar':
          errorMessage = '語法錯誤'
          break
        default:
          errorMessage = `語音識別錯誤: ${event.error}`
      }

      error.value = errorMessage
      emit('error', errorMessage)
    }

    speechRecognition.value.onend = () => {
      console.log('🎤 語音識別結束')
      isListening.value = false
    }

    speechRecognition.value.onnomatch = () => {
      // 可以選擇是否顯示無匹配訊息
    }

    return true
  } catch (err) {
    console.error('語音識別初始化失敗:', err)
    error.value = '語音識別初始化失敗'
    emit('error', error.value)
    return false
  }
}

// 開始錄音
const startRecording = async () => {
  try {
    error.value = ''
    
    // Try Permissions API first to give clearer guidance on mobile
    try {
      const perms = (navigator as any).permissions
      if (perms && perms.query) {
        try {
          const status = await perms.query({ name: 'microphone' } as any)
          if (status.state === 'denied') {
            error.value = '麥克風權限已被拒絕，請到瀏覽器設定允許本網站使用麥克風'
            emit('error', error.value)
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
    if (speechRecognition.value) {
      // 確保語音識別實例正確初始化
      try {
        speechRecognition.value.start()
      } catch (error) {
        console.warn('語音識別啟動失敗，嘗試重新初始化:', error)
        // 如果啟動失敗，重新初始化並重試
        initializeSpeechRecognition()
        setTimeout(() => {
          if (speechRecognition.value) {
            speechRecognition.value.start()
          }
        }, 100)
      }
    }
    
    // 開始計時
    recordingInterval.value = window.setInterval(() => {
      recordingTime.value++
    }, 1000)
    
    emit('recordingStart')
    props.onRecordingStart?.()
    
    // 成功開始錄音後隱藏移動設備指引
    if (showMobileGuidance.value) {
      showMobileGuidance.value = false
    }
    
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
    emit('error', error.value)
    console.error('錄音錯誤:', err)
  }
}

// 停止錄音
const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false
    
    // 停止語音識別
    if (speechRecognition.value) {
      speechRecognition.value.stop()
    }
    
    if (recordingInterval.value) {
      clearInterval(recordingInterval.value)
      recordingInterval.value = null
    }
    
    emit('recordingStop')
    props.onRecordingStop?.()
  }
}

// 切換錄音狀態
const toggleRecording = () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

// 清理資源
const cleanup = () => {
  if (recordingInterval.value) {
    clearInterval(recordingInterval.value)
  }
  if (speechRecognition.value) {
    speechRecognition.value.abort()
  }
}

// 檢測是否為移動設備
const isMobileDevice = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
         (navigator.maxTouchPoints && navigator.maxTouchPoints > 2)
}

onMounted(() => {
  // 檢查是否在 HTTPS 環境下（移動設備需要）
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
    error.value = '語音功能需要 HTTPS 環境，請使用 HTTPS 訪問'
    emit('error', error.value)
    return
  }
  
  // 如果是移動設備，顯示使用指引 - 已關閉
  // if (isMobileDevice()) {
  //   showMobileGuidance.value = true
  // }
  
  // 初始化語音識別
  const success = initializeSpeechRecognition()
  if (!success) {
    console.warn('語音識別初始化失敗')
  }
})

onUnmounted(() => {
  cleanup()
})
</script>
