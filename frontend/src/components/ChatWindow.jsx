import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble.jsx'
import ChatInput from './ChatInput.jsx'
import './ChatWindow.css'

const API_URL = 'http://localhost:8000/chat'

const WELCOME_MESSAGE = {
  role: 'assistant',
  content:
    'Ola! Sou a Secretaria Virtual da FAMED/UFPA. Posso responder perguntas sobre o Calendario Academico 2026. Como posso ajudar?',
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
            'Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente mais tarde.',
          sources: [],
        },
      ])
      console.error('[ChatWindow] Erro ao chamar API:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-window" role="dialog" aria-label="Secretaria Virtual FAMED">
      <div className="chat-window-header">
        <div className="chat-window-header-info">
          <span className="chat-window-avatar">&#127891;</span>
          <div>
            <p className="chat-window-title">Secretaria Virtual</p>
            <p className="chat-window-subtitle">FAMED/UFPA</p>
          </div>
        </div>
        <button
          className="chat-window-close"
          onClick={onClose}
          aria-label="Fechar chat"
        >
          &#x2715;
        </button>
      </div>

      <div className="chat-window-messages">
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            role={msg.role}
            content={msg.content}
            sources={msg.sources}
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
    </div>
  )
}