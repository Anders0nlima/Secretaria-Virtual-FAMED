import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './MessageBubble.css'

const FEEDBACK_URL = `http://${window.location.hostname}:8000/feedback`

/**
 * Normaliza o texto markdown para garantir que listas com hífen ou números
 * que tenham vindo em linha única recebam quebras de linha limpas.
 */
function formatMarkdownContent(text) {
  if (!text) return ''
  // Converte listas com traço em linha única (' - Item') para linhas separadas ('\n- Item')
  let formatted = text.replace(/([^\n])\s+-\s+([A-Z0-9À-Ú])/g, '$1\n- $2')
  // Converte passos numerados em linha única (' 1. Passo') para linhas separadas ('\n1. Passo')
  formatted = formatted.replace(/([^\n])\s+(\d+\.\s+)/g, '$1\n$2')
  return formatted
}

export default function MessageBubble({
  role,
  content,
  sources,
  showFeedback = false,
  question = null,
}) {
  const [feedbackSent, setFeedbackSent] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleFeedback = async (isHelpful) => {
    if (feedbackSent !== null || isSubmitting) return
    setIsSubmitting(true)
    const choice = isHelpful ? 'sim' : 'nao'
    setFeedbackSent(choice)

    try {
      await fetch(FEEDBACK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          helpful: isHelpful,
          question: question,
          answer: content,
        }),
      })
    } catch (err) {
      console.warn('[MessageBubble] Falha ao enviar feedback:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const safeSources = sources || []

  return (
    <div className={`bubble-wrapper bubble-wrapper--${role}`}>
      <div className={`bubble bubble--${role}`}>
        {role === 'assistant' ? (
          <div className="bubble-markdown">
            <ReactMarkdown>{formatMarkdownContent(content)}</ReactMarkdown>
          </div>
        ) : (
          <p className="bubble-text-user">{content}</p>
        )}

        {safeSources.length > 0 && (
          <div className="bubble-sources">
            <span className="bubble-sources-label">Fonte:</span>
            <ul>
              {safeSources.map((src, i) => (
                <li key={i}>{src}</li>
              ))}
            </ul>
          </div>
        )}

        {showFeedback && (
          <div className="bubble-feedback" role="group" aria-label="Avaliação da resposta">
            {feedbackSent === null ? (
              <>
                <span className="bubble-feedback-label">Essa resposta ajudou?</span>
                <div className="bubble-feedback-actions">
                  <button
                    type="button"
                    className="bubble-feedback-btn bubble-feedback-btn--yes"
                    onClick={() => handleFeedback(true)}
                    disabled={isSubmitting}
                    title="Sim, essa resposta ajudou"
                    aria-label="Sim, essa resposta ajudou"
                  >
                    {/* Ícone de positivo (Thumbs Up) */}
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
                    </svg>
                    <span>Sim</span>
                  </button>
                  <button
                    type="button"
                    className="bubble-feedback-btn bubble-feedback-btn--no"
                    onClick={() => handleFeedback(false)}
                    disabled={isSubmitting}
                    title="Não, essa resposta não ajudou"
                    aria-label="Não, essa resposta não ajudou"
                  >
                    {/* Ícone de negativo (Thumbs Down) */}
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"/>
                    </svg>
                    <span>Não</span>
                  </button>
                </div>
              </>
            ) : (
              <span className="bubble-feedback-thanks">
                Obrigado pelo seu feedback!
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
