"use client"
import { useEffect, useState } from "react"

export default function LiveTranscript() {
  const [lines, setLines] = useState<any[]>([])

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/transcript")

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setLines(prev => [...prev, data])
    }

    return () => ws.close()
  }, [])

  return (
    <div className="space-y-2 max-h-[400px] overflow-y-auto">
      {lines.map((l, i) => (
        <p key={i}>
          <b>{l.speaker}</b> ({l.language}): {l.text}
        </p>
      ))}
    </div>
  )
}