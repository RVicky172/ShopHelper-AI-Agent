import { describe, expect, it } from 'vitest'
import { searchLessons } from './lessonSearch'
import { checkQuestions, interviewQuestions, parseLesson } from './lessons'
import { toHref } from './links'
import { emptyProgress, markDone, parseProgress, toggleDone } from './progress'

const COURSE = [
  {
    id: '03-agents',
    title: 'Agents',
    short: 'Agents',
    lessons: [
      {
        stage: '03-agents',
        id: '02-the-loop',
        title: 'The agent loop',
        minutes: 8,
        headings: ['Why a loop', 'Stopping'],
        checked: '2026-11-06',
      },
    ],
  },
  {
    id: '05-rag',
    title: 'RAG',
    short: 'RAG',
    lessons: [
      {
        stage: '05-rag',
        id: '03-chunking',
        title: 'Chunking',
        minutes: 9,
        headings: ['Overlap'],
        checked: '2026-11-06',
      },
    ],
  },
]

describe('parseLesson', () => {
  const raw =
    '---\ntitle: Chunking\nchecked: 2026-11-06\n---\n\nIntro.\n\n## One\nFirst.\n\n## Two\n```\n## not a part\n```\n'

  it('reads the header and leaves it out of the body', () => {
    const lesson = parseLesson(raw)
    expect(lesson.front.title).toBe('Chunking')
    expect(lesson.intro.trim()).toBe('Intro.')
  })

  it('splits on level 2 headings, ignoring code', () => {
    const lesson = parseLesson(raw)
    expect(lesson.sections.map((s) => s.title)).toEqual(['One', 'Two'])
    expect(lesson.sections[1].body).toContain('## not a part')
  })

  it('copes with a lesson that has no header', () => {
    expect(parseLesson('## One\nFirst.').sections[0].title).toBe('One')
  })
})

describe('interviewQuestions', () => {
  it('reads each question, answer and follow-up', () => {
    const body =
      '### Why?\n**Strong answer:** Because.\nMore.\n**Follow-up:** And then?\n\n### How?\n**Strong answer:** So.\n**Follow-up:** Really?\n'
    expect(interviewQuestions(body)).toEqual([
      { question: 'Why?', answer: 'Because.\nMore.', followUp: 'And then?' },
      { question: 'How?', answer: 'So.', followUp: 'Really?' },
    ])
  })
})

describe('checkQuestions', () => {
  it('reads options, the right one and the feedback', () => {
    const body = '### Pick one?\n- [ ] Wrong — not this.\n- [x] Right — yes, this.\n'
    expect(checkQuestions(body)).toEqual([
      {
        question: 'Pick one?',
        options: [
          { text: 'Wrong', correct: false, feedback: 'not this.' },
          { text: 'Right', correct: true, feedback: 'yes, this.' },
        ],
      },
    ])
  })
})

describe('toHref', () => {
  it('turns a lesson link into a route', () => {
    expect(toHref('../05-rag/03-chunking.md', '03-agents')).toBe('/learn/05-rag/03-chunking')
    expect(toHref('02-the-loop.md', '03-agents')).toBe('/learn/03-agents/02-the-loop')
    expect(toHref('../05-rag/03-chunking.md#overlap', '03-agents')).toBe('/learn/05-rag/03-chunking#overlap')
  })

  it('sends a link to project files to the repository', () => {
    expect(toHref('../../../src/shophelper/agent/graph.py', '03-agents')).toBe(
      'https://github.com/RVicky172/ShopHelper-AI-Agent/blob/main/src/shophelper/agent/graph.py',
    )
  })

  it('leaves other links and page anchors alone', () => {
    expect(toHref('https://example.com', '03-agents')).toBe('https://example.com')
    expect(toHref('#overlap', '03-agents')).toBe('#overlap')
  })
})

describe('progress', () => {
  it('survives bad storage', () => {
    expect(parseProgress(null)).toEqual(emptyProgress)
    expect(parseProgress('not json')).toEqual(emptyProgress)
    expect(parseProgress('{"done":"nope"}')).toEqual(emptyProgress)
    expect(parseProgress('{"done":[1,"a/b"],"last":5}')).toEqual({ done: ['a/b'], last: null })
  })

  it('marks a lesson once, and can undo it', () => {
    const once = markDone(emptyProgress, 'a/b')
    expect(markDone(once, 'a/b').done).toEqual(['a/b'])
    expect(toggleDone(once, 'a/b').done).toEqual([])
  })
})

describe('searchLessons', () => {
  it('finds a title or a heading, ignoring case', () => {
    expect(searchLessons(COURSE, 'CHUNK').map((r) => r.id)).toEqual(['03-chunking'])
    expect(searchLessons(COURSE, 'stopping').map((r) => r.id)).toEqual(['02-the-loop'])
  })

  it('puts a title match first', () => {
    const course = [{ ...COURSE[0], lessons: [{ ...COURSE[0].lessons[0], headings: ['Chunking'] }] }, COURSE[1]]
    expect(searchLessons(course, 'chunking').map((r) => r.id)).toEqual(['03-chunking', '02-the-loop'])
  })

  it('finds nothing for a blank search', () => {
    expect(searchLessons(COURSE, '  ')).toEqual([])
  })
})
