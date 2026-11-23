
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    original_data = response.data

    if isinstance(original_data, dict):
        if "detail" in original_data:
            message = str(original_data["detail"])
        else:
            message = "Request validation failed."
    else:
        message = "Request could not be processed."

    response.data = {
        "success": False,
        "status_code": response.status_code,
        "message": message,
        "errors": original_data,
    }

    return response
