import { course } from 'virtual:course'
import { useCallback, useEffect, useState } from 'react'
import { Link, Route, Routes, useParams } from 'react-router'
import { NotFound } from '../../shared/layout/NotFound'
import { CourseMenu, CourseRail } from './CourseNav'
import { allLessons, lessonKey, lessonPath, neighbours, type Stage } from './course'
import './learn.css'
import { LessonBody } from './LessonBody'
import { loadProgress, type Progress, saveProgress, toggleDone } from './progress'
import { Search } from './Search'

const SEARCH_LABEL = 'Search the course'
const PAGE = 'mx-auto grid w-full max-w-page gap-10 px-gutter py-6 lg:grid-cols-[minmax(0,1fr)_17rem]'

function useProgress() {
  const [progress, setProgress] = useState<Progress>(loadProgress)
  const update = useCallback((change: (current: Progress) => Progress) => {
    setProgress((current) => {
      const next = change(current)
      saveProgress(next)
      return next
    })
  }, [])
  return [progress, update] as const
}

function stageDone(stage: Stage, done: string[]) {
  return stage.lessons.filter((lesson) => done.includes(lessonKey(lesson))).length
}

function LearnHome({ progress }: { progress: Progress }) {
  const lessons = allLessons(course)
  const last = lessons.find((lesson) => lessonKey(lesson) === progress.last)
  const start = last ?? lessons[0]
  return (
    <div className={PAGE}>
      <title>Learn AI engineering · ShopHelper</title>
      <div className="min-w-0">
        <CourseMenu course={course} done={progress.done} />
        <h1 className="mt-4 text-title font-semibold lg:mt-0">Learn AI engineering</h1>
        <p className="mt-2 max-w-2xl text-muted">
          One path from how a language model works to passing an AI engineer interview, using this shop's real code. Go
          in order, about 10 minutes a lesson.
        </p>
        <div className="mt-5 flex flex-wrap items-center gap-4">
          {start && (
            <Link
              to={lessonPath(start)}
              className="inline-flex min-h-11 items-center rounded-xl bg-cobalt px-4 font-medium text-on-cobalt"
            >
              {last ? `Continue: ${last.title}` : 'Start the course'}
            </Link>
          )}
          <p className="text-sm text-muted">
            {progress.done.length} of {lessons.length} lessons done
          </p>
        </div>
        <div className="mt-6 max-w-md lg:hidden">
          <Search course={course} label={SEARCH_LABEL} />
        </div>
        <ol className="mt-8 grid gap-3 md:grid-cols-2">
          {course.map((stage, index) => {
            const first = stage.lessons[0]
            const label = (
              <>
                <span className="block text-sm text-muted">Stage {index}</span>
                <span className="block font-medium">{stage.title}</span>
                <span className="mt-1 block text-sm text-muted">
                  {stage.lessons.length === 0
                    ? 'Coming soon'
                    : `${stageDone(stage, progress.done)} of ${stage.lessons.length} done`}
                </span>
              </>
            )
            return (
              <li key={stage.id}>
                {first ? (
                  <Link to={lessonPath(first)} className="glass-tile card-lift block h-full p-4 hover:border-cobalt">
                    {label}
                  </Link>
                ) : (
                  <div className="glass-tile h-full p-4 opacity-80">{label}</div>
                )}
              </li>
            )
          })}
        </ol>
      </div>
      <CourseRail course={course} done={progress.done} />
    </div>
  )
}

function LessonPage({
  progress,
  update,
}: {
  progress: Progress
  update: (change: (current: Progress) => Progress) => void
}) {
  const { stage: stageId = '', lesson: lessonId = '' } = useParams()
  const stage = course.find((item) => item.id === stageId)
  const lesson = stage?.lessons.find((item) => item.id === lessonId)
  const key = lesson ? lessonKey(lesson) : null

  useEffect(() => {
    if (key) update((current) => ({ ...current, last: key }))
  }, [key, update])

  if (!stage || !lesson || !key) return <NotFound title="We can't find that lesson" />
  const { previous, next } = neighbours(course, stage.id, lesson.id)
  const done = progress.done.includes(key)

  return (
    <div className={PAGE}>
      <title>{`${lesson.title} · Learn · ShopHelper`}</title>
      <article className="min-w-0">
        <CourseMenu course={course} stageId={stage.id} lessonId={lesson.id} done={progress.done} />
        <div className="surface-solid mt-4 p-5 lg:mt-0 lg:p-8">
          <p className="text-sm text-muted">{stage.title}</p>
          <h1 className="mt-1 text-title font-semibold">{lesson.title}</h1>
          <p className="mt-1 text-sm text-muted">{lesson.minutes} min read</p>
          <LessonBody key={key} lesson={lesson} />
          <div className="mt-10 border-t border-edge pt-5">
            <button
              type="button"
              aria-pressed={done}
              onClick={() => update((current) => toggleDone(current, key))}
              className={`min-h-11 rounded-xl border px-4 font-medium ${
                done ? 'border-guard text-guard' : 'border-cobalt bg-cobalt text-on-cobalt'
              }`}
            >
              {done ? 'Done ✓' : 'Mark as done'}
            </button>
          </div>
        </div>
        <nav aria-label="Lessons" className="mt-5 flex flex-wrap justify-between gap-4 pb-10">
          {previous ? (
            <Link to={lessonPath(previous)} className="flex min-h-11 items-center text-cobalt underline">
              ← {previous.title}
            </Link>
          ) : (
            <span />
          )}
          {next && (
            <Link to={lessonPath(next)} className="flex min-h-11 items-center text-cobalt underline">
              {next.title} →
            </Link>
          )}
        </nav>
      </article>
      <CourseRail course={course} stageId={stage.id} lessonId={lesson.id} done={progress.done} />
    </div>
  )
}

export function Learn() {
  const [progress, update] = useProgress()
  return (
    <div>
      <Routes>
        <Route index element={<LearnHome progress={progress} />} />
        <Route path=":stage/:lesson" element={<LessonPage progress={progress} update={update} />} />
        <Route path="*" element={<NotFound title="We can't find that lesson" />} />
      </Routes>
    </div>
  )
}
