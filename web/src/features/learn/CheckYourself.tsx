import { useState } from 'react'
import type { CheckQuestion } from './lessons'

function Question({ item }: { item: CheckQuestion }) {
  const [picked, setPicked] = useState<number | null>(null)
  const answer = picked === null ? null : item.options[picked]

  return (
    <fieldset className="rounded-inner border border-edge p-4">
      <legend className="px-1 font-medium">{item.question}</legend>
      <div className="space-y-1">
        {item.options.map((option, index) => (
          <label
            key={option.text}
            className="flex min-h-11 cursor-pointer items-center gap-3 rounded px-2 hover:bg-shelf"
          >
            <input
              type="radio"
              name={item.question}
              checked={picked === index}
              onChange={() => setPicked(index)}
              className="size-5 shrink-0"
            />
            <span>{option.text}</span>
          </label>
        ))}
      </div>
      <p role="status" className="mt-2 min-h-6 text-sm">
        {answer && (
          <>
            <span className={`font-medium ${answer.correct ? 'text-guard' : 'text-danger'}`}>
              {answer.correct ? 'Right. ' : 'Not quite. '}
            </span>
            {answer.feedback}
          </>
        )}
      </p>
    </fieldset>
  )
}

export function CheckYourself({ questions }: { questions: CheckQuestion[] }) {
  return (
    <div className="mt-3 space-y-3">
      {questions.map((item) => (
        <Question key={item.question} item={item} />
      ))}
    </div>
  )
}
