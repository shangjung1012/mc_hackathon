import { ref } from 'vue'

export function useTTS() {
  const ttsReady = ref(false)
  let selectedVoice: SpeechSynthesisVoice | null = null

  function pickZhVoice() {
    try {
      if (!('speechSynthesis' in window)) return
      const voices = window.speechSynthesis.getVoices() || []
      const preferred = voices.find(v => /^(zh(-|_)TW|cmn-Hant-TW)/i.test(v.lang)) || voices.find(v => /^zh/i.test(v.lang))
      selectedVoice = preferred || null
    } catch {}
  }

  function ensureTtsUnlocked() {
    try {
      if (!('speechSynthesis' in window)) return
      const unlock = new SpeechSynthesisUtterance(' ')
      unlock.volume = 0
      unlock.rate = 1
      if (selectedVoice) unlock.voice = selectedVoice
      window.speechSynthesis.cancel()
      window.speechSynthesis.resume()
      window.speechSynthesis.speak(unlock)
      ttsReady.value = true
    } catch {}
  }

  function speakText(text: string) {
    try {
      if (!('speechSynthesis' in window)) return
      if (!ttsReady.value) {
        ensureTtsUnlocked()
        if (!ttsReady.value) return
      }
      const utter = new SpeechSynthesisUtterance(text)
      utter.lang = 'zh-TW'
      if (selectedVoice) utter.voice = selectedVoice
      utter.rate = 1.0
      utter.volume = 1.0
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel()
      }
      window.speechSynthesis.resume()
      window.speechSynthesis.speak(utter)
    } catch {}
  }

  return {
    ttsReady,
    pickZhVoice,
    ensureTtsUnlocked,
    speakText,
  }
}