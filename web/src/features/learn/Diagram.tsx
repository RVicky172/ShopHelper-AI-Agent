import mermaid from 'mermaid'
import { useEffect, useId, useState } from 'react'

export function Diagram({ source }: { source: string }) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, '')
  const [svg, setSvg] = useState('')
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let current = true
    const dark = matchMedia('(prefers-color-scheme: dark)').matches
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: dark ? 'dark' : 'neutral' })
    mermaid
      .render(`diagram-${id}`, source)
      .then((result) => {
        if (current) setSvg(result.svg)
      })
      .catch(() => {
        if (current) setFailed(true)
      })
    return () => {
      current = false
    }
  }, [id, source])

  if (failed) return <pre>{source}</pre>
  if (!svg) return <div className="diagram-space" />
  // Mermaid's strict mode cleans this SVG, and its source is a lesson in this repository.
  return <div className="diagram" role="img" aria-label="Diagram" dangerouslySetInnerHTML={{ __html: svg }} />
}
