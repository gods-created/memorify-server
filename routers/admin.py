from fastapi import APIRouter
from fastapi.responses import JSONResponse
import copy
import os

from modules.admin import Admin

app = APIRouter(
    prefix='/api/admin',
    tags=['API', 'Admin API']
)

st_response_json = {
    'status': 'error',
    'err_description': ''
}

@app.get('/customers', name='Receive all customers', status_code=200)
def customers():
    global st_response_json
    
    response_json = copy.deepcopy(st_response_json)

    try:
        with Admin() as module:
            customers_response = module.customers()
            
        response_json = copy.copy(customers_response)
        
    except Exception as e:
        response_json['err_description'] = str(e)
       
    finally:
        return JSONResponse(
            content=response_json
        )
        
@app.delete('/customers', name='Delete all customers', status_code=200)
def delete_all_customers():
    global st_response_json
    
    response_json = copy.deepcopy(st_response_json)

    try:
        with Admin() as module:
            delete_all_customers_response = module.delete_all_customers()
            
        response_json = copy.copy(delete_all_customers_response)
        
    except Exception as e:
        response_json['err_description'] = str(e)
       
    finally:
        return JSONResponse(
            content=response_json
        )
        
@app.delete('/customers/{user_id}', name='Delete customer', status_code=200)
def delete_customer(user_id: str):
    global st_response_json
    
    response_json = copy.deepcopy(st_response_json)

    try:
        with Admin() as module:
            delete_customer_response = module.delete_customer(user_id)
            
        response_json = copy.copy(delete_customer_response)
        
    except Exception as e:
        response_json['err_description'] = str(e)
       
    finally:
        return JSONResponse(
            content=response_json
        )

@app.get('/customers/create_page/{user_id}', name='Create page for customer', status_code=200)
def create_page(user_id: str):
    global st_response_json
    
    response_json = copy.deepcopy(st_response_json)

    try:
        with Admin() as module:
            create_page_response = module.create_page(user_id)
            
        response_json = copy.copy(create_page_response)
        
    except Exception as e:
        response_json['err_description'] = str(e)
       
    finally:
        return JSONResponse(
            content=response_json
        )
