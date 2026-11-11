import { questions } from 'virtual:course-questions'
import { useId, useState } from 'react'
import { Link } from 'react-router'
import { type BankQuestion, filterQuestions } from './bankQuestions'
import { lessonPath } from './course'
import { Text } from './LessonText'

const stages = [...new Map(questions.map((item) => [item.stage, item.stageTitle])).entries()]

function Question({ item }: { item: BankQuestion }) {
  // Hundreds of answers are Markdown, so each one renders only when it's first opened.
  const [opened, setOpened] = useState(false)
  return (
    <details
      className="rounded border border-rule px-4 py-2"
      onToggle={(event) => {
        if (event.currentTarget.open) setOpened(true)
      }}
    >
      <summary className="min-h-11 cursor-pointer py-2 font-medium">{item.question}</summary>
      {opened && (
        <div className="pb-2">
          <p className="text-sm font-medium text-muted">A strong answer</p>
          <Text stage={item.stage}>{item.answer}</Text>
          <p className="mt-3 text-sm font-medium text-muted">Likely follow-up</p>
          <Text stage={item.stage}>{item.followUp}</Text>
          <p className="mt-3 text-sm">
            From{' '}
            <Link to={lessonPath({ stage: item.stage, id: item.lesson })}>
              {item.stageTitle}: {item.lessonTitle}
            </Link>
          </p>
        </div>
      )}
    </details>
  )
}

export function QuestionBank() {
  const [stage, setStage] = useState('')
  const [query, setQuery] = useState('')
  const stageId = useId()
  const queryId = useId()
  const shown = filterQuestions(questions, stage, query)

  return (
    <div className="mt-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor={stageId} className="block text-sm font-medium">
            Stage
          </label>
          <select
            id={stageId}
            value={stage}
            onChange={(event) => setStage(event.target.value)}
            className="mt-1 min-h-11 w-full rounded border border-field bg-paper px-3"
          >
            <option value="">All stages</option>
            {stages.map(([id, title]) => (
              <option key={id} value={id}>
                {title}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor={queryId} className="block text-sm font-medium">
            Find a question
          </label>
          <input
            id={queryId}
            type="search"
            value={query}
            placeholder='Try "refund" or "latency"'
            onChange={(event) => setQuery(event.target.value)}
            className="mt-1 min-h-11 w-full rounded border border-field bg-paper px-3"
          />
        </div>
      </div>
      <p role="status" className="mt-3 text-sm text-muted">
        Showing {shown.length} of {questions.length} questions.
      </p>
      <div className="mt-2 space-y-2">
        {shown.map((item) => (
          <Question key={`${item.stage}/${item.lesson}/${item.question}`} item={item} />
        ))}
      </div>
    </div>
  )
}
