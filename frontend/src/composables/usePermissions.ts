import { ref } from 'vue'

export type PermissionState = 'granted' | 'denied' | 'prompt' | 'unsupported'

export function usePermissions() {
  const micPermission = ref<PermissionState>('unsupported')
  const cameraPermission = ref<PermissionState>('unsupported')
  let micPermissionWatcher: any | null = null
  let cameraPermissionWatcher: any | null = null

  async function refreshPermissionsFromDevices() {
    try {
      if (!navigator.mediaDevices || typeof navigator.mediaDevices.enumerateDevices !== 'function') return
      const devices = await navigator.mediaDevices.enumerateDevices()
      const hasLabeledMic = devices.some(d => d.kind === 'audioinput' && !!d.label)
      const hasLabeledCam = devices.some(d => d.kind === 'videoinput' && !!d.label)
      if (hasLabeledMic) micPermission.value = 'granted'
      if (hasLabeledCam) cameraPermission.value = 'granted'
    } catch {}
  }

  async function checkMicPermission() {
    try {
      if (!navigator.permissions || typeof navigator.permissions.query !== 'function') {
        micPermission.value = 'unsupported'
        return
      }
      const status = await navigator.permissions.query({ name: 'microphone' as PermissionName })
      micPermission.value = status.state as PermissionState
      micPermissionWatcher = status
      status.onchange = () => {
        micPermission.value = status.state as PermissionState
      }
    } catch {
      micPermission.value = 'unsupported'
    }
  }

  async function checkCameraPermission() {
    try {
      if (!navigator.permissions || typeof navigator.permissions.query !== 'function') {
        cameraPermission.value = 'unsupported'
        return
      }
      const status = await navigator.permissions.query({ name: 'camera' as PermissionName })
      cameraPermission.value = status.state as PermissionState
      cameraPermissionWatcher = status
      status.onchange = () => {
        cameraPermission.value = status.state as PermissionState
      }
    } catch {
      cameraPermission.value = 'unsupported'
    }
  }

  function cleanupPermissionWatchers() {
    try {
      if (micPermissionWatcher && typeof micPermissionWatcher.onchange === 'function') {
        micPermissionWatcher.onchange = null
      }
      if (cameraPermissionWatcher && typeof cameraPermissionWatcher.onchange === 'function') {
        cameraPermissionWatcher.onchange = null
      }
    } catch {}
  }

  return {
    micPermission,
    cameraPermission,
    refreshPermissionsFromDevices,
    checkMicPermission,
    checkCameraPermission,
    cleanupPermissionWatchers,
  }
}
