from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os

class AdminMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        route = request.scope.get('route', None)
        if route is not None and 'api/admin' in route.path:
            headers = request.headers
            token = headers.get('Authorization', '').replace('Bearer ', '')

            if token != os.environ.get('ADMIN_API_KEY'):
                return RedirectResponse('/error403')
            
        return response
