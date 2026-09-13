import './MessageBubble.css'

export default function MessageBubble({ role, content, sources }) {
  if (!sources) sources = []
  return (
    <div className={"bubble-wrapper bubble-wrapper--" + role}>
      <div className={"bubble bubble--" + role}>
        <p>{content}</p>
        {sources.length > 0 && (
          <div className="bubble-sources">
            <span className="bubble-sources-label">Fonte:</span>
            <ul>
              {sources.map(function(src, i) { return <li key={i}>{src}</li> })}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}