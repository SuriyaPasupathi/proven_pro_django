class FixDoubleSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Fix double slashes in the path
        if '//' in request.path:
            request.path = request.path.replace('//', '/')
            request.path_info = request.path_info.replace('//', '/')
        
        response = self.get_response(request)
        return response