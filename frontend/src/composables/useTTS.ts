import { ref } from 'vue'

export function useTTS() {
  const ttsReady = ref(false)
  const audioUrl = ref<string>('') // Store backend returned audio_url
  const audioRef = ref<HTMLAudioElement | null>(null)
  let selectedVoice: SpeechSynthesisVoice | null = null

  // Browser native TTS related functions
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

  // Backend API TTS related functions
  function playAudioFromBackend(url: string) {
    audioUrl.value = url
    // If audio element exists, play directly
    if (audioRef.value) {
      audioRef.value.pause()
      audioRef.value.currentTime = 0
      audioRef.value.src = url
      audioRef.value.load()
      audioRef.value.oncanplay = () => {
        audioRef.value?.play()
      }
    } else {
      // If no audio element, use new Audio for dynamic playback
      const audio = new Audio(url)
      audio.play()
    }
  }

  // Unified playback method: prefer backend TTS, fallback to browser native TTS
  function playText(text: string, preferBackend = true) {
    if (preferBackend && audioUrl.value) {
      // If backend audio URL exists, play it first
      playAudioFromBackend(audioUrl.value)
    } else {
      // Fallback to browser native TTS
      speakText(text)
    }
  }

  return {
    // State
    ttsReady,
    audioUrl,
    audioRef,
    // Browser native TTS methods
    pickZhVoice,
    ensureTtsUnlocked,
    speakText,
    // Backend API TTS methods
    playAudioFromBackend,
    // Unified playback method
    playText,
  }
}