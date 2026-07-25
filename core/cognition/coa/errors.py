class CourseOfActionError(Exception):
    """Base error for executive course-of-action generation."""

class InvalidCourseOfActionError(CourseOfActionError):
    """Raised when a course-of-action contract is invalid."""

class AlternativeGenerationError(CourseOfActionError):
    """Raised when alternatives cannot be generated."""

__all__ = ["CourseOfActionError", "InvalidCourseOfActionError", "AlternativeGenerationError"]
