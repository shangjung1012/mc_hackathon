import { ref } from 'vue'
import type { PermissionState } from './usePermissions'

export function useCamera() {
  const videoEl = ref<HTMLVideoElement | null>(null)
  const cameraReady = ref(false)
  const cameraError = ref<string | null>(null)
  let mediaStream: MediaStream | null = null

  async function startCamera(options?: {
    cameraPermissionRef?: { value: PermissionState },
    refreshPermissionsFromDevices?: () => Promise<void> | void,
  }) {
    try {
      cameraError.value = null
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 1706 } },
        audio: false,
      })
      if (videoEl.value) {
        videoEl.value.srcObject = mediaStream
        await videoEl.value.play()
        cameraReady.value = true
      }
      if (options?.cameraPermissionRef) options.cameraPermissionRef.value = 'granted'
      if (options?.refreshPermissionsFromDevices) await options.refreshPermissionsFromDevices()
    } catch (e: any) {
      cameraError.value = e?.message || '無法開啟相機（需要 HTTPS 或權限）'
      cameraReady.value = false
      const name = e?.name || ''
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        if (options?.cameraPermissionRef) options.cameraPermissionRef.value = 'denied'
      }
    }
  }

  function stopCamera() {
    if (mediaStream) {
      mediaStream.getTracks().forEach(t => t.stop())
      mediaStream = null
    }
    cameraReady.value = false
  }

  async function captureFrame(): Promise<{ blob: Blob, url: string } | null> {
    if (!videoEl.value) return null
    const video = videoEl.value
    const canvas = document.createElement('canvas')
    const vw = video.videoWidth || 1080
    const vh = video.videoHeight || 1440
    canvas.width = vw
    canvas.height = vh
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(video, 0, 0, vw, vh)
    const blob: Blob | null = await new Promise(resolve => canvas.toBlob(b => resolve(b), 'image/jpeg', 0.9))
    if (!blob) return null
    const url = URL.createObjectURL(blob)
    if (navigator.vibrate) navigator.vibrate(10)
    return { blob, url }
  }

  return {
    videoEl,
    cameraReady,
    cameraError,
    startCamera,
    stopCamera,
    captureFrame,
  }
}
