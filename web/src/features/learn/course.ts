export type Lesson = {
  stage: string
  id: string
  title: string
  minutes: number
  headings: string[]
  checked: string
}

export type Stage = { id: string; title: string; short: string; lessons: Lesson[] }

export const lessonKey = (lesson: Pick<Lesson, 'stage' | 'id'>) => `${lesson.stage}/${lesson.id}`
export const lessonPath = (lesson: Pick<Lesson, 'stage' | 'id'>) => `/learn/${lesson.stage}/${lesson.id}`

export function allLessons(course: Stage[]): Lesson[] {
  return course.flatMap((stage) => stage.lessons)
}

/** The lessons either side of this one, carrying on across stages. */
export function neighbours(course: Stage[], stage: string, id: string) {
  const lessons = allLessons(course)
  const at = lessons.findIndex((lesson) => lesson.stage === stage && lesson.id === id)
  return { previous: lessons[at - 1], next: at === -1 ? undefined : lessons[at + 1] }
}
