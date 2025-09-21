<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
    <div class="text-center max-w-2xl mx-auto px-4">
      <!-- 首頁開始畫面 -->
      <div v-if="currentStep === 'welcome'" class="space-y-8">
        <h1 class="text-4xl font-bold text-gray-800 dark:text-gray-200 mb-8">
          語音助手服務
        </h1>
        <VoiceRecordingButton
          :disabled="isProcessing"
          @transcript="handleWelcomeTranscript"
          @error="handleError"
        />
        <p v-if="isProcessing" class="text-lg text-gray-600 dark:text-gray-400">
          處理中...
        </p>
        <p v-if="error" class="text-red-500 text-sm">
          {{ error }}
        </p>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          <p>請說：「開始使用」</p>
        </div>
        
        <!-- 臨時調試按鈕 - 透明全螢幕覆蓋 -->
        <button 
          @click="testVoiceCommand" 
          class="fixed inset-0 w-full h-full bg-transparent border-0 cursor-pointer z-50"
          style="background: transparent; border: none; outline: none;"
        >
          <!-- 隱藏文字，但保持可點擊區域 -->
          <span class="sr-only">測試語音指令</span>
        </button>
      </div>

      <!-- 登入/註冊選擇 -->
      <div v-else-if="currentStep === 'auth-choice'" class="space-y-8">
        <h2 class="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-8">
          請說出您要的操作
        </h2>
        <VoiceRecordingButton
          :disabled="isProcessing"
          @transcript="handleAuthChoiceTranscript"
          @error="handleError"
        />
        <p v-if="isProcessing" class="text-lg text-gray-600 dark:text-gray-400">
          處理中...
        </p>
        <p v-if="error" class="text-red-500 text-sm">
          {{ error }}
        </p>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          <p>請說：「登入」或「註冊」</p>
        </div>
      </div>

      <!-- 登入流程 -->
      <div v-else-if="currentStep === 'login'" class="space-y-8">
        <h2 class="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-8">
          登入
        </h2>
        <VoiceRecordingButton
          :disabled="isProcessing"
          @transcript="handleLoginTranscript"
          @error="handleError"
        />
        <p v-if="isProcessing" class="text-lg text-gray-600 dark:text-gray-400">
          處理中...
        </p>
        <p v-if="error" class="text-red-500 text-sm">
          {{ error }}
        </p>
        <button
          @click="goBackToChoice"
          class="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          返回
        </button>
      </div>

      <!-- 註冊流程 -->
      <div v-else-if="currentStep === 'register'" class="space-y-8">
        <h2 class="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-8">
          註冊
        </h2>
        <VoiceRecordingButton
          :disabled="isProcessing"
          @transcript="handleRegisterTranscript"
          @error="handleError"
        />
        <p v-if="isProcessing" class="text-lg text-gray-600 dark:text-gray-400">
          處理中...
        </p>
        <p v-if="error" class="text-red-500 text-sm">
          {{ error }}
        </p>
        <button
          @click="goBackToChoice"
          class="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          返回
        </button>
      </div>

      <!-- 登入成功 -->
      <div v-else-if="currentStep === 'login-success'" class="space-y-8">
        <h2 class="text-3xl font-bold text-green-600 dark:text-green-400 mb-8">
          登入成功！
        </h2>
        <p class="text-lg text-gray-600 dark:text-gray-400">
          歡迎回來，{{ currentUser?.username }}
        </p>
        <p class="text-sm text-gray-500 dark:text-gray-500">
          重聽教學請下滑，三秒後將開啟服務
        </p>
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
          {{ countdown }}
        </div>
      </div>

      <!-- 註冊成功 -->
      <div v-else-if="currentStep === 'register-success'" class="space-y-8">
        <h2 class="text-3xl font-bold text-green-600 dark:text-green-400 mb-8">
          註冊成功！
        </h2>
        <p class="text-lg text-gray-600 dark:text-gray-400">
          歡迎您註冊本服務，您的使用者名稱是 {{ currentUser?.username }}
        </p>
        <p class="text-sm text-gray-500 dark:text-gray-500">
          三秒後將開啟服務
        </p>
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
          {{ countdown }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import VoiceRecordingButton from '../components/VoiceRecordingButton.vue'
import { useTextToSpeech } from '../services/textToSpeech'
import { useAuth, type User } from '../services/authService'

// 定義 emits
const emit = defineEmits<{
  loginSuccess: [user: User]
}>()

// 狀態管理
const currentStep = ref<'welcome' | 'auth-choice' | 'login' | 'register' | 'login-success' | 'register-success'>('welcome')
const isProcessing = ref(false)
const error = ref('')
const currentUser = ref<User | null>(null)
const countdown = ref(3)

// 服務
const tts = useTextToSpeech()
const auth = useAuth()

// 倒數計時
let countdownInterval: number | null = null

// 處理首頁語音輸入
const handleWelcomeTranscript = async (transcript: string) => {
  console.log('🎤 收到語音轉文字:', transcript)
  
  if (isProcessing.value) {
    console.log('⏳ 正在處理中，忽略此次輸入')
    return
  }
  
  isProcessing.value = true
  error.value = ''
  
  const normalizedTranscript = transcript.trim().toLowerCase()
  console.log('📝 標準化後的文字:', normalizedTranscript)
  
  try {
    if (normalizedTranscript.includes('開始') || normalizedTranscript.includes('使用') || normalizedTranscript.includes('開始使用')) {
      console.log('✅ 匹配到「開始使用」指令')
      await speak('歡迎使用語音助手服務')
      startLoginProcess()
    } else {
      console.log('❌ 未匹配到「開始使用」指令')
      error.value = '請說「開始使用」'
      await speak('請說開始使用')
    }
  } catch (err) {
    console.error('❌ 語音處理錯誤:', err)
    error.value = '語音識別錯誤，請重試'
    await speak('語音識別錯誤，請重試')
  } finally {
    isProcessing.value = false
  }
}

// 開始登入流程
const startLoginProcess = async () => {
  console.log('🚀 開始登入流程，切換到 auth-choice 步驟')
  currentStep.value = 'auth-choice'
  console.log('📱 當前步驟:', currentStep.value)
  await speak('請說出您要的操作，登入或註冊')
}

// 處理登入/註冊選擇的語音輸入
const handleAuthChoiceTranscript = async (transcript: string) => {
  if (isProcessing.value) return
  
  isProcessing.value = true
  error.value = ''
  
  const normalizedTranscript = transcript.trim().toLowerCase()
  
  try {
    if (normalizedTranscript.includes('登入') || normalizedTranscript.includes('登錄')) {
      await speak('開始登入流程')
      startLogin()
    } else if (normalizedTranscript.includes('註冊') || normalizedTranscript.includes('註冊')) {
      await speak('開始註冊流程')
      startRegister()
    } else {
      error.value = '請說「登入」或「註冊」'
      await speak('請說登入或註冊')
    }
  } catch (err) {
    error.value = '語音識別錯誤，請重試'
    await speak('語音識別錯誤，請重試')
  } finally {
    isProcessing.value = false
  }
}

// 開始登入
const startLogin = async () => {
  currentStep.value = 'login'
  error.value = ''
  await speak('請輸入使用者名稱')
}

// 開始註冊
const startRegister = async () => {
  currentStep.value = 'register'
  error.value = ''
  await speak('請輸入註冊使用者名稱')
}

// 處理登入語音輸入
const handleLoginTranscript = async (transcript: string) => {
  if (isProcessing.value) return
  
  isProcessing.value = true
  error.value = ''
  
  try {
    const result = await auth.login(transcript.trim())
    
    if (result.success && result.user) {
      currentUser.value = result.user
      auth.saveUser(result.user)
      currentStep.value = 'login-success'
      await speak('登入成功，重聽教學請下滑，三秒後將開啟服務')
      startCountdown()
    } else {
      error.value = result.message || '登入失敗'
      await speak('登入失敗，請重試')
    }
  } catch (err) {
    error.value = '登入時發生錯誤'
    await speak('登入時發生錯誤，請重試')
  } finally {
    isProcessing.value = false
  }
}

// 處理註冊語音輸入
const handleRegisterTranscript = async (transcript: string) => {
  if (isProcessing.value) return
  
  isProcessing.value = true
  error.value = ''
  
  try {
    const result = await auth.register(transcript.trim())
    
    if (result.success && result.user) {
      currentUser.value = result.user
      auth.saveUser(result.user)
      currentStep.value = 'register-success'
      await speak('歡迎您註冊本服務，您的使用者名稱是 ' + result.user.username)
      startCountdown()
    } else {
      error.value = result.message || '註冊失敗'
      await speak('註冊失敗，請重試')
    }
  } catch (err) {
    error.value = '註冊時發生錯誤'
    await speak('註冊時發生錯誤，請重試')
  } finally {
    isProcessing.value = false
  }
}

// 處理錯誤
const handleError = (errorMessage: string) => {
  error.value = errorMessage
}

// 返回選擇頁面
const goBackToChoice = () => {
  currentStep.value = 'auth-choice'
  error.value = ''
}

// 開始倒數計時
const startCountdown = () => {
  countdown.value = 3
  countdownInterval = window.setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      if (countdownInterval) {
        clearInterval(countdownInterval)
        countdownInterval = null
      }
      // 發送登入成功事件
      if (currentUser.value) {
        emit('loginSuccess', currentUser.value)
      }
    }
  }, 1000)
}

// 語音播放
const speak = async (text: string) => {
  try {
    await tts.speak(text)
  } catch (err) {
    console.error('語音播放失敗:', err)
  }
}

// 測試語音指令（臨時調試功能）
const testVoiceCommand = () => {
  console.log('🧪 測試語音指令觸發')
  handleWelcomeTranscript('開始使用')
}

// 清理資源
const cleanup = () => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
  }
  tts.destroy()
}

onMounted(async () => {
  // 檢查是否已經登入
  if (auth.isLoggedIn()) {
    const user = await auth.getCurrentUser()
    if (user) {
      currentUser.value = user
      currentStep.value = 'login-success'
      startCountdown()
    }
  } else {
    // 播放歡迎語音
    await speak('歡迎使用語音助手服務，請說開始使用')
  }
})

onUnmounted(() => {
  cleanup()
})
</script>
