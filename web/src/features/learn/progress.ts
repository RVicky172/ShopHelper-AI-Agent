// Kept in this browser only (spec Q4). Storage can be blocked or edited, so nothing here trusts it.
const KEY = 'shophelper.learn.v1'

export type Progress = { done: string[]; last: string | null }

export const emptyProgress: Progress = { done: [], last: null }

export function parseProgress(raw: string | null): Progress {
  try {
    const value = JSON.parse(raw ?? 'null')
    if (!value || !Array.isArray(value.done)) return emptyProgress
    return {
      done: value.done.filter((item: unknown) => typeof item === 'string'),
      last: typeof value.last === 'string' ? value.last : null,
    }
  } catch {
    return emptyProgress
  }
}

export function markDone(progress: Progress, key: string): Progress {
  return progress.done.includes(key) ? progress : { ...progress, done: [...progress.done, key] }
}

export function toggleDone(progress: Progress, key: string): Progress {
  return progress.done.includes(key)
    ? { ...progress, done: progress.done.filter((item) => item !== key) }
    : markDone(progress, key)
}

export function loadProgress(): Progress {
  try {
    return parseProgress(localStorage.getItem(KEY))
  } catch {
    return emptyProgress
  }
}

export function saveProgress(progress: Progress): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(progress))
  } catch {
    // Blocked storage only costs the learner their place.
  }
}
