from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.encoders import jsonable_encoder
import uvicorn

from middlewares.error404 import Error404Middleware
from middlewares.admin import AdminMiddleware

from modules.env import read_and_write

from routers.customer import app as customer_router
from routers.admin import app as admin_router

app = FastAPI(
    title='Memorify API',
    version='0.0.1'
)

app.add_middleware(
    CORSMiddleware,
    allow_headers=['*'],
    allow_methods=['*'],
    allow_origins=['*']
)

app.add_middleware(Error404Middleware)
app.add_middleware(AdminMiddleware)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'detail': exc.detail
        }
    )
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({
            'detail': exc.errors()
        })
    )

@app.get('/', tags=['No API'], name='Root', status_code=302)
def root():
    return RedirectResponse('/docs')
    
@app.get('/error404', tags=['No API', 'Errors'], name='Error 404', status_code=200)
def error404():
    return HTMLResponse(
        content='''
            <div style="width:100%;text-align:center;">
                <h3>ПОМИЛКА 404: сторінка не знайдена.</h3>
            </div>
        '''
    )
    
@app.get('/error403', tags=['No API', 'Errors'], name='Error 403', status_code=200)
def error403():
    return HTMLResponse(
        content='''
            <div style="width:100%;text-align:center;">
                <h3>ПОМИЛКА 403: заборонене використання API.</h3>
            </div>
        '''
    )
    
app.include_router(customer_router)
app.include_router(admin_router)

if __name__ == '__main__':
    read_and_write()
    uvicorn.run('main:app', host='0.0.0.0', port=8001, reload=True)
