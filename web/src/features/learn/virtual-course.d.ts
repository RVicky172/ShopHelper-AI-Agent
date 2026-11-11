declare module 'virtual:course' {
  export const course: import('./course').Stage[]
}

declare module 'virtual:course-questions' {
  export const questions: import('./bankQuestions').BankQuestion[]
}
