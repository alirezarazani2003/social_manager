from rest_framework.response import Response

def success_response(message='', data=None, status_code=200):
    return Response({
        'status': 'success',
        'message': message,
        'data': data,
    }, status=status_code)

def error_response(message='', errors=None, status_code=400):
    return Response({
        'status': 'error',
        'message': message,
        'errors': errors,
    }, status=status_code)
