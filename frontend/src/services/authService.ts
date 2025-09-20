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

// 重新導出類型
export type { User, AuthResponse } from './useAPI'

// 創建單例實例
export const authService = new AuthService()

// 導出便捷函數
export const useAuth = () => {
  return authService
}
