/**
 * 用戶認證服務
 * 處理登入和註冊功能
 */

import { useAPI, type User, type AuthResponse } from './useAPI'

export interface LoginRequest {
  username: string
}

export interface RegisterRequest {
  username: string
}

export class AuthService {
  private api = useAPI()

  /**
   * 用戶註冊
   */
  public async register(username: string): Promise<AuthResponse> {
    return this.api.register(username)
  }

  /**
   * 用戶登入
   */
  public async login(username: string): Promise<AuthResponse> {
    return this.api.login(username)
  }

  /**
   * 檢查用戶是否已登入
   */
  public isLoggedIn(): boolean {
    return !!localStorage.getItem('auth_token')
  }

  /**
   * 獲取當前用戶（從 API 獲取最新信息）
   */
  public async getCurrentUser(): Promise<User | null> {
    const token = localStorage.getItem('auth_token')
    if (!token) return null

    try {
      const response = await this.api.getCurrentUser()
      if (response.success && response.data) {
        this.saveUser(response.data)
        return response.data
      }
      return null
    } catch {
      return null
    }
  }

  /**
   * 獲取本地存儲的用戶信息（同步方法）
   */
  public getCachedUser(): User | null {
    const token = localStorage.getItem('auth_token')
    if (!token) return null

    try {
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

// 重新導出類型
export type { User, AuthResponse } from './useAPI'

// 創建單例實例
export const authService = new AuthService()

// 導出便捷函數
export const useAuth = () => {
  return authService
}
