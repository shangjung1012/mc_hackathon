import { ref } from 'vue'

export function apiTTS() {
  const audioUrl = ref<string>('') // 儲存後端回傳的 audio_url
  const audioRef = ref<HTMLAudioElement | null>(null)

  // 播放後端回傳的音檔
  function playAudioFromBackend(url: string) {
    audioUrl.value = url
    // 若已經有 audio 標籤，則直接播放
    if (audioRef.value) {
      audioRef.value.pause()
      audioRef.value.currentTime = 0
      audioRef.value.src = url
      audioRef.value.play()
    } else {
      // 若沒有 audio 標籤，則用 new Audio 動態播放
      const audio = new Audio(url)
      audio.play()
    }
  }

  return {
    audioUrl,
    audioRef,
    playAudioFromBackend,
  }
}