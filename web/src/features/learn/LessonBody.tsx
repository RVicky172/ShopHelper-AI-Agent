import { lazy, type ReactNode, Suspense, useEffect, useState } from 'react'
import { CheckYourself } from './CheckYourself'
import type { Lesson } from './course'
import { Text } from './LessonText'
import { checkQuestions, firstScreen, interviewQuestions, type ParsedLesson, parseLesson } from './lessons'

// Lessons come one at a time, and the question bank comes only with its own lesson.
const files = import.meta.glob('../../../../docs/learn/*/*.md', { query: '?raw', import: 'default' })
const QuestionBank = lazy(() => import('./QuestionBank').then((m) => ({ default: m.QuestionBank })))

function Interview({ stage, body }: { stage: string; body: string }) {
  return (
    <div className="mt-3 space-y-2">
      {interviewQuestions(body).map((item) => (
        <details key={item.question} className="rounded-inner border border-edge px-4 py-2">
          <summary className="min-h-11 cursor-pointer py-2 font-medium">{item.question}</summary>
          <div className="pb-2">
            <p className="text-sm font-medium text-muted">A strong answer</p>
            <Text stage={stage}>{item.answer}</Text>
            <p className="mt-3 text-sm font-medium text-muted">Likely follow-up</p>
            <Text stage={stage}>{item.followUp}</Text>
          </div>
        </details>
      ))}
    </div>
  )
}

function Part({ stage, title, body }: { stage: string; title: string; body: string }): ReactNode {
  const heading = <h2>{title}</h2>
  if (title === 'Interview questions') {
    return (
      <section>
        {heading}
        <Interview stage={stage} body={body} />
      </section>
    )
  }
  if (title === 'All the questions') {
    return (
      <section>
        {heading}
        <Text stage={stage}>{body}</Text>
        <Suspense fallback={<div className="min-h-96" aria-hidden="true" />}>
          <QuestionBank />
        </Suspense>
      </section>
    )
  }
  if (title === 'Check yourself') {
    return (
      <section>
        {heading}
        <CheckYourself questions={checkQuestions(body)} />
      </section>
    )
  }
  return (
    <section>
      {heading}
      <Text stage={stage}>{body}</Text>
    </section>
  )
}

export function LessonBody({ lesson }: { lesson: Lesson }) {
  const [parsed, setParsed] = useState<ParsedLesson | null>(null)
  const [whole, setWhole] = useState<ParsedLesson | null>(null)

  useEffect(() => {
    let current = true
    const load = files[`../../../../docs/learn/${lesson.stage}/${lesson.id}.md`]
    load?.().then((text) => {
      if (current) setParsed(parseLesson(text as string))
    })
    return () => {
      current = false
    }
  }, [lesson.stage, lesson.id])

  // On a slow phone, turning a whole lesson into a page held back its first words by about 0.3 s. Only the
  // top fits on screen, so the rest follows a frame after the first paint, below the fold where nothing moves.
  // Show a whole screen first, or the second paint lands in view and becomes the page's largest paint.
  useEffect(() => {
    if (!parsed || whole === parsed) return
    let timer = 0
    const frame = requestAnimationFrame(() => {
      timer = window.setTimeout(() => setWhole(parsed))
    })
    return () => {
      cancelAnimationFrame(frame)
      clearTimeout(timer)
    }
  }, [parsed, whole])

  if (!parsed) return <div className="mt-6 min-h-dvh" aria-hidden="true" />
  const sections = whole === parsed ? parsed.sections : parsed.sections.slice(0, firstScreen(parsed))
  return (
    <div className={`lesson mt-4 ${whole === parsed ? '' : 'min-h-dvh'}`}>
      {parsed.intro.trim() && <Text stage={lesson.stage}>{parsed.intro}</Text>}
      {sections.map((section) => (
        <Part key={section.title} stage={lesson.stage} title={section.title} body={section.body} />
      ))}
    </div>
  )
}
