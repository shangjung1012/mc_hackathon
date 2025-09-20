/**
 * 相機服務
 * 處理相機訪問、拍照和語音指令偵測
 */

export interface CameraOptions {
  width?: number
  height?: number
  facingMode?: 'user' | 'environment'
}

export interface PhotoCaptureResult {
  dataUrl: string
  blob: Blob
  timestamp: Date
}

export class CameraService {
  private stream: MediaStream | null = null
  private videoElement: HTMLVideoElement | null = null
  private canvas: HTMLCanvasElement | null = null
  private isActive = false
  private options: CameraOptions = {
    width: 640,
    height: 480,
    facingMode: 'environment'
  }

  constructor(options?: CameraOptions) {
    this.options = { ...this.options, ...options }
  }

  /**
   * 初始化相機
   */
  public async initialize(videoElement: HTMLVideoElement): Promise<void> {
    try {
      this.videoElement = videoElement
      
      // 請求相機權限
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: this.options.width,
          height: this.options.height,
          facingMode: this.options.facingMode
        }
      })

      // 設定視頻元素
      this.videoElement.srcObject = this.stream
      this.videoElement.play()
      
      this.isActive = true
    } catch (error) {
      console.error('相機初始化失敗:', error)
      throw new Error('無法訪問相機，請檢查權限設定')
    }
  }

  /**
   * 拍照
   */
  public capturePhoto(): PhotoCaptureResult | null {
    if (!this.videoElement || !this.isActive) {
      return null
    }

    // 創建 canvas 元素
    if (!this.canvas) {
      this.canvas = document.createElement('canvas')
    }

    const canvas = this.canvas
    const video = this.videoElement
    
    // 設定 canvas 尺寸
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // 繪製視頻幀到 canvas
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    }

    // 轉換為 Blob 和 DataURL
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (blob) {
          const dataUrl = canvas.toDataURL('image/jpeg', 0.8)
          resolve({
            dataUrl,
            blob,
            timestamp: new Date()
          })
        } else {
          resolve(null)
        }
      }, 'image/jpeg', 0.8)
    }) as Promise<PhotoCaptureResult>
  }

  /**
   * 停止相機
   */
  public stop(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop())
      this.stream = null
    }
    
    if (this.videoElement) {
      this.videoElement.srcObject = null
    }
    
    this.isActive = false
  }

  /**
   * 檢查相機是否可用
   */
  public isSupported(): boolean {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  }

  /**
   * 獲取當前狀態
   */
  public getIsActive(): boolean {
    return this.isActive
  }

  /**
   * 清理資源
   */
  public destroy(): void {
    this.stop()
    this.videoElement = null
    this.canvas = null
  }
}

// 創建單例實例
export const cameraService = new CameraService()

// 導出便捷函數
export const useCamera = (options?: CameraOptions) => {
  return new CameraService(options)
}
