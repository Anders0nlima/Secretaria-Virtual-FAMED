import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble.jsx'
import ChatInput from './ChatInput.jsx'
import famedLogo from '../assets/logo_Famed.png'
import './ChatWindow.css'

const API_URL = `http://${window.location.hostname}:8000/chat`

const WELCOME_MESSAGE = {
  role: 'assistant',
  content:
    'Olá! Sou a Secretaria Virtual da FAMED/UFPA. Posso ajudar com dúvidas sobre o Calendário Acadêmico 2026, normas da faculdade, resoluções, TCC, formulários e agendamentos institucionais. Como posso ajudar você hoje?',
  sources: [],
}

export default function ChatWindow({ onClose }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (userMessage) => {
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: userMessage, sources: [] },
    ])
    setIsLoading(true)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      })

      if (!response.ok) {
        throw new Error('Erro na requisicao: ' + response.status)
      }

      const data = await response.json()
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.answer, sources: data.sources ?? [] },
      ])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, verifique se o servidor local está ativo e tente novamente.',
          sources: [],
        },
      ])
      console.error('[ChatWindow] Erro ao chamar API:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-window" role="dialog" aria-label="Secretaria Virtual FAMED/UFPA">
      <div className="chat-window-header">
        {/* Botão de retorno visível em smartphones */}
        <button
          className="chat-window-back-btn"
          onClick={onClose}
          aria-label="Voltar para o site da FAMED"
          title="Voltar ao portal da FAMED"
        >
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          <span className="chat-window-back-text">Voltar</span>
        </button>

        <div className="chat-window-header-info">
          <div className="chat-window-badge-icon" aria-hidden="true">
            <img src={famedLogo} alt="Logo FAMED" className="chat-window-badge-logo" />
          </div>
          <div>
            <p className="chat-window-title">Secretaria Virtual</p>
            <p className="chat-window-subtitle">FACULDADE DE MEDICINA · UFPA</p>
          </div>
        </div>

        {/* Botão fechar (X) */}
        <button
          className="chat-window-close"
          onClick={onClose}
          aria-label="Fechar chat"
          title="Fechar"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="chat-window-messages">
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            role={msg.role}
            content={msg.content}
            sources={msg.sources}
            showFeedback={msg.role === 'assistant' && i > 0}
            question={i > 0 && messages[i - 1]?.role === 'user' ? messages[i - 1].content : null}
          />
        ))}

        {isLoading && (
          <div className="bubble-wrapper bubble-wrapper--assistant">
            <div className="bubble bubble--assistant typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={isLoading} />

      <p className="chat-window-disclaimer">
        Respostas geradas com auxílio de IA com base na documentação oficial da FAMED/UFPA.
      </p>
    </div>
  )
}
