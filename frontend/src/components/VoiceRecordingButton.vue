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

  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  speechRecognition.value = new SpeechRecognition()
  
  speechRecognition.value.lang = 'zh-TW'
  speechRecognition.value.continuous = true
  speechRecognition.value.interimResults = true
  speechRecognition.value.maxAlternatives = 1

  speechRecognition.value.onstart = () => {
    isListening.value = true
  }

  speechRecognition.value.onresult = (event: any) => {
    const result = event.results[event.resultIndex]
    const transcript = result[0].transcript
    const isFinal = result.isFinal

    if (isFinal) {
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
      default:
        errorMessage = `語音識別錯誤: ${event.error}`
    }

    error.value = errorMessage
    emit('error', errorMessage)
  }

  speechRecognition.value.onend = () => {
    isListening.value = false
  }

  return true
}

// 開始錄音
const startRecording = async () => {
  try {
    error.value = ''
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    mediaRecorder.value = new MediaRecorder(stream)
    
    mediaRecorder.value.onstop = () => {
      stream.getTracks().forEach(track => track.stop())
    }
    
    mediaRecorder.value.start()
    isRecording.value = true
    recordingTime.value = 0
    
    // 開始語音識別
    if (speechRecognition.value) {
      speechRecognition.value.start()
    }
    
    // 開始計時
    recordingInterval.value = window.setInterval(() => {
      recordingTime.value++
    }, 1000)
    
    emit('recordingStart')
    props.onRecordingStart?.()
    
  } catch (err) {
    error.value = '無法訪問麥克風，請檢查權限設定'
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

onMounted(() => {
  initializeSpeechRecognition()
})

onUnmounted(() => {
  cleanup()
})
</script>
