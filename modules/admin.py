import boto3
import os
import copy
import json
import requests
import time
import qrcode
from loguru import logger

class Admin:
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    dynamodb_table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
    memorify_url = os.environ.get('MEMORIFY_URL')
    d_api_roken = os.environ.get('D-ID_API_TOKEN')
    d_base_url = 'https://api.d-id.com/talks'
    
    st_response_json = {
        'status': 'error',
        'err_description': ''
    }
    
    def __enter__(self):
        self.dynamodb_table = boto3.resource('dynamodb',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name='us-east-1'
        ).Table(self.dynamodb_table_name)
        
        self.s3_bucket = boto3.resource('s3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name='us-east-1'
        ).Bucket(self.s3_bucket_name)
        
        return self
        
    def customers(self) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
      
        try:
            scan = self.dynamodb_table.scan()
            items = scan.get('Items', [])
            if len(items) == 0:
                response_json['err_description'] = 'Жодного записа не знайдено!'
                return response_json
                
            response_json['customers'] = items
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
        
        finally:
            return response_json
            
    def customer(self, user_id: str) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
      
        try:
            get_item = self.dynamodb_table.get_item(Key={'user_id': user_id})
            item = get_item.get('Item', {})
            if not item:
                response_json['err_description'] = 'Запис не знайдено!'
                return response_json
                
            response_json['customer'] = item
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
        
        finally:
            return response_json
            
    def delete_all_customers(self) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
      
        try:
            customers_request = self.customers()
            customers = customers_request.get('customers', [])
            if len(customers) > 0:
                customers_ids = [customer['user_id'] for customer in customers]
                for id in customers_ids: self.delete_customer(id)
            
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
        
        finally:
            return response_json
            
    def delete_customer(self, user_id: str) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
      
        try:
            self.dynamodb_table.delete_item(Key={'user_id': user_id})
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
        
        finally:
            return response_json
        
    def __create_new_talk(self, user_id: str, body: dict) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
      
        try:
            headers = {
                'accept': 'application/json',
                'authorization': 'Basic ' + self.d_api_roken,
                'content-type': 'application/json'
            }

            post_request = requests.post(self.d_base_url, headers=headers, data=json.dumps(body))
            post_response = post_request.json() if 'application/json' in post_request.headers.get('Content-Type') else {}
            
            if post_request.status_code not in [200, 201]:
                post_response_description = post_response.get('description')
                err_description = f'D-ID Talks API відповіло статусом {post_request.status_code}.'
                response_json['err_description'] = f'{err_description} Детальний опис помилки: {post_response_description}.' if post_response_description is not None else err_description
                
                return response_json
            
            talks_id = post_response.get('id')
            
            response_json['talks_id'] = talks_id
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
        
        finally:
            return response_json
            
    def __create_qr(self, user_id: str) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
      
        try:
            url = f'{self.memorify_url}/page?id={user_id}'
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color='black', back_color='white')
            qr_filename = f'{user_id}.png'
            img.save(qr_filename)
            
            with open(qr_filename, 'rb') as qr:
                self.s3_bucket.upload_fileobj(qr, f'{user_id}/qrcode.png')
                
            os.remove(qr_filename)
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
        
        finally:
            return response_json
            
    def create_page(self, user_id: str) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
      
        try:
            customer_request = self.customer(user_id)
            if customer_request['status'] == 'error':
                response_json['err_description'] = customer_request['err_description']
                return response_json
            
            customer = customer_request['customer']
            if customer.get('page', 'FALSE') == 'TRUE':
                response_json['err_description'] = 'Сторінка з такими даними вже створена!'
                return response_json
            
            source_url = 'https://{}.s3.amazonaws.com/{}/{}'.format(self.s3_bucket_name, user_id, customer.get('image_for_video_filename'))
            voice_id = 'Polina' if customer.get('dead_gender') == 'жінка' else 'Ostap'
            input = customer.get('text_for_video')
            body = {
              'source_url': source_url,
              'script': {
                'type': 'text',
                'subtitles': 'false',
                'provider': {
                  'type': 'microsoft',
                  'voice_id': voice_id
                },
                'input': input
              },
              'config': {
                'fluent': 'false',
                'pad_audio': '0.0'
              }
            }

            create_new_qr_request = self.__create_qr(user_id)
            if create_new_qr_request['status'] == 'error':
                response_json['err_description'] = create_new_qr_request['err_description']
                return response_json
            
            create_new_talk_request = self.__create_new_talk(user_id, body)
            if create_new_talk_request['status'] == 'error':
                response_json['err_description'] = create_new_talk_request['err_description']
                return response_json
            
            talks_id = create_new_talk_request.get('talks_id')
            self.dynamodb_table.update_item(
                Key={'user_id': user_id},
                AttributeUpdates={
                    'page': {
                        'Value': 'TRUE',
                        'Action': 'PUT'
                    },
                    'qrcode_source': {
                        'Value': 'qrcode.png',
                        'Action': 'PUT'
                    },
                    'video_source': {
                        'Value': 'video.mp4',
                        'Action': 'PUT'
                    },
                    'talks_id': {
                        'Value': talks_id,
                        'Action': 'PUT'
                    }
                }
            )
            
            customer_endpoint_url = f'{self.memorify_url}/page?id={user_id}'
            response_json['message'] = f'Створення почалось! Перевірте результат по цій ссилці {customer_endpoint_url} через декілька хвилин.'
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
        
        finally:
            return response_json
            
    def __exit__(self, *args):
        pass
