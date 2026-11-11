"""
OpenAPI documentation of the HTTP errors raised by the routes.

FastAPI only documents the successful response of a route: the status codes of the
HTTPException it raises are added with the "responses" parameter of the route decorator.
"""
from http import HTTPStatus
from typing import Any, Dict


def error_responses(*status_codes: int) -> Dict[int, Dict[str, Any]]:
    """Build the "responses" metadata of a route from the HTTP error status codes it can raise.

    Example:
        @router.get("/{id}", responses=error_responses(404, 500))
    """
    return {code: {"description": HTTPStatus(code).phrase} for code in status_codes}
