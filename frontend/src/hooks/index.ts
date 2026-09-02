/** Data hooks. One place per resource so cache keys stay consistent. */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, API } from '../lib/api'
import type {
  Activity,
  AdminOverview,
  Assessment,
  AssessmentHistoryItem,
  Competency,
  CompetencyMatrix,
  Course,
  EventStream,
  Enrollment,
  GapList,
  GenerationSummary,
  Health,
  Material,
  MyAnalytics,
  MyCompetency,
  Profile,
  Question,
  RecommendationBatch,
  RecommendationContext,
  SubmitResponse,
  TrainingEffectiveness,
} from '../lib/types'

// ── system ───────────────────────────────────────────────────────────────────

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => (await api.get<Health>('/health')).data,
    staleTime: 60_000,
  })
}

// ── M1 · profile ─────────────────────────────────────────────────────────────

/**
 * The signed-in officer's profile is held by AuthProvider in React state, not
 * in the query cache, so there is no key to invalidate here. Callers fold the
 * returned Profile back into the session with `applyProfile` from useAuth().
 */
export function useUpdateProfile() {
  return useMutation({
    mutationFn: async (data: {
      full_name?: string
      designation?: string
      station?: string
      years_experience?: number
      education?: string
    }) => (await api.patch<Profile>(API.v1('/profiles/me'), data)).data,
  })
}

// ── M2 · competencies ────────────────────────────────────────────────────────

export function useCompetencies() {
  return useQuery({
    queryKey: ['competencies'],
    queryFn: async () => (await api.get<Competency[]>(API.v1('/competencies'))).data,
    staleTime: 10 * 60_000,
  })
}

export function useDeclareBatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (declarations: Array<{ competency_id: string; level: number; note?: string }>) =>
      (await api.post(API.v1('/competencies/me/declare'), { declarations })).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['competencies', 'me'] })
      void queryClient.invalidateQueries({ queryKey: ['gaps'] })
      void queryClient.invalidateQueries({ queryKey: ['analytics'] })
    },
  })
}

export function useMyCompetencies() {
  return useQuery({
    queryKey: ['competencies', 'me'],
    queryFn: async () => (await api.get<MyCompetency[]>(API.v1('/competencies/me'))).data,
  })
}

// ── M4 · gaps ────────────────────────────────────────────────────────────────

export function useGaps() {
  return useQuery({
    queryKey: ['gaps', 'me'],
    queryFn: async () => (await api.get<GapList>(API.v1('/gaps/me'))).data,
  })
}

/** Position -> Role -> Activity -> Competency: what the role actually does. */
export function useActivities() {
  return useQuery({
    queryKey: ['gaps', 'me', 'activities'],
    queryFn: async () => (await api.get<Activity[]>(API.v1('/gaps/me/activities'))).data,
    staleTime: 5 * 60_000,
  })
}

// ── M5 · recommendations ─────────────────────────────────────────────────────

export function useRecommendations() {
  return useQuery({
    queryKey: ['recommendations', 'me'],
    queryFn: async () =>
      (await api.get<RecommendationBatch>(API.v1('/recommendations/me?batch=latest'))).data,
  })
}

export function useGenerateRecommendations() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () =>
      (
        await api.post<RecommendationBatch>(API.v1('/recommendations/generate'), {
          limit: 5,
          max_per_competency: 2,
          explain: true,
        })
      ).data,
    onSuccess: (batch) => {
      queryClient.setQueryData(['recommendations', 'me'], batch)
    },
  })
}

export function useRecommendationContext(id: string | null) {
  return useQuery({
    queryKey: ['recommendation-context', id],
    enabled: Boolean(id),
    queryFn: async () =>
      (await api.get<RecommendationContext>(API.v1(`/recommendations/${id}/breakdown`))).data,
  })
}

// ── M6 · catalogue ───────────────────────────────────────────────────────────

export function useCourses(params: { competency?: string; source?: string; q?: string } = {}) {
  const search = new URLSearchParams()
  if (params.competency) search.set('competency', params.competency)
  if (params.source) search.set('source', params.source)
  if (params.q) search.set('q', params.q)
  const suffix = search.toString() ? `?${search.toString()}` : ''

  return useQuery({
    queryKey: ['courses', params],
    queryFn: async () => (await api.get<Course[]>(API.v1(`/catalogue/courses${suffix}`))).data,
  })
}

export function useCourse(id: string | undefined) {
  return useQuery({
    queryKey: ['course', id],
    enabled: Boolean(id),
    queryFn: async () => (await api.get<Course>(API.v1(`/catalogue/courses/${id}`))).data,
  })
}

export function useMyEnrollments() {
  return useQuery({
    queryKey: ['enrollments', 'me'],
    queryFn: async () => (await api.get<Enrollment[]>(API.v1('/catalogue/my-enrollments'))).data,
  })
}

export function useEnroll() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (courseId: string) =>
      (await api.post<Enrollment>(API.v1(`/catalogue/courses/${courseId}/enroll`), {})).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['enrollments'] })
    },
  })
}

export function useNominate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      courseId,
      justification,
    }: {
      courseId: string
      justification: string
    }) =>
      (
        await api.post<Enrollment>(API.v1(`/catalogue/programmes/${courseId}/nominate`), {
          justification,
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['enrollments'] })
    },
  })
}

// ── M8 · materials ───────────────────────────────────────────────────────────

export function useMaterials(enabled = true) {
  return useQuery({
    queryKey: ['materials'],
    enabled,
    queryFn: async () => (await api.get<Material[]>(API.v1('/materials'))).data,
  })
}

export function useUploadMaterial() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { file: File; title: string; competencyId: string }) => {
      const form = new FormData()
      form.append('file', input.file)
      form.append('title', input.title)
      form.append('competency_id', input.competencyId)
      const { data } = await api.post<Material>(API.v1('/materials'), form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

export function useGenerateQuestions() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { materialId: string; numQuestions: number }) =>
      (
        await api.post<GenerationSummary>(API.v1(`/materials/${input.materialId}/generate`), {
          num_questions: input.numQuestions,
          difficulty_mix: 'balanced',
          auto_approve_passing: false,
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['materials'] })
      void queryClient.invalidateQueries({ queryKey: ['material-questions'] })
    },
  })
}

export function useMaterialQuestions(materialId: string | null) {
  return useQuery({
    queryKey: ['material-questions', materialId],
    enabled: Boolean(materialId),
    queryFn: async () =>
      (await api.get<Question[]>(API.v1(`/materials/${materialId}/questions`))).data,
  })
}

export function useReviewQuestion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { id: string; status: 'APPROVED' | 'REJECTED' }) =>
      (await api.patch<Question>(API.v1(`/questions/${input.id}`), { status: input.status })).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['material-questions'] })
      void queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

// ── M3 · assessments ─────────────────────────────────────────────────────────

export function useAssessmentHistory() {
  return useQuery({
    queryKey: ['assessments', 'me'],
    queryFn: async () => (await api.get<AssessmentHistoryItem[]>(API.v1('/assessments/me'))).data,
  })
}

export function useAssessment(id: string | undefined) {
  return useQuery({
    queryKey: ['assessment', id],
    enabled: Boolean(id),
    queryFn: async () => (await api.get<Assessment>(API.v1(`/assessments/${id}`))).data,
  })
}

export function useCreateAssessment() {
  return useMutation({
    mutationFn: async (input: {
      competencyId: string
      count: number
      materialId?: string
      mode?: 'proctored' | 'practice'
    }) =>
      (
        await api.post<Assessment>(API.v1('/assessments'), {
          competency_id: input.competencyId,
          count: input.count,
          material_id: input.materialId ?? null,
          mode: input.mode ?? 'practice',
        })
      ).data,
  })
}

export function useAnswer() {
  return useMutation({
    mutationFn: async (input: {
      assessmentId: string
      questionId: string
      selectedIndex: number
    }) =>
      (
        await api.post(API.v1(`/assessments/${input.assessmentId}/answer`), {
          question_id: input.questionId,
          selected_index: input.selectedIndex,
        })
      ).data,
  })
}

export function useSubmitAssessment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (assessmentId: string) =>
      (await api.post<SubmitResponse>(API.v1(`/assessments/${assessmentId}/submit`))).data,
    onSuccess: () => {
      // The loop closed: everything downstream of the evidence ledger is stale.
      void queryClient.invalidateQueries({ queryKey: ['gaps'] })
      void queryClient.invalidateQueries({ queryKey: ['competencies', 'me'] })
      void queryClient.invalidateQueries({ queryKey: ['recommendations'] })
      void queryClient.invalidateQueries({ queryKey: ['analytics'] })
      void queryClient.invalidateQueries({ queryKey: ['assessments'] })
    },
  })
}

// ── M9 · analytics ───────────────────────────────────────────────────────────

export function useMyAnalytics() {
  return useQuery({
    queryKey: ['analytics', 'me'],
    queryFn: async () => (await api.get<MyAnalytics>(API.v1('/analytics/me'))).data,
  })
}

export function useAdminOverview(enabled = true) {
  return useQuery({
    queryKey: ['analytics', 'admin', 'overview'],
    enabled,
    queryFn: async () => (await api.get<AdminOverview>(API.v1('/analytics/admin/overview'))).data,
  })
}

export function useCompetencyMatrix(enabled = true) {
  return useQuery({
    queryKey: ['analytics', 'admin', 'matrix'],
    enabled,
    queryFn: async () =>
      (await api.get<CompetencyMatrix>(API.v1('/analytics/admin/competency-matrix'))).data,
  })
}

export function useEventStream(enabled = true) {
  return useQuery({
    queryKey: ['analytics', 'admin', 'events'],
    enabled,
    queryFn: async () =>
      (await api.get<EventStream>(API.v1('/analytics/admin/events?limit=25'))).data,
  })
}

export function useRebuildMarts() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () =>
      (await api.post<Record<string, number | string>>(API.v1('/analytics/admin/rebuild-marts')))
        .data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['analytics'] })
    },
  })
}

export function useTrainingEffectiveness(enabled = true) {
  return useQuery({
    queryKey: ['analytics', 'admin', 'effectiveness'],
    enabled,
    queryFn: async () =>
      (await api.get<TrainingEffectiveness>(API.v1('/analytics/admin/training-effectiveness')))
        .data,
  })
}

// ── M3 · initial competency assessment ───────────────────────────────────────

import type {
  InitialTopicsResponse,
  InitialStartResponse,
  InitialCompleteResponse,
} from '../lib/types'

export function useInitialAssessmentTopics() {
  return useQuery({
    queryKey: ['initial-assessment', 'topics'],
    queryFn: async () =>
      (await api.get<InitialTopicsResponse>(API.v1('/assessments/initial/topics'))).data,
    staleTime: 0,
  })
}

export function useStartInitialAssessment() {
  return useMutation({
    mutationFn: async () =>
      (await api.post<InitialStartResponse>(API.v1('/assessments/initial/start'))).data,
  })
}

export function useCompleteInitialAssessment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (assessmentIds: string[]) => {
      const { data } = await api.post<InitialCompleteResponse>(
        API.v1('/assessments/initial/complete'),
        { assessment_ids: assessmentIds },
      )
      return data
    },
    onSuccess: () => {
      // Invalidate both /me and /auth/me to fetch the updated initial_assessment_completed flag
      void queryClient.invalidateQueries({ queryKey: ['me'] })
      void queryClient.invalidateQueries({ queryKey: ['assessments', 'me'] })
      // The assessment wrote real evidence — everything downstream is stale.
      void queryClient.invalidateQueries({ queryKey: ['recommendations'] })
      void queryClient.invalidateQueries({ queryKey: ['gaps'] })
      void queryClient.invalidateQueries({ queryKey: ['competencies', 'me'] })
      void queryClient.invalidateQueries({ queryKey: ['analytics'] })
      void queryClient.invalidateQueries({ queryKey: ['assessments'] })
    },
  })
}

export function useTerminateInitialAssessment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<{ status: string; message: string }>(
        API.v1('/assessments/initial/terminate')
      )
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export function useBlockedAccounts() {
  return useQuery({
    queryKey: ['blockedAccounts'],
    queryFn: async () => {
      const { data } = await api.get<{ id: string; full_name: string; email: string; blocked_until: string }[]>(
        API.v1('/profiles/all/blocked')
      )
      return data
    },
  })
}

export function useUnblockUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) => {
      const { data } = await api.post<{ status: string; message: string }>(
        API.v1(`/profiles/${userId}/unblock`)
      )
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['blockedAccounts'] })
    },
  })
}
