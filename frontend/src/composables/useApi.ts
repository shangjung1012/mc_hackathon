export type HealthStatus = 'ok' | 'error'

export function useApi() {
  const API_BASE = (import.meta as any).env?.VITE_BACKEND_URL || ''

  function resolveApiUrl(path: string): string {
    if (API_BASE && String(API_BASE).trim()) {
      return String(API_BASE).replace(/\/$/, '') + path
    }
    const host = (typeof window !== 'undefined' && window.location?.hostname) || '127.0.0.1'
    const protocol = (typeof window !== 'undefined' && window.location?.protocol === 'https:') ? 'https' : 'http'
    return `${protocol}://${host}:8000${path}`
  }

  async function checkBackendHealth(): Promise<HealthStatus> {
    const url = resolveApiUrl('/health')
    try {
      const res = await fetch(url, { method: 'GET' })
      if (!res.ok) throw new Error(String(res.status))
      const data = await res.json()
      return data?.status === 'ok' ? 'ok' : 'error'
    } catch {
      return 'error'
    }
  }
  async function synthesizeTTS(text: string, language_code = 'cmn-CN', voice_name = 'cmn-CN-Chirp3-HD-Achernar') {
    const apiUrl = resolveApiUrl('/tts/synthesize')
    const res = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language_code, voice_name })
    })
    if (!res.ok) throw new Error(String(res.status))
    return res.json()
}

  async function analyze(action: string, text: string | null, blob: Blob): Promise<any> {
    const apiUrl = resolveApiUrl('/gemini/analyze')
    const fd = new FormData()
    fd.append('action', action)
    if (text) fd.append('text', text)
    fd.append('image', new File([blob], 'photo.jpg', { type: 'image/jpeg' }))

    const res = await fetch(apiUrl, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(String(res.status))
    return res.json()
  }

  return {
    synthesizeTTS,
    resolveApiUrl,
    checkBackendHealth,
    analyze,
  }
}
