/**
 * 用戶認證服務
 * 處理登入和註冊功能
 */

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

export interface LoginRequest {
  username: string
}

export interface RegisterRequest {
  username: string
}

export class AuthService {
  private baseUrl = '/api'

  /**
   * 用戶註冊
   */
  public async register(username: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/users/register?username=${encodeURIComponent(username)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          message: data.detail || '註冊失敗'
        }
      }

      // 保存 token 到 localStorage
      if (data.token) {
        localStorage.setItem('auth_token', data.token)
      }

      return {
        success: true,
        user: data.user,
        message: data.message || '註冊成功'
      }
    } catch (error) {
      console.error('註冊錯誤:', error)
      return {
        success: false,
        message: '網路連線錯誤，請稍後再試'
      }
    }
  }

  /**
   * 用戶登入
   */
  public async login(username: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/users/login?username=${encodeURIComponent(username)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          message: data.detail || '登入失敗'
        }
      }

      // 保存 token 到 localStorage
      if (data.token) {
        localStorage.setItem('auth_token', data.token)
      }

      return {
        success: true,
        user: data.user,
        message: data.message || '登入成功'
      }
    } catch (error) {
      console.error('登入錯誤:', error)
      return {
        success: false,
        message: '網路連線錯誤，請稍後再試'
      }
    }
  }

  /**
   * 檢查用戶是否已登入
   */
  public isLoggedIn(): boolean {
    return !!localStorage.getItem('auth_token')
  }

  /**
   * 獲取當前用戶
   */
  public getCurrentUser(): User | null {
    const token = localStorage.getItem('auth_token')
    if (!token) return null

    try {
      // 簡單的 token 解析（實際應用中應該驗證 token 的有效性）
      const userData = localStorage.getItem('current_user')
      return userData ? JSON.parse(userData) : null
    } catch {
      return null
    }
  }

  /**
   * 登出
   */
  public logout(): void {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('current_user')
  }

  /**
   * 保存用戶資料
   */
  public saveUser(user: User): void {
    localStorage.setItem('current_user', JSON.stringify(user))
  }
}

// 創建單例實例
export const authService = new AuthService()

// 導出便捷函數
export const useAuth = () => {
  return authService
}
