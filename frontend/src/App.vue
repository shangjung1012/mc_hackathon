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
      
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick } from 'vue'
import ActionButton from './components/ActionButton.vue'
import { useSpeechToText, type SpeechRecognitionResult } from './services/speechToText'
import { useCamera, type PhotoCaptureResult } from './services/cameraService'
import { useVoiceCommand, type CommandMatch } from './services/voiceCommandService'

const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingTime = ref(0)
const error = ref('')
const recordingInterval = ref<number | null>(null)
const sessionTranscript = ref('')
const lastSwipeDirection = ref<string | null>(null) // 'up' | 'down' | null
const lastPhotoCache = ref<PhotoCaptureResult | null>(null)
const lastPhotoUploaded = ref(false)

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
          
        // 累積本次錄音 session 的 transcript
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
  // 長按可以進入相機模式作示範
  enterCameraMode()
}

const onActionSwipe = (direction: string) => {
  lastCommand.value = `swipe: ${direction}`
  // 根據方向執行不同動作
  switch (direction) {
    case 'up':
      // 顯示範例動作：拍照（需在相機模式下）
      if (cameraMode.value) takePhoto()
      break
    case 'down':
      // 關閉相機模式
      if (cameraMode.value) exitCameraMode()
      break
    case 'left':
      // 範例：顯示上一張（暫未實作）
      lastCommand.value = '向左滑 — previous (未實作)'
      break
    case 'right':
      // 範例：顯示下一張（暫未實作）
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

  // Decide scenario
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
    if (lastPhotoCache.value && !lastPhotoUploaded.value) {
      // attach previous photo but use scenario 2 behavior
      system_instruction = '請簡短快速地回答，重點即可。'
      photoToSend = await downscaleDataUrl(lastPhotoCache.value.dataUrl, 640)
    } else {
      // no photo ever taken or already uploaded -> only text
      system_instruction = '請簡短快速地回答，重點即可。'
      photoToSend = null
    }
  }

  // Build form data
  try {
    const form = new FormData()
    form.append('transcript', transcript)
    form.append('system_instruction', system_instruction)
    if (photoToSend) {
      form.append('photo', photoToSend, 'photo.jpg')
    }

    lastCommand.value = '上傳中...'

    const res = await fetch('/api/process', {
      method: 'POST',
      body: form
    })

    if (!res.ok) {
      const text = await res.text()
      throw new Error(`API 回傳錯誤: ${res.status} ${text}`)
    }

    const data = await res.json().catch(() => null)
    lastCommand.value = '上傳完成'
    // mark photo as uploaded if we sent one
    if (photoToSend && lastPhotoCache.value) {
      lastPhotoUploaded.value = true
    }
    // 清理 swipe flag
    lastSwipeDirection.value = null
    setTimeout(() => (lastCommand.value = ''), 2000)
    return data
  } catch (err: any) {
    console.error('上傳失敗:', err)
    lastCommand.value = '上傳失敗'
    setTimeout(() => (lastCommand.value = ''), 3000)
  }
}
</script>
