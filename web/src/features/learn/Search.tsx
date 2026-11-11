import { useId, useState } from 'react'
import { Link } from 'react-router'
import { lessonPath, type Stage } from './course'
import { searchLessons } from './lessonSearch'

export function Search({ course, label, compact = false }: { course: Stage[]; label: string; compact?: boolean }) {
  const [query, setQuery] = useState('')
  const id = useId()
  const results = searchLessons(course, query)
  const searched = query.trim().length > 0

  return (
    <div>
      <label htmlFor={id} className={compact ? 'sr-only' : 'block text-sm font-medium'}>
        {label}
      </label>
      <input
        id={id}
        type="search"
        value={query}
        placeholder={compact ? 'Search' : 'Try "chunking" or "prompt injection"'}
        onChange={(event) => setQuery(event.target.value)}
        className="mt-1 min-h-11 w-full rounded-xl border border-field bg-paper px-3"
      />
      {searched && (
        <div role="status" className="mt-2">
          {results.length === 0 ? (
            <p className="text-sm text-muted">No lessons match that yet.</p>
          ) : (
            <ul className="surface-solid overflow-hidden">
              {results.map((lesson) => (
                <li key={`${lesson.stage}/${lesson.id}`}>
                  <Link
                    to={lessonPath(lesson)}
                    onClick={() => setQuery('')}
                    className="flex min-h-11 items-center px-3 py-1 text-sm hover:bg-shelf"
                  >
                    {lesson.title}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
