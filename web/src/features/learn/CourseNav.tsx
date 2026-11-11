import { useEffect, useRef } from 'react'
import { Link } from 'react-router'
import { lessonKey, lessonPath, type Stage } from './course'
import { Search } from './Search'

function isFinished(stage: Stage, done: string[]) {
  return stage.lessons.length > 0 && stage.lessons.every((lesson) => done.includes(lessonKey(lesson)))
}

function Dot({ index, active, finished }: { index: number; active: boolean; finished: boolean }) {
  const colours = active
    ? 'border-cobalt bg-cobalt text-on-cobalt'
    : finished
      ? 'border-guard bg-paper text-guard'
      : 'border-field bg-paper text-muted'
  return (
    <span
      aria-hidden="true"
      className={`relative z-10 flex size-7 shrink-0 items-center justify-center rounded-full border text-xs font-medium ${colours}`}
    >
      {finished ? '✓' : index}
    </span>
  )
}

function Lessons({ stage, current, done }: { stage: Stage; current?: string; done: string[] }) {
  return (
    <ol className="mt-1 mb-2 ml-9 space-y-0.5">
      {stage.lessons.map((lesson) => {
        const active = lesson.id === current
        const finished = done.includes(lessonKey(lesson))
        return (
          <li key={lesson.id}>
            <Link
              to={lessonPath(lesson)}
              aria-current={active ? 'page' : undefined}
              className={`flex min-h-11 items-center gap-2 rounded px-2 py-1 text-sm ${
                active ? 'bg-shelf font-medium text-cobalt' : 'hover:bg-shelf'
              }`}
            >
              <span>
                {lesson.title}
                {finished && <span className="sr-only"> (done)</span>}
              </span>
              {finished && (
                <span aria-hidden="true" className="ml-auto text-guard">
                  ✓
                </span>
              )}
            </Link>
          </li>
        )
      })}
    </ol>
  )
}

function Stages({
  course,
  stageId,
  lessonId,
  done,
}: {
  course: Stage[]
  stageId?: string
  lessonId?: string
  done: string[]
}) {
  const current = useRef<HTMLLIElement>(null)

  useEffect(() => {
    if (stageId) current.current?.scrollIntoView({ block: 'nearest' })
  }, [stageId])

  return (
    <ol>
      {course.map((stage, index) => {
        const active = stage.id === stageId
        const finished = isFinished(stage, done)
        const first = stage.lessons[0]
        const row = (
          <>
            <Dot index={index} active={active} finished={finished} />
            <span>
              <span className="sr-only">Stage {index}: </span>
              {stage.title}
              {finished && <span className="sr-only">, finished</span>}
              {!first && <span className="block text-xs text-muted">Coming soon</span>}
            </span>
          </>
        )
        const last = index === course.length - 1
        return (
          <li
            key={stage.id}
            ref={active ? current : undefined}
            aria-current={active ? 'step' : undefined}
            className="relative"
          >
            {!last && <span aria-hidden="true" className="absolute top-3 bottom-0 left-[1.3125rem] w-px bg-rule" />}
            {first ? (
              <Link
                to={lessonPath(first)}
                className={`flex min-h-11 items-center gap-2 rounded px-2 py-1 text-sm ${
                  active ? 'font-semibold text-cobalt' : 'hover:text-cobalt'
                }`}
              >
                {row}
              </Link>
            ) : (
              <div className="flex min-h-11 items-center gap-2 px-2 py-1 text-sm text-muted">{row}</div>
            )}
            {active && <Lessons stage={stage} current={lessonId} done={done} />}
          </li>
        )
      })}
    </ol>
  )
}

type Props = { course: Stage[]; stageId?: string; lessonId?: string; done: string[] }

/** On a wide screen, a sticky rail beside the page. */
export function CourseRail({ course, stageId, lessonId, done }: Props) {
  return (
    <aside className="hidden lg:block">
      <div className="glass-tile sticky top-24 max-h-[calc(100dvh-8rem)] overflow-y-auto p-3">
        <Search course={course} label="Search the course" compact />
        <nav aria-label="Course stages" className="mt-4">
          <Stages course={course} stageId={stageId} lessonId={lessonId} done={done} />
        </nav>
      </div>
    </aside>
  )
}

/** On a phone there's no room beside the page, so the same list opens above it. */
export function CourseMenu({ course, stageId, lessonId, done }: Props) {
  const index = course.findIndex((stage) => stage.id === stageId)
  const stage = course[index]
  return (
    <details className="glass-tile lg:hidden">
      <summary className="min-h-11 cursor-pointer px-3 py-2.5 font-medium">
        {stage ? `Stage ${index} of ${course.length - 1}: ${stage.title}` : 'Course menu'}
      </summary>
      <div className="px-1 pb-2">
        <div className="px-2 pb-2">
          <Search course={course} label="Search the course" compact />
        </div>
        <nav aria-label="Course stages">
          <Stages course={course} stageId={stageId} lessonId={lessonId} done={done} />
        </nav>
      </div>
    </details>
  )
}
