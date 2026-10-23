import { useState, useRef, useEffect } from 'react'
import './ChatInput.css'

/**
 * Campo de input unificado: caixa de texto com auto-expansão, scroll interno
 * e botão de envio integrado no rodapé da própria caixa.
 *
 * Props:
 *  - onSend: (message: string) => void
 *  - disabled: boolean
 */
export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    // Reseta temporariamente a altura para mensurar o scrollHeight real do conteúdo
    textarea.style.height = 'auto'
    const scrollHeight = textarea.scrollHeight
    const maxHeight = 100 // Altura máxima proporcional à janela do chat (~4 linhas)

    if (scrollHeight > maxHeight) {
      textarea.style.height = `${maxHeight}px`
      textarea.style.overflowY = 'auto'
    } else {
      textarea.style.height = `${Math.max(scrollHeight, 24)}px`
      textarea.style.overflowY = 'hidden'
    }
  }, [value])

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e) => {
    // Envia com Enter (sem Shift) e pula linha com Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className={`chat-input-container ${disabled ? 'chat-input-container--disabled' : ''}`}>
        <textarea
          ref={textareaRef}
          className="chat-input-textarea"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digite sua pergunta..."
          disabled={disabled}
          rows={1}
          aria-label="Digite sua pergunta"
        />
        <div className="chat-input-footer">
          <button
            type="submit"
            className="chat-input-btn"
            disabled={disabled || !value.trim()}
            title="Enviar mensagem"
            aria-label="Enviar mensagem"
          >
            {/* Ícone de envio */}
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    </form>
  )
}
