import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'
import { questionsIn } from './src/features/learn/bankQuestions'

const WORDS_PER_MINUTE = 200
const LEARN = resolve(dirname(fileURLToPath(import.meta.url)), '../docs/learn')
const VIRTUAL = 'virtual:course'
const RESOLVED = `\0${VIRTUAL}`
const VIRTUAL_QUESTIONS = 'virtual:course-questions'
const RESOLVED_QUESTIONS = `\0${VIRTUAL_QUESTIONS}`

type Chunk = {
  type: string
  name?: string
  isEntry?: boolean
  imports?: string[]
  viteMetadata?: { importedCss?: Set<string> }
  facadeModuleId?: string | null
}

/** The course's files that the entry doesn't already load. */
export function courseFiles(bundle: Record<string, unknown>): string[] {
  const chunks = bundle as Record<string, Chunk>
  const learn = Object.keys(chunks).find((file) => chunks[file].type === 'chunk' && chunks[file].name === 'Learn')
  if (!learn) return []

  const walk = (file: string, seen: Set<string>) => {
    if (seen.has(file) || !chunks[file]) return seen
    seen.add(file)
    for (const next of chunks[file].imports ?? []) walk(next, seen)
    return seen
  }
  const loaded = new Set<string>()
  for (const file of Object.keys(chunks)) if (chunks[file].isEntry) walk(file, loaded)

  const needed = [...walk(learn, new Set())].filter((file) => !loaded.has(file))
  const css = needed.flatMap((file) => [...(chunks[file].viteMetadata?.importedCss ?? [])])
  return [...needed, ...css].map((file) => `/${file}`)
}

/** Each lesson's own file, by its path under /learn. */
export function lessonFiles(bundle: Record<string, unknown>): Record<string, string> {
  const chunks = bundle as Record<string, Chunk>
  const found = Object.keys(chunks).flatMap((file) => {
    const lesson = /docs\/learn\/([^/]+\/[^/]+)\.md/.exec(chunks[file].facadeModuleId ?? '')?.[1]
    return lesson ? [[lesson, `/${file}`]] : []
  })
  return Object.fromEntries(found)
}

// A lazy route's code is only found once the main bundle has run. On a slow phone that wait was most of
// the time to the first words of a lesson, so course pages ask for it straight away. Vite loads them with
// crossorigin, and a preload without it doesn't match, so the browser fetched the stylesheet twice.
export function preloadScript(files: string[], lessons: Record<string, string>): string {
  return `<script>if(location.pathname.startsWith('/learn')){const m=${JSON.stringify(lessons)}[location.pathname.slice(7)];for(const f of ${JSON.stringify(files)}.concat(m||[])){const l=document.createElement('link');const c=f.endsWith('.css');l.rel=c?'preload':'modulepreload';if(c)l.as='style';l.crossOrigin='';l.href=f;document.head.append(l)}}</script>`
}

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
// The questions are a separate module, so only the question bank's lesson downloads them.
export function learnPlugin(): Plugin {
  return {
    name: 'shophelper-course',
    transformIndexHtml: {
      order: 'post',
      handler(html, context) {
        const files = context.bundle ? courseFiles(context.bundle) : []
        if (!context.bundle || !files.length) return html
        return html.replace('</title>', `</title>${preloadScript(files, lessonFiles(context.bundle))}`)
      },
    },
    resolveId(id) {
      if (id === VIRTUAL) return RESOLVED
      return id === VIRTUAL_QUESTIONS ? RESOLVED_QUESTIONS : undefined
    },
    load(id) {
      if (id !== RESOLVED && id !== RESOLVED_QUESTIONS) return undefined
      const file = resolve(LEARN, 'course.json')
      this.addWatchFile(file)
      const course = JSON.parse(readFileSync(file, 'utf-8')) as CourseFile
      if (id === RESOLVED_QUESTIONS) {
        const questions = course.stages.flatMap((stage) =>
          stage.lessons.flatMap((lesson) => {
            const path = resolve(LEARN, stage.id, `${lesson}.md`)
            this.addWatchFile(path)
            const raw = readFileSync(path, 'utf-8')
            const lessonTitle = header(raw).title ?? lesson
            return questionsIn(raw, { stage: stage.id, stageTitle: stage.title, lesson, lessonTitle })
          }),
        )
        return `export const questions = ${JSON.stringify(questions)}`
      }
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
