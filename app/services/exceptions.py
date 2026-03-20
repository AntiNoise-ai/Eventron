"""Domain-specific exceptions for the service layer.

API routes catch these and map to HTTP status codes.
"""


class EventronError(Exception):
    """Base exception for all Eventron domain errors."""

    pass


class NotFoundError(EventronError):
    """Requested entity does not exist."""

    pass


class EventNotFoundError(NotFoundError):
    pass


class AttendeeNotFoundError(NotFoundError):
    pass


class SeatNotFoundError(NotFoundError):
    pass


class SeatNotAvailableError(EventronError):
    """Seat cannot be assigned (already occupied, disabled, etc.)."""

    pass


class InvalidStateTransitionError(EventronError):
    """Entity cannot transition to the requested state."""

    pass


class DuplicateAssignmentError(EventronError):
    """Attendee is already assigned to a seat."""

    pass


class ApprovalRequiredError(EventronError):
    """The requested change requires human approval."""

    def __init__(self, approval_id: str, message: str = "Approval required"):
        self.approval_id = approval_id
        super().__init__(message)


class AuthenticationError(EventronError):
    """Login failed — bad credentials or disabled account."""

    pass


class DuplicateEmailError(EventronError):
    """Email already registered."""

    pass


class TemplateNotFoundError(NotFoundError):
    pass
