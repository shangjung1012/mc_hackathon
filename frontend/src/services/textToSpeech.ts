/**
 * 文字轉語音服務
 * 使用瀏覽器內建的 Web Speech API
 */

export interface TTSOptions {
  language?: string
  rate?: number
  pitch?: number
  volume?: number
  voice?: SpeechSynthesisVoice
}

export interface TTSCallbacks {
  onStart?: () => void
  onEnd?: () => void
  onError?: (error: string) => void
}

export class TextToSpeechService {
  private isSpeaking = false
  private callbacks: TTSCallbacks = {}
  private options: TTSOptions = {
    language: 'zh-TW',
    rate: 0.9,
    pitch: 1.0,
    volume: 1.0
  }

  constructor(options?: TTSOptions) {
    this.options = { ...this.options, ...options }
  }

  /**
   * 檢查瀏覽器是否支援語音合成
   */
  public isSupported(): boolean {
    return 'speechSynthesis' in window
  }

  /**
   * 獲取可用的語音列表
   */
  public getVoices(): SpeechSynthesisVoice[] {
    return speechSynthesis.getVoices()
  }

  /**
   * 獲取中文語音
   */
  public getChineseVoices(): SpeechSynthesisVoice[] {
    return this.getVoices().filter(voice => 
      voice.lang.startsWith('zh') || 
      voice.name.includes('Chinese') ||
      voice.name.includes('中文')
    )
  }

  /**
   * 設定回調函數
   */
  public setCallbacks(callbacks: TTSCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  /**
   * 更新選項
   */
  public updateOptions(options: Partial<TTSOptions>): void {
    this.options = { ...this.options, ...options }
  }

  /**
   * 檢查是否可以播放語音（處理瀏覽器自動播放限制）
   */
  public canPlay(): boolean {
    if (!this.isSupported()) {
      return false
    }
    
    // 檢查是否有用戶手勢上下文
    try {
      // 嘗試創建一個測試的 utterance 來檢查是否被阻止
      new SpeechSynthesisUtterance('')
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * 播放語音
   */
  public speak(text: string, options?: Partial<TTSOptions>): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.isSupported()) {
        const error = '此瀏覽器不支援語音合成功能'
        this.callbacks.onError?.(error)
        reject(new Error(error))
        return
      }

      // 停止當前播放
      this.stop()

      const utterance = new SpeechSynthesisUtterance(text)
      const finalOptions = { ...this.options, ...options }

      // 設定語音選項
      utterance.lang = finalOptions.language || 'zh-TW'
      utterance.rate = finalOptions.rate || 0.9
      utterance.pitch = finalOptions.pitch || 1.0
      utterance.volume = finalOptions.volume || 1.0

      // 如果有指定語音，使用指定的語音
      if (finalOptions.voice) {
        utterance.voice = finalOptions.voice
      } else {
        // 自動選擇中文語音
        const chineseVoices = this.getChineseVoices()
        if (chineseVoices.length > 0) {
          utterance.voice = chineseVoices[0]
        }
      }

      // 綁定事件
      utterance.onstart = () => {
        this.isSpeaking = true
        this.callbacks.onStart?.()
      }

      utterance.onend = () => {
        this.isSpeaking = false
        this.callbacks.onEnd?.()
        resolve()
      }

      utterance.onerror = (event) => {
        this.isSpeaking = false
        let errorMessage = `語音播放錯誤: ${event.error}`
        
        // 處理特定的錯誤類型
        if (event.error === 'not-allowed') {
          errorMessage = '語音播放被瀏覽器阻止，請點擊頁面後再試'
        } else if (event.error === 'interrupted') {
          errorMessage = '語音播放被中斷'
        } else if (event.error === 'audio-busy') {
          errorMessage = '音訊設備忙碌中，請稍後再試'
        } else if (event.error === 'audio-hardware') {
          errorMessage = '音訊硬體錯誤'
        }
        
        this.callbacks.onError?.(errorMessage)
        reject(new Error(errorMessage))
      }

      // 開始播放
      try {
        speechSynthesis.speak(utterance)
      } catch (error) {
        this.isSpeaking = false
        const errorMessage = `語音播放失敗: ${error instanceof Error ? error.message : String(error)}`
        this.callbacks.onError?.(errorMessage)
        reject(new Error(errorMessage))
      }
    })
  }

  /**
   * 停止播放
   */
  public stop(): void {
    if (this.isSpeaking) {
      speechSynthesis.cancel()
      this.isSpeaking = false
    }
  }

  /**
   * 暫停播放
   */
  public pause(): void {
    if (this.isSpeaking) {
      speechSynthesis.pause()
    }
  }

  /**
   * 恢復播放
   */
  public resume(): void {
    if (this.isSpeaking) {
      speechSynthesis.resume()
    }
  }

  /**
   * 獲取當前播放狀態
   */
  public getIsSpeaking(): boolean {
    return this.isSpeaking
  }

  /**
   * 清理資源
   */
  public destroy(): void {
    this.stop()
    this.callbacks = {}
  }
}

// 創建單例實例
export const textToSpeechService = new TextToSpeechService()

// 導出便捷函數
export const useTextToSpeech = (callbacks?: TTSCallbacks) => {
  if (callbacks) {
    textToSpeechService.setCallbacks(callbacks)
  }
  return textToSpeechService
}
