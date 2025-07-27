from rest_framework.response import Response

def success_response(message='', data=None, status_code=200):
    response_data = {
        'status': 'success',
        'message': message,
    }
    
    if data is not None:
        response_data['data'] = data
    
    return Response(response_data, status=status_code)

def error_response(message='', errors=None, status_code=400, data=None):
    response_data = {
        'status': 'error',
        'message': message,
    }
    
    if errors is not None:
        response_data['errors'] = errors
    
    if data is not None:
        response_data.update(data)
    return Response(response_data, status=status_code)