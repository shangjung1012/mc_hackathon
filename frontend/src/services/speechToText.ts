/**
 * 語音轉文字服務
 * 使用瀏覽器內建的 Web Speech API
 */

export interface SpeechRecognitionResult {
  transcript: string
  confidence: number
  isFinal: boolean
}

export interface SpeechRecognitionOptions {
  language?: string
  continuous?: boolean
  interimResults?: boolean
  maxAlternatives?: number
}

export interface SpeechRecognitionCallbacks {
  onResult?: (result: SpeechRecognitionResult) => void
  onError?: (error: string) => void
  onStart?: () => void
  onEnd?: () => void
  onNoMatch?: () => void
}

export class SpeechToTextService {
  private recognition: any = null
  private isListening = false
  private callbacks: SpeechRecognitionCallbacks = {}
  private options: SpeechRecognitionOptions = {
    language: 'zh-TW',
    continuous: true,
    interimResults: true,
    maxAlternatives: 1
  }

  constructor(options?: SpeechRecognitionOptions) {
    this.options = { ...this.options, ...options }
    this.initializeRecognition()
  }

  /**
   * 初始化語音識別
   */
  private initializeRecognition(): void {
    // 檢查瀏覽器支援
    if (!this.isSupported()) {
      throw new Error('此瀏覽器不支援語音識別功能')
    }

    // 創建語音識別實例
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    this.recognition = new SpeechRecognition()

    // 設定選項
    this.recognition.lang = this.options.language
    this.recognition.continuous = this.options.continuous
    this.recognition.interimResults = this.options.interimResults
    this.recognition.maxAlternatives = this.options.maxAlternatives

    // 綁定事件
    this.bindEvents()
  }

  /**
   * 綁定語音識別事件
   */
  private bindEvents(): void {
    this.recognition.onstart = () => {
      this.isListening = true
      this.callbacks.onStart?.()
    }

    this.recognition.onresult = (event: any) => {
      const result = event.results[event.resultIndex]
      const transcript = result[0].transcript
      const confidence = result[0].confidence
      const isFinal = result.isFinal

      this.callbacks.onResult?.({
        transcript,
        confidence,
        isFinal
      })
    }

    this.recognition.onerror = (event: any) => {
      this.isListening = false
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

      this.callbacks.onError?.(errorMessage)
    }

    this.recognition.onend = () => {
      this.isListening = false
      this.callbacks.onEnd?.()
    }

    this.recognition.onnomatch = () => {
      this.callbacks.onNoMatch?.()
    }
  }

  /**
   * 開始語音識別
   */
  public startListening(): void {
    if (!this.recognition) {
      throw new Error('語音識別未初始化')
    }

    if (this.isListening) {
      console.warn('語音識別已在進行中')
      return
    }

    try {
      this.recognition.start()
    } catch (error) {
      this.callbacks.onError?.('無法開始語音識別')
    }
  }

  /**
   * 停止語音識別
   */
  public stopListening(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop()
    }
  }

  /**
   * 中止語音識別
   */
  public abortListening(): void {
    if (this.recognition && this.isListening) {
      this.recognition.abort()
    }
  }

  /**
   * 設定回調函數
   */
  public setCallbacks(callbacks: SpeechRecognitionCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  /**
   * 更新選項
   */
  public updateOptions(options: Partial<SpeechRecognitionOptions>): void {
    this.options = { ...this.options, ...options }
    
    if (this.recognition) {
      this.recognition.lang = this.options.language
      this.recognition.continuous = this.options.continuous
      this.recognition.interimResults = this.options.interimResults
      this.recognition.maxAlternatives = this.options.maxAlternatives
    }
  }

  /**
   * 檢查瀏覽器是否支援語音識別
   */
  public isSupported(): boolean {
    return 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
  }

  /**
   * 獲取當前監聽狀態
   */
  public getIsListening(): boolean {
    return this.isListening
  }

  /**
   * 獲取支援的語言列表
   */
  public getSupportedLanguages(): string[] {
    return [
      'zh-TW', // 繁體中文
      'zh-CN', // 簡體中文
      'en-US', // 美式英語
      'en-GB', // 英式英語
      'ja-JP', // 日語
      'ko-KR', // 韓語
      'es-ES', // 西班牙語
      'fr-FR', // 法語
      'de-DE', // 德語
      'it-IT', // 義大利語
      'pt-BR', // 葡萄牙語
      'ru-RU'  // 俄語
    ]
  }

  /**
   * 清理資源
   */
  public destroy(): void {
    if (this.recognition) {
      this.abortListening()
      this.recognition = null
    }
    this.callbacks = {}
  }
}

// 創建單例實例
export const speechToTextService = new SpeechToTextService()

// 導出便捷函數
export const useSpeechToText = (callbacks?: SpeechRecognitionCallbacks) => {
  if (callbacks) {
    speechToTextService.setCallbacks(callbacks)
  }
  return speechToTextService
}
