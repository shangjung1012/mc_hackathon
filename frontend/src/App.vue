<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
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
      <!-- 錄音按鈕 -->
      <button
        @click="toggleRecording"
        :class="[
          'w-48 h-48 rounded-full transition-all duration-300 transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-4 focus:ring-opacity-50',
          isRecording 
            ? 'bg-red-500 hover:bg-red-600 focus:ring-red-300 shadow-lg shadow-red-200' 
            : 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-300 shadow-lg shadow-blue-200'
        ]"
      >
        <div class="flex items-center justify-center h-full">
          <!-- 未錄音時顯示三角形（播放圖標） -->
          <div v-if="!isRecording" class="w-0 h-0 border-l-[24px] border-l-white border-t-[18px] border-t-transparent border-b-[18px] border-b-transparent ml-2"></div>
          <!-- 錄音時顯示正方形（停止圖標） -->
          <div v-else class="w-8 h-8 bg-white rounded-sm"></div>
        </div>
      </button>
      
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
      
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick } from 'vue'
import { useSpeechToText, type SpeechRecognitionResult } from './services/speechToText'
import { useCamera, type PhotoCaptureResult } from './services/cameraService'
import { useVoiceCommand, type CommandMatch } from './services/voiceCommandService'

const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingTime = ref(0)
const error = ref('')
const recordingInterval = ref<number | null>(null)

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

// 初始化語音轉文字
const initializeSpeechToText = () => {
  speechRecognitionSupported.value = speechToText.isSupported()
  
  if (speechRecognitionSupported.value) {
    speechToText.setCallbacks({
      onResult: (result: SpeechRecognitionResult) => {
        if (result.isFinal) {
          transcriptText.value += result.transcript + ' '
          interimText.value = ''
          
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
    error.value = '無法訪問麥克風，請檢查權限設定'
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
      
      // 保存最新照片
      latestPhoto.value = photo
      
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



// 初始化
initializeSpeechToText()

// 清理資源
onUnmounted(() => {
  if (recordingInterval.value) {
    clearInterval(recordingInterval.value)
  }
  speechToText.destroy()
  camera.destroy()
  voiceCommand.destroy()
})
</script>
