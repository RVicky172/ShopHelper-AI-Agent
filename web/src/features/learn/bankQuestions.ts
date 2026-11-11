import { type InterviewQuestion, interviewQuestions, parseLesson } from './lessons'

export type Source = { stage: string; stageTitle: string; lesson: string; lessonTitle: string }
export type BankQuestion = InterviewQuestion & Source

/** One lesson's interview questions. The lesson stays their only home, so the bank is never a copy. */
export function questionsIn(raw: string, where: Source): BankQuestion[] {
  const part = parseLesson(raw).sections.find((section) => section.title === 'Interview questions')
  return part ? interviewQuestions(part.body).map((item) => ({ ...where, ...item })) : []
}

export function filterQuestions(bank: BankQuestion[], stage: string, query: string): BankQuestion[] {
  const term = query.trim().toLowerCase()
  return bank.filter(
    (item) =>
      (!stage || item.stage === stage) &&
      (!term || item.question.toLowerCase().includes(term) || item.answer.toLowerCase().includes(term)),
  )
}
