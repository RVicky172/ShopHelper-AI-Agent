import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'

const WORDS_PER_MINUTE = 200
const LEARN = resolve(dirname(fileURLToPath(import.meta.url)), '../docs/learn')
const VIRTUAL = 'virtual:course'
const RESOLVED = `\0${VIRTUAL}`

type CourseFile = { stages: { id: string; title: string; short: string; lessons: string[] }[] }

function header(text: string): Record<string, string> {
  const match = /^---\r?\n([\s\S]*?)\r?\n---/.exec(text)
  if (!match) return {}
  return Object.fromEntries(
    match[1].split(/\r?\n/).map((line) => {
      const at = line.indexOf(':')
      return [line.slice(0, at).trim(), line.slice(at + 1).trim()]
    }),
  )
}

function withoutCode(text: string): string {
  return text.replace(/^```[\s\S]*?^```/gm, '')
}

function lessonIndex(stage: string, id: string) {
  const text = readFileSync(resolve(LEARN, stage, `${id}.md`), 'utf-8')
  const front = header(text)
  const prose = withoutCode(text)
  return {
    stage,
    id,
    title: front.title ?? id,
    minutes: Math.max(1, Math.round(prose.split(/\s+/).filter(Boolean).length / WORDS_PER_MINUTE)),
    headings: [...prose.matchAll(/^#{2,3} (.+)$/gm)].map((m) => m[1].trim()),
    checked: front.checked ?? '',
  }
}

// Titles and headings only, so the stepper and search never download 81 lessons to draw a menu.
export function learnPlugin(): Plugin {
  return {
    name: 'shophelper-course',
    resolveId: (id) => (id === VIRTUAL ? RESOLVED : undefined),
    load(id) {
      if (id !== RESOLVED) return undefined
      const file = resolve(LEARN, 'course.json')
      this.addWatchFile(file)
      const course = JSON.parse(readFileSync(file, 'utf-8')) as CourseFile
      const stages = course.stages.map((stage) => ({
        ...stage,
        lessons: stage.lessons.map((lesson) => {
          this.addWatchFile(resolve(LEARN, stage.id, `${lesson}.md`))
          return lessonIndex(stage.id, lesson)
        }),
      }))
      return `export const course = ${JSON.stringify(stages)}`
    },
  }
}
