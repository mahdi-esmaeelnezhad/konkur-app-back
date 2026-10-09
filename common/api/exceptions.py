from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    code = getattr(exc, "default_code", "error")
    if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
        message = detail["detail"]
        errors = None
    else:
        message = getattr(exc, "default_detail", "Request failed")
        errors = detail

    response.data = {
        "success": False,
        "error": {
            "code": code,
            "message": str(message),
            "errors": errors,
        },
    }
    return response


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"
    default_code = "conflict"


class ForbiddenAction(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Forbidden"
    default_code = "forbidden"
