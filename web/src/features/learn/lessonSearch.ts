import { allLessons, type Lesson, type Stage } from './course'

const MAX_RESULTS = 8

export function searchLessons(course: Stage[], query: string): Lesson[] {
  const term = query.trim().toLowerCase()
  if (!term) return []
  const byTitle: Lesson[] = []
  const byHeading: Lesson[] = []
  for (const lesson of allLessons(course)) {
    if (lesson.title.toLowerCase().includes(term)) byTitle.push(lesson)
    else if (lesson.headings.some((heading) => heading.toLowerCase().includes(term))) byHeading.push(lesson)
  }
  return [...byTitle, ...byHeading].slice(0, MAX_RESULTS)
}
