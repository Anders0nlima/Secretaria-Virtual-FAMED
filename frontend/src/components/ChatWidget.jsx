import { useState } from 'react'
import ChatWindow from './ChatWindow.jsx'
import './ChatWidget.css'

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="chat-widget">
      {/* Janela de chat — visível quando isOpen === true */}
      {isOpen && <ChatWindow onClose={() => setIsOpen(false)} />}

      {/* Botão flutuante */}
      <button
        className="chat-toggle-btn"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? 'Fechar Secretaria Virtual' : 'Abrir Secretaria Virtual'}
        title="Secretaria Virtual FAMED"
      >
        {isOpen ? (
          /* Ícone "X" quando aberto */
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>
        ) : (
          /* Ícone de chat quando fechado */
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
        )}
      </button>
    </div>
  )
}
