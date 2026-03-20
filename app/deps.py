"""FastAPI dependency injection providers.

All service/repo instantiation in API routes MUST use Depends().
Direct construction breaks testability.
"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# ── Database engine & session factory ────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, auto-commit on success, rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Repository providers ─────────────────────────────────────
from app.repositories.approval_repo import ApprovalRepository
from app.repositories.attendee_repo import AttendeeRepository
from app.repositories.badge_template_repo import BadgeTemplateRepository
from app.repositories.event_repo import EventRepository
from app.repositories.organizer_repo import OrganizerRepository
from app.repositories.seat_repo import SeatRepository


def get_event_repo(db: AsyncSession = Depends(get_db)) -> EventRepository:
    return EventRepository(db)


def get_attendee_repo(db: AsyncSession = Depends(get_db)) -> AttendeeRepository:
    return AttendeeRepository(db)


def get_seat_repo(db: AsyncSession = Depends(get_db)) -> SeatRepository:
    return SeatRepository(db)


def get_approval_repo(db: AsyncSession = Depends(get_db)) -> ApprovalRepository:
    return ApprovalRepository(db)


def get_organizer_repo(db: AsyncSession = Depends(get_db)) -> OrganizerRepository:
    return OrganizerRepository(db)


def get_badge_template_repo(db: AsyncSession = Depends(get_db)) -> BadgeTemplateRepository:
    return BadgeTemplateRepository(db)


# ── Service providers ────────────────────────────────────────
from app.services.approval_service import ApprovalService
from app.services.attendee_service import AttendeeService
from app.services.checkin_service import CheckinService
from app.services.event_service import EventService
from app.services.identity_service import IdentityService
from app.services.seating_service import SeatingService
from app.services.session_service import SessionService, get_session_service


def get_event_service(
    event_repo: EventRepository = Depends(get_event_repo),
) -> EventService:
    return EventService(event_repo)


def get_attendee_service(
    attendee_repo: AttendeeRepository = Depends(get_attendee_repo),
) -> AttendeeService:
    return AttendeeService(attendee_repo)


def get_seating_service(
    seat_repo: SeatRepository = Depends(get_seat_repo),
    attendee_repo: AttendeeRepository = Depends(get_attendee_repo),
) -> SeatingService:
    return SeatingService(seat_repo, attendee_repo)


def get_checkin_service(
    attendee_repo: AttendeeRepository = Depends(get_attendee_repo),
    seat_repo: SeatRepository = Depends(get_seat_repo),
) -> CheckinService:
    return CheckinService(attendee_repo, seat_repo)


def get_approval_service(
    approval_repo: ApprovalRepository = Depends(get_approval_repo),
) -> ApprovalService:
    return ApprovalService(approval_repo)


def get_identity_service(
    attendee_repo: AttendeeRepository = Depends(get_attendee_repo),
) -> IdentityService:
    return IdentityService(attendee_repo)


def get_session_svc() -> SessionService:
    return get_session_service()


# ── Organizer portal service providers ───────────────────────
from app.services.auth_service import AuthService
from app.services.badge_template_service import BadgeTemplateService
from app.services.dashboard_service import DashboardService
from app.services.import_service import ImportService


def get_auth_service(
    organizer_repo: OrganizerRepository = Depends(get_organizer_repo),
) -> AuthService:
    return AuthService(organizer_repo)


def get_dashboard_service(
    event_repo: EventRepository = Depends(get_event_repo),
    attendee_repo: AttendeeRepository = Depends(get_attendee_repo),
    seat_repo: SeatRepository = Depends(get_seat_repo),
    approval_repo: ApprovalRepository = Depends(get_approval_repo),
) -> DashboardService:
    return DashboardService(event_repo, attendee_repo, seat_repo, approval_repo)


def get_import_service(
    attendee_repo: AttendeeRepository = Depends(get_attendee_repo),
) -> ImportService:
    return ImportService(attendee_repo)


def get_badge_template_service(
    badge_template_repo: BadgeTemplateRepository = Depends(get_badge_template_repo),
) -> BadgeTemplateService:
    return BadgeTemplateService(badge_template_repo)
