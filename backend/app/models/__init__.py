"""SQLAlchemy ORM models.

Importing this package registers every mapper, which matters for relationship
resolution by string name.
"""

from app.models.ai import ActivityLog, LLMAudit, LLMCache
from app.models.architecture import (
    Activity,
    ActivityCompetency,
    AssistantQuery,
    CompetencyCutScore,
    ConsentRecord,
    Event,
    FrameworkVersion,
    GapSnapshot,
    MartCompetency,
    MartTrainingEffectiveness,
    Nomination,
    OutboxEntry,
    ProfileAttribute,
    TagCrosswalk,
)
from app.models.assessment import Assessment, AssessmentQuestion
from app.models.base import Base
from app.models.competency import Competency, RoleCompetencyRequirement
from app.models.course import Course, Enrollment, Recommendation
from app.models.evidence import CONFIDENCE_BY_SOURCE, CompetencyEvidence, UserCompetency
from app.models.material import LearningMaterial, MaterialChunk
from app.models.question import Question
from app.models.user import AuthUser, JobRole, Profile, UserRole

__all__ = [
    "Activity",
    "ActivityCompetency",
    "ActivityLog",
    "AssistantQuery",
    "CompetencyCutScore",
    "ConsentRecord",
    "Event",
    "FrameworkVersion",
    "GapSnapshot",
    "MartCompetency",
    "MartTrainingEffectiveness",
    "Nomination",
    "OutboxEntry",
    "ProfileAttribute",
    "TagCrosswalk",
    "Assessment",
    "AssessmentQuestion",
    "AuthUser",
    "Base",
    "CONFIDENCE_BY_SOURCE",
    "Competency",
    "CompetencyEvidence",
    "Course",
    "Enrollment",
    "JobRole",
    "LLMAudit",
    "LLMCache",
    "LearningMaterial",
    "MaterialChunk",
    "Profile",
    "Question",
    "Recommendation",
    "RoleCompetencyRequirement",
    "UserCompetency",
    "UserRole",
]
