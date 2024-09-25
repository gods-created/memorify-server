from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from validators.customer import Customer as CustomerValidator
from typing import List
import copy

from modules.customer import Customer
from modules.admin import Admin

app = APIRouter(
    prefix='/api',
    tags=['API']
)

st_response_json = {
    'status': 'error',
    'err_description': ''
}

@app.post('/customer', name='New customer', status_code=200)
async def new_customer(customer: CustomerValidator, image_for_video: UploadFile, dead_images: List[UploadFile]):
    global st_response_json
    
    response_json = copy.deepcopy(st_response_json)

    try:
        with Customer() as module:
            send_application_form_response = await module.send_application_form(
                customer.to_json(),
                image_for_video,
                dead_images
            )
            
        response_json = copy.copy(send_application_form_response)
        
    except Exception as e:
        response_json['err_description'] = str(e)
       
    finally:
        return JSONResponse(
            content=response_json
        )
        
@app.get('/customer/{user_id}', name='Receive customer', status_code=200)
def customer(user_id: str):
    global st_response_json
    
    response_json = copy.deepcopy(st_response_json)

    try:
        with Admin() as module:
            customer_response = module.customer(user_id)
            
        response_json = copy.copy(customer_response)
        
    except Exception as e:
        response_json['err_description'] = str(e)
       
    finally:
        return JSONResponse(
            content=response_json
        )
