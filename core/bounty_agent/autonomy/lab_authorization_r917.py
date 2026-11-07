"""R9.17B: explicit authorization for one local lab target."""

from dataclasses import dataclass
from urllib.parse import urlsplit


class LabAuthorizationError(ValueError):
    pass


@dataclass(frozen=True)
class LocalLabAuthorization:
    target: str
    method: str
    path: str
    approved: bool

    def require(self):
        if self.approved is not True:
            raise LabAuthorizationError("Lab not approved")

        if self.method != "GET" or self.path != "/":
            raise LabAuthorizationError("Operation not authorized")

        try:
            url = urlsplit(self.target)
            valid = (
                url.scheme == "http"
                and url.netloc == "127.0.0.1:3000"
                and url.path in ("", "/")
                and not url.query
                and not url.fragment
                and url.username is None
                and url.password is None
            )
        except ValueError as exc:
            raise LabAuthorizationError("Invalid target") from exc

        if not valid:
            raise LabAuthorizationError("Target outside local lab")

        return True
