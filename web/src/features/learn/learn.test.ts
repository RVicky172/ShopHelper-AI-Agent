import { describe, expect, it } from 'vitest'
import { courseFiles, lessonFiles, preloadScript } from '../../../learn-plugin'
import { filterQuestions, questionsIn } from './bankQuestions'
import { searchLessons } from './lessonSearch'
import { checkQuestions, firstScreen, interviewQuestions, parseLesson } from './lessons'
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

describe('firstScreen', () => {
  const lesson = (intro: number, ...bodies: number[]) => ({
    front: {},
    intro: 'i'.repeat(intro),
    sections: bodies.map((n, at) => ({ title: `S${at}`, body: 'b'.repeat(n) })),
  })

  it('keeps adding sections until a screen of text is above the next one', () => {
    expect(firstScreen(lesson(0, 250, 600, 5000, 100))).toBe(3)
  })

  it('always shows the first section, however long the intro', () => {
    expect(firstScreen(lesson(2000, 50, 50))).toBe(1)
  })

  it('copes with a lesson with no sections', () => {
    expect(firstScreen(lesson(10))).toBe(0)
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

describe('early course downloads', () => {
  const bundle = {
    'assets/index.js': { type: 'chunk', name: 'index', isEntry: true, imports: ['assets/shared.js'] },
    'assets/shared.js': { type: 'chunk', name: 'shared', isEntry: false, imports: [] },
    'assets/Learn.js': {
      type: 'chunk',
      name: 'Learn',
      isEntry: false,
      imports: ['assets/shared.js', 'assets/lib.js'],
      viteMetadata: { importedCss: new Set(['assets/Learn.css']) },
    },
    'assets/lib.js': { type: 'chunk', name: 'lib', isEntry: false, imports: [] },
    'assets/Other.js': { type: 'chunk', name: 'Other', isEntry: false, imports: [] },
  }

  it('lists the course and what it needs, but not what the entry already loads', () => {
    expect(courseFiles(bundle)).toEqual(['/assets/Learn.js', '/assets/lib.js', '/assets/Learn.css'])
  })

  it('asks for them only on course pages', () => {
    const script = preloadScript(['/assets/Learn.js', '/assets/Learn.css'], {})
    expect(script).toContain("location.pathname.startsWith('/learn')")
    expect(script).toContain('modulepreload')
  })

  it('asks the way Vite will, so the browser reuses the answer instead of fetching twice', () => {
    expect(preloadScript(['/assets/Learn.css'], {})).toContain("l.crossOrigin=''")
  })

  it('maps each lesson to its file, so its text can start downloading straight away', () => {
    const files = {
      'assets/03-chunking-abc.js': { type: 'chunk', facadeModuleId: '/repo/docs/learn/05-rag/03-chunking.md?raw' },
      'assets/Other.js': { type: 'chunk', facadeModuleId: '/repo/web/src/Other.tsx' },
    }
    expect(lessonFiles(files)).toEqual({ '05-rag/03-chunking': '/assets/03-chunking-abc.js' })
    expect(preloadScript([], lessonFiles(files))).toContain('"05-rag/03-chunking":"/assets/03-chunking-abc.js"')
  })

  it('adds nothing when the course is missing', () => {
    expect(courseFiles({})).toEqual([])
  })
})

describe('the question bank', () => {
  const where = { stage: '05-rag', stageTitle: 'RAG', lesson: '03-chunking', lessonTitle: 'Chunking' }
  const raw = [
    '---',
    'title: Chunking',
    '---',
    '',
    '## An example',
    '### Not an interview question',
    '',
    '## Interview questions',
    '',
    '### What is overlap?',
    '',
    '**Strong answer:** Repeated text.',
    '',
    '**Follow-up:** How much?',
    '',
    '## Check yourself',
    '',
    '### Not this one either',
    '',
  ].join('\n')

  it('takes questions only from the interview part, and says where they came from', () => {
    expect(questionsIn(raw, where)).toEqual([
      { ...where, question: 'What is overlap?', answer: 'Repeated text.', followUp: 'How much?' },
    ])
  })

  it('finds nothing in a lesson with no interview part', () => {
    expect(questionsIn('## An example\nWords.\n', where)).toEqual([])
  })

  const bank = [
    { ...where, question: 'What is overlap?', answer: 'Repeated text.', followUp: 'How much?' },
    {
      ...where,
      stage: '08-security',
      stageTitle: 'Security',
      question: 'What is injection?',
      answer: 'An attack.',
      followUp: 'Why?',
    },
  ]

  it('shows everything with no filter', () => {
    expect(filterQuestions(bank, '', '')).toEqual(bank)
  })

  it('filters by stage', () => {
    expect(filterQuestions(bank, '08-security', '').map((q) => q.question)).toEqual(['What is injection?'])
  })

  it('searches the question and the answer, ignoring case', () => {
    expect(filterQuestions(bank, '', 'OVERLAP')).toEqual([bank[0]])
    expect(filterQuestions(bank, '', 'an attack')).toEqual([bank[1]])
  })

  it('applies both filters together', () => {
    expect(filterQuestions(bank, '05-rag', 'attack')).toEqual([])
  })
})
