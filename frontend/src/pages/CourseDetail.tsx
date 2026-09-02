import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, CalendarDays, Clock, Layers, MonitorPlay, Users } from 'lucide-react'

import {
  Badge,
  Button,
  Card,
  ErrorNote,
  Field,
  PageHeader,
  Skeleton,
} from '../components/common'
import { MockNotice } from '../components/common/MockNotice'
import { useCourse, useEnroll, useMyEnrollments, useNominate } from '../hooks'
import { errorMessage } from '../lib/api'
import { FORMAT_LABEL, formatDate } from '../lib/format'

export default function CourseDetail() {
  const { courseId } = useParams<{ courseId: string }>()
  const { data: course, isLoading } = useCourse(courseId)
  const enrollments = useMyEnrollments()
  const enroll = useEnroll()
  const nominate = useNominate()

  const [justification, setJustification] = useState('')

  const existing = enrollments.data?.find((e) => e.course_id === courseId)
  const isNSSTA = course?.source === 'NSSTA'
  const action = isNSSTA ? nominate : enroll

  if (isLoading) {
    return (
      <Card>
        <Skeleton className="mb-3 h-6 w-2/3" />
        <Skeleton className="h-32 w-full" />
      </Card>
    )
  }

  if (!course) {
    return (
      <Card>
        <p className="text-14 text-ink-2">That course could not be found.</p>
      </Card>
    )
  }

  return (
    <>
      <Link
        to="/recommendations"
        className="mb-4 inline-flex items-center gap-1 text-13 text-ink-2 hover:text-accent"
      >
        <ArrowLeft size={14} strokeWidth={1.5} aria-hidden />
        Back to recommendations
      </Link>

      <PageHeader title={course.title} description={course.provider} />

      <div className="mb-4">
        <MockNotice />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-8" label="About this course">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Badge tone={course.source === 'IGOT' ? 'accent' : 'neutral'}>{course.source}</Badge>
            <Badge>{course.competency_code}</Badge>
            <span className="inline-flex items-center gap-1 text-12 text-ink-2">
              <Layers size={14} strokeWidth={1.5} aria-hidden />
              Level {course.proficiency_level}
            </span>
            <span className="inline-flex items-center gap-1 text-12 text-ink-2">
              <Clock size={14} strokeWidth={1.5} aria-hidden />
              {course.duration_hours} h
            </span>
            <span className="inline-flex items-center gap-1 text-12 text-ink-2">
              <MonitorPlay size={14} strokeWidth={1.5} aria-hidden />
              {FORMAT_LABEL[course.learning_format] ?? course.learning_format}
            </span>
            {course.session_start && (
              <span className="inline-flex items-center gap-1 text-12 text-ink-2">
                <CalendarDays size={14} strokeWidth={1.5} aria-hidden />
                Starts {formatDate(course.session_start)}
              </span>
            )}
            {course.seats != null && (
              <span className="inline-flex items-center gap-1 text-12 text-ink-2">
                <Users size={14} strokeWidth={1.5} aria-hidden />
                {course.seats} seats
              </span>
            )}
          </div>

          <p className="max-w-prose text-14 leading-relaxed text-ink">{course.description}</p>

          {course.prerequisites.length > 0 && (
            <div className="mt-4">
              <p className="eyebrow mb-2">Prerequisites</p>
              <div className="flex flex-wrap gap-1.5">
                {course.prerequisites.map((code) => (
                  <Badge key={code}>{code}</Badge>
                ))}
              </div>
            </div>
          )}

          <p className="mt-4 font-mono text-11 text-ink-3">
            external_id={course.external_id} · synced {formatDate(course.synced_at)}
          </p>
        </Card>

        <Card className="lg:col-span-4" label={isNSSTA ? 'Request nomination' : 'Enrolment'}>
          {existing ? (
            <>
              <Badge tone={existing.status === 'COMPLETED' ? 'met' : 'accent'}>
                {existing.status.replace(/_/g, ' ')}
              </Badge>
              {existing.external_ref && (
                <p className="mt-2 font-mono text-11 text-ink-3">ref {existing.external_ref}</p>
              )}
              {existing.note && (
                <p className="mt-2 max-w-prose text-12 leading-relaxed text-ink-2">
                  {existing.note}
                </p>
              )}
            </>
          ) : isNSSTA ? (
            <div className="space-y-4">
              <p className="max-w-prose text-13 leading-relaxed text-ink-2">
                Academy programmes are nominated for, not self-enrolled. You request; a controlling
                authority nominates; the academy confirms against available seats. Only the first
                step is modelled here.
              </p>
              <Field id="justification" label="Justification">
                <textarea
                  id="justification"
                  rows={4}
                  className="w-full rounded border border-rule bg-surface p-3 text-14 text-ink"
                  value={justification}
                  onChange={(event) => setJustification(event.target.value)}
                />
              </Field>
              {nominate.isError && <ErrorNote>{errorMessage(nominate.error)}</ErrorNote>}
              <Button
                variant="primary"
                loading={nominate.isPending}
                onClick={() => nominate.mutate({ courseId: course.id, justification })}
              >
                Request nomination
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="max-w-prose text-13 leading-relaxed text-ink-2">
                iGOT courses are self-paced and joined directly by the officer.
              </p>
              {enroll.isError && <ErrorNote>{errorMessage(enroll.error)}</ErrorNote>}
              <Button
                variant="primary"
                loading={enroll.isPending}
                onClick={() => enroll.mutate(course.id)}
              >
                Enrol
              </Button>
            </div>
          )}

          {action.data?.note && (
            <p className="mt-3 max-w-prose text-12 leading-relaxed text-ink-2">
              {action.data.note}
            </p>
          )}
        </Card>
      </div>
    </>
  )
}
