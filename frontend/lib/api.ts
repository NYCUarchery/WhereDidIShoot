import type {
  ArrowInput,
  ArrowRecord,
  EndInput,
  EndRecord,
  HealthResponse,
  PracticeInput,
  PracticeRecord,
  RoundInput,
  RoundRecord,
  UserInput,
  UserRecord,
} from '~/generated/sdk'

type ApiFetchOptions = Parameters<typeof $fetch>[1]

export interface LoginInput {
  password: string
  username: string
}

export interface LoginResponse {
  created: boolean
  password_initialized?: boolean
  user: UserRecord
}

function getBaseUrl() {
  const config = useRuntimeConfig()
  return import.meta.server ? config.apiInternalBase : config.public.apiBase
}

function apiFetch<T>(path: string, options: ApiFetchOptions = {}) {
  return $fetch<T>(path, {
    baseURL: getBaseUrl(),
    ...options,
  })
}

export function getErrorMessage(error: unknown) {
  if (error && typeof error === 'object' && 'data' in error) {
    const data = (error as { data?: { message?: string } }).data
    if (data?.message) {
      return data.message
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Request failed.'
}

export function useHealthApi() {
  return {
    getHealth: () => apiFetch<HealthResponse>('/health'),
  }
}

export function useAuthApi() {
  return {
    login: (payload: LoginInput) =>
      apiFetch<LoginResponse>('/auth/login', { body: payload, method: 'POST' }),
  }
}

export function useUsersApi() {
  return {
    list: () => apiFetch<UserRecord[]>('/users'),
    get: (userId: number) => apiFetch<UserRecord>(`/users/${userId}`),
    create: (payload: UserInput) =>
      apiFetch<UserRecord>('/users', { body: payload, method: 'POST' }),
    update: (userId: number, payload: UserInput) =>
      apiFetch<UserRecord>(`/users/${userId}`, { body: payload, method: 'PUT' }),
    remove: (userId: number) =>
      apiFetch<void>(`/users/${userId}`, { method: 'DELETE' }),
  }
}

export function usePracticesApi() {
  return {
    list: (query: { user_id?: number } = {}) =>
      apiFetch<PracticeRecord[]>('/practices', { query }),
    get: (practiceId: number) => apiFetch<PracticeRecord>(`/practices/${practiceId}`),
    create: (payload: PracticeInput) =>
      apiFetch<PracticeRecord>('/practices', { body: payload, method: 'POST' }),
    update: (practiceId: number, payload: PracticeInput) =>
      apiFetch<PracticeRecord>(`/practices/${practiceId}`, { body: payload, method: 'PUT' }),
    remove: (practiceId: number) =>
      apiFetch<void>(`/practices/${practiceId}`, { method: 'DELETE' }),
  }
}

export function useRoundsApi() {
  return {
    list: (query: { practice_id?: number } = {}) =>
      apiFetch<RoundRecord[]>('/rounds', { query }),
    get: (roundId: number) => apiFetch<RoundRecord>(`/rounds/${roundId}`),
    create: (payload: RoundInput) =>
      apiFetch<RoundRecord>('/rounds', { body: payload, method: 'POST' }),
    update: (roundId: number, payload: RoundInput) =>
      apiFetch<RoundRecord>(`/rounds/${roundId}`, { body: payload, method: 'PUT' }),
    remove: (roundId: number) =>
      apiFetch<void>(`/rounds/${roundId}`, { method: 'DELETE' }),
  }
}

export function useEndsApi() {
  return {
    list: (query: { round_id?: number } = {}) => apiFetch<EndRecord[]>('/ends', { query }),
    get: (endId: number) => apiFetch<EndRecord>(`/ends/${endId}`),
    create: (payload: EndInput) =>
      apiFetch<EndRecord>('/ends', { body: payload, method: 'POST' }),
    update: (endId: number, payload: EndInput) =>
      apiFetch<EndRecord>(`/ends/${endId}`, { body: payload, method: 'PUT' }),
    remove: (endId: number) => apiFetch<void>(`/ends/${endId}`, { method: 'DELETE' }),
  }
}

export function useArrowsApi() {
  return {
    list: (query: { end_id?: number } = {}) => apiFetch<ArrowRecord[]>('/arrows', { query }),
    get: (arrowId: number) => apiFetch<ArrowRecord>(`/arrows/${arrowId}`),
    create: (payload: ArrowInput) =>
      apiFetch<ArrowRecord>('/arrows', { body: payload, method: 'POST' }),
    update: (arrowId: number, payload: ArrowInput) =>
      apiFetch<ArrowRecord>(`/arrows/${arrowId}`, { body: payload, method: 'PUT' }),
    remove: (arrowId: number) =>
      apiFetch<void>(`/arrows/${arrowId}`, { method: 'DELETE' }),
  }
}
