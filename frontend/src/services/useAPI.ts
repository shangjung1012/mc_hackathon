/**
 * API 服務統一管理
 * 集中處理所有後端 API 調用
 */

// API 基礎配置 - 根據前端協議動態調整後端協議
const getApiBase = () => {
  const backendUrl = (import.meta as any).env?.VITE_BACKEND_URL || 'http://localhost:8000'
  const cleanUrl = backendUrl.replace(/\/+$/, '')
  
  // 檢測前端是否使用 HTTPS
  const isHttps = window.location.protocol === 'https:'
  
  // 如果前端是 HTTPS 但後端是 HTTP，則調整後端為 HTTPS
  if (isHttps && cleanUrl.startsWith('http://')) {
    return cleanUrl.replace('http://', 'https://')
  }
  
  // 如果前端是 HTTP 但後端是 HTTPS，則調整後端為 HTTP
  if (!isHttps && cleanUrl.startsWith('https://')) {
    return cleanUrl.replace('https://', 'http://')
  }
  
  return cleanUrl
}

const API_BASE = getApiBase()

// 通用 API 響應類型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// 用戶相關類型
export interface User {
  id: string
  username: string
  createdAt: string
}

export interface AuthResponse {
  success: boolean
  user?: User
  message?: string
  token?: string
}

// Gemini 分析請求類型
export interface GeminiAnalyzeRequest {
  text: string
  system_instruction: string
  image?: Blob
}

export class ApiService {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
  }

  /**
   * 獲取認證標頭
   */
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('auth_token')
    if (token) {
      return {
        'Authorization': `Bearer ${token}`
      }
    }
    return {}
  }

  /**
   * 通用 fetch 包裝器
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders(),
          ...options.headers,
        },
        ...options,
      })
      console.log('url', url)
      console.log('response', response)
      const contentType = response.headers.get('content-type') || ''
      
      // 處理音訊響應
      if (contentType.includes('audio')) {
        return {
          success: true,
          data: response as any, // 返回 Response 對象供後續處理
        }
      }

      // 處理 JSON 響應
      if (contentType.includes('application/json')) {
        const data = await response.json()
        
        if (!response.ok) {
          return {
            success: false,
            error: data.detail || data.message || `HTTP ${response.status}`,
            message: data.detail || data.message || `HTTP ${response.status}`,
          }
        }

        return {
          success: true,
          data,
        }
      }

      // 處理其他響應類型
      const text = await response.text()
      if (!response.ok) {
        return {
          success: false,
          error: text || `HTTP ${response.status}`,
          message: text || `HTTP ${response.status}`,
        }
      }

      return {
        success: true,
        data: text as any,
      }
    } catch (error) {
      console.error('API 請求錯誤:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : '網路連線錯誤',
        message: '網路連線錯誤，請稍後再試',
      }
    }
  }

  /**
   * 用戶註冊
   */
  async register(username: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>(
      `/users/register?username=${encodeURIComponent(username)}`,
      {
        method: 'POST',
      }
    )

    if (response.success && response.data) {
      // 保存 token 到 localStorage
      if (response.data.token) {
        localStorage.setItem('auth_token', response.data.token)
      }
      return response.data
    }

    return {
      success: false,
      message: response.message || '註冊失敗',
    }
  }

  /**
   * 用戶登入
   */
  async login(username: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>(
      `/users/login?username=${encodeURIComponent(username)}`,
      {
        method: 'POST',
      }
    )

    if (response.success && response.data) {
      // 保存 token 到 localStorage
      if (response.data.token) {
        localStorage.setItem('auth_token', response.data.token)
      }
      return response.data
    }

    return {
      success: false,
      message: response.message || '登入失敗',
    }
  }

  /**
   * Gemini 分析並語音合成
   */
  async analyzeAndSpeak(request: GeminiAnalyzeRequest): Promise<ApiResponse<Response>> {
    try {
      const form = new FormData()
      form.append('text', request.text)
      form.append('system_instruction', request.system_instruction)
      
      if (request.image) {
        form.append('image', request.image, 'photo.jpg')
      }

      const response = await fetch(`${this.baseUrl}/gemini/analyze-and-speak`, {
        method: 'POST',
        headers: {
          ...this.getAuthHeaders(),
        },
        body: form,
      })

      if (!response.ok) {
        const text = await response.text()
        return {
          success: false,
          error: `API 回傳錯誤: ${response.status} ${text}`,
          message: `API 回傳錯誤: ${response.status} ${text}`,
        }
      }

      return {
        success: true,
        data: response,
      }
    } catch (error) {
      console.error('Gemini API 錯誤:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Gemini API 調用失敗',
        message: '語音合成失敗，請稍後再試',
      }
    }
  }

  /**
   * 檢查健康狀態
   */
  async checkHealth(): Promise<ApiResponse<any>> {
    return this.request('/health')
  }

  /**
   * 獲取系統提示
   */
  async getSystemPrompt(): Promise<ApiResponse<string>> {
    return this.request('/system-prompt')
  }

  /**
   * 獲取當前用戶信息
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/users/me')
  }

  /**
   * 文字轉語音
   */
  async textToSpeech(text: string): Promise<ApiResponse<Response>> {
    try {
      const response = await fetch(`${this.baseUrl}/tts/speak`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders(),
        },
        body: JSON.stringify({ text }),
      })

      if (!response.ok) {
        const text = await response.text()
        return {
          success: false,
          error: `TTS API 錯誤: ${response.status} ${text}`,
          message: `TTS API 錯誤: ${response.status} ${text}`,
        }
      }

      return {
        success: true,
        data: response,
      }
    } catch (error) {
      console.error('TTS API 錯誤:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'TTS API 調用失敗',
        message: '語音合成失敗，請稍後再試',
      }
    }
  }
}

// 創建單例實例
export const apiService = new ApiService()

// 導出便捷函數
export const useAPI = () => {
  return apiService
}

// 類型已在上面定義並導出
