/**
 * 語音指令服務
 * 處理語音指令的模糊匹配和執行
 */

export interface VoiceCommand {
  keywords: string[]
  action: string
  threshold?: number // 相似度閾值，預設 0.6
}

export interface CommandMatch {
  command: VoiceCommand
  confidence: number
  matchedText: string
}

export class VoiceCommandService {
  private commands: VoiceCommand[] = [
    {
      keywords: ['開啟拍照模式', '打開拍照模式', '拍照模式', '相機模式', '開啟相機', '打開相機'],
      action: 'camera_mode',
      threshold: 0.6
    },
    {
      keywords: ['拍照', '拍一張', '拍照片', '照相', '拍攝'],
      action: 'take_photo',
      threshold: 0.7
    },
    {
      keywords: ['關閉拍照模式', '關閉相機', '退出拍照', '退出相機'],
      action: 'close_camera',
      threshold: 0.6
    }
  ]

  /**
   * 計算兩個字符串的相似度 (使用 Levenshtein 距離)
   */
  private calculateSimilarity(str1: string, str2: string): number {
    const len1 = str1.length
    const len2 = str2.length
    
    if (len1 === 0) return len2 === 0 ? 1 : 0
    if (len2 === 0) return 0

    const matrix: number[][] = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0))

    // 初始化第一行和第一列
    for (let i = 0; i <= len1; i++) matrix[i][0] = i
    for (let j = 0; j <= len2; j++) matrix[0][j] = j

    // 填充矩陣
    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,      // 刪除
          matrix[i][j - 1] + 1,      // 插入
          matrix[i - 1][j - 1] + cost // 替換
        )
      }
    }

    const maxLen = Math.max(len1, len2)
    return maxLen === 0 ? 1 : (maxLen - matrix[len1][len2]) / maxLen
  }

  /**
   * 模糊匹配語音指令
   */
  public matchCommand(transcript: string): CommandMatch | null {
    const normalizedTranscript = transcript.trim().toLowerCase()
    
    let bestMatch: CommandMatch | null = null
    let bestConfidence = 0

    for (const command of this.commands) {
      for (const keyword of command.keywords) {
        const normalizedKeyword = keyword.toLowerCase()
        const similarity = this.calculateSimilarity(normalizedTranscript, normalizedKeyword)
        
        if (similarity >= (command.threshold || 0.6) && similarity > bestConfidence) {
          bestMatch = {
            command,
            confidence: similarity,
            matchedText: keyword
          }
          bestConfidence = similarity
        }
      }
    }

    return bestMatch
  }

  /**
   * 添加自定義指令
   */
  public addCommand(command: VoiceCommand): void {
    this.commands.push(command)
  }

  /**
   * 移除指令
   */
  public removeCommand(action: string): void {
    this.commands = this.commands.filter(cmd => cmd.action !== action)
  }

  /**
   * 獲取所有指令
   */
  public getCommands(): VoiceCommand[] {
    return [...this.commands]
  }

  /**
   * 清理資源
   */
  public destroy(): void {
    this.commands = []
  }
}

// 創建單例實例
export const voiceCommandService = new VoiceCommandService()

// 導出便捷函數
export const useVoiceCommand = () => {
  return voiceCommandService
}
