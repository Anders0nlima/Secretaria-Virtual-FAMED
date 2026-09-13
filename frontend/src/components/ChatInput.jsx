import { useState } from 'react'
import './ChatInput.css'

/**
 * Campo de input do chat.
 *
 * Props:
 *  - onSend: (message: string) => void
 *  - disabled: boolean
 */
export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e)
    }
  }

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <textarea
        className="chat-input-textarea"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Digite sua pergunta..."
        disabled={disabled}
        rows={1}
        aria-label="Digite sua pergunta"
      />
      <button
        type="submit"
        className="chat-input-btn"
        disabled={disabled || !value.trim()}
        aria-label="Enviar mensagem"
      >
        {/* Ícone de enviar */}
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
        </svg>
      </button>
    </form>
  )
}
