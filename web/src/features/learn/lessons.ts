export type Section = { title: string; body: string }
export type ParsedLesson = { front: Record<string, string>; intro: string; sections: Section[] }
export type InterviewQuestion = { question: string; answer: string; followUp: string }
export type CheckOption = { text: string; correct: boolean; feedback: string }
export type CheckQuestion = { question: string; options: CheckOption[] }

export function parseLesson(raw: string): ParsedLesson {
  const text = raw.replace(/\r\n/g, '\n')
  const match = /^---\n([\s\S]*?)\n---\n/.exec(text)
  const front: Record<string, string> = {}
  for (const line of match?.[1].split('\n') ?? []) {
    const at = line.indexOf(':')
    if (at > 0) front[line.slice(0, at).trim()] = line.slice(at + 1).trim()
  }

  const lines = (match ? text.slice(match[0].length) : text).split('\n')
  const intro: string[] = []
  const sections: Section[] = []
  let fenced = false
  for (const line of lines) {
    if (line.startsWith('```')) fenced = !fenced
    const heading = !fenced && /^## (.+)$/.exec(line)
    if (heading) sections.push({ title: heading[1].trim(), body: '' })
    else if (sections.length > 0) sections[sections.length - 1].body += `${line}\n`
    else intro.push(line)
  }
  return { front, intro: intro.join('\n'), sections }
}

function blocks(body: string): string[] {
  return body.split(/^### /m).slice(1)
}

export function interviewQuestions(body: string): InterviewQuestion[] {
  return blocks(body).map((block) => {
    const [question, ...rest] = block.split('\n')
    const text = rest.join('\n')
    const answerAt = text.indexOf('**Strong answer:**')
    const followAt = text.indexOf('**Follow-up:**')
    return {
      question: question.trim(),
      answer: text.slice(answerAt + '**Strong answer:**'.length, followAt).trim(),
      followUp: text.slice(followAt + '**Follow-up:**'.length).trim(),
    }
  })
}

export function checkQuestions(body: string): CheckQuestion[] {
  return blocks(body).map((block) => {
    const [question, ...rest] = block.split('\n')
    const options = rest.flatMap((line) => {
      const match = /^- \[([ x])\] (.+?) — (.+)$/.exec(line)
      return match ? [{ text: match[2], correct: match[1] === 'x', feedback: match[3] }] : []
    })
    return { question: question.trim(), options }
  })
}
