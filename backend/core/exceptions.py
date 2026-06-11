from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        errors = []
        if isinstance(response.data, dict):
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    for msg in messages:
                        errors.append({
                            'field': field,
                            'message': str(msg),
                        })
                else:
                    errors.append({
                        'field': field,
                        'message': str(messages),
                    })
        else:
            errors.append({
                'field': 'non_field',
                'message': str(response.data),
            })
        response.data = {
            'success': False,
            'status_code': response.status_code,
            'errors': errors,
        }
    return response


class ServiceUnavailable(Exception):
    pass


class DataValidationError(Exception):
    pass


class ETLProcessingError(Exception):
    pass


class MLTrainingError(Exception):
    pass
