import boto3
import os
import copy
import uuid
import json
import threading
from loguru import logger
from datetime import datetime

class Customer:
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    dynamodb_table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
    topic_arn = os.environ.get('TOPIC_ARN')
    
    st_response_json = {
        'status': 'error',
        'err_description': ''
    }
    
    def __enter__(self):
        self.sns_client = boto3.client('sns',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name='us-east-1'
        )
        
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
        
    def __if_file_is_image(self, files: list) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
        response_json['image_for_video_filename'] = ''
        response_json['dead_images_filenames'] = []
        
        for index, f in enumerate(files):
            filename = f.filename
            
            if not filename.endswith(('.png', '.jpg', '.jpeg')):
                return response_json
            
            if index == 0:
                response_json['image_for_video_filename'] = filename
            else:
                response_json['dead_images_filenames'].append(filename)
            
        response_json['status'] = 'success'
        return response_json
        
    def __save_data_to_db(self, *args) -> None:
        try:
            item = {
                'user_id': str(args[0]),
                'user_fullname': args[1],
                'user_email': args[2],
                'user_phone': args[3],
                'dead_fullname': args[4],
                'dead_gender': args[5],
                'text_for_video': args[6],
                'dead_biography': args[7],
                'image_for_video_filename': args[8],
                'dead_images_filenames': json.dumps(args[9])
            }
            
            self.dynamodb_table.put_item(
                Item=item
            )
            
            logger.success('Дані замовніка додані в БД!')
            
        except Exception as e:
            logger.error(str(e))
        
    async def __save_images_to_bucket(self, folder_name: str, files: list) -> None:
        try:
            for file in files:
                self.s3_bucket.upload_fileobj(
                    file.file, Key=f'{folder_name}/{file.filename}'
                )
                
            logger.success('Зображення завантажені в бакет!')
                
        except Exception as e:
            logger.error(str(e))
            
    def __send_mail(self, *args) -> None:
        try:
            user_id, fullname, email, phone = args
            created_at = datetime.now().strftime('%d.%m.%Y, %H:%M:%S')
            
            mail_message = 'ДАНІ КЛІЄНТА:\n\n' \
                    f'Айді клієнта в БД: {user_id}\n' \
                    f'ПІБ: {fullname}\n' \
                    f'Пошта: {email}\n' \
                    f'Телефон: {phone}\n' \
                    \
                    f'\n{created_at}'

            self.sns_client.publish(
                TopicArn=self.topic_arn,
                Message=mail_message,
                Subject='Повідомлення від клієнта "Memorify"'
            )

            logger.success('Повідомлення надіслано менеджеру на пошту!')
                
        except Exception as e:
            logger.error(str(e))
        
    async def send_application_form(self, *args) -> dict:
        response_json = copy.deepcopy(self.st_response_json)
        
        try:
            customer, image_for_video, dead_images = args
            all_files_list = [image_for_video, *dead_images]
            if_file_is_image = self.__if_file_is_image(all_files_list)
            
            if if_file_is_image['status'] == 'error':
                response_json['err_description'] = 'Зображення не вірного формату!'
                return response_json
            
            user_id = uuid.uuid4()
            user_fullname = customer.get('user_fullname')
            user_email = customer.get('user_email')
            user_phone = customer.get('user_phone')
            dead_fullname = customer.get('dead_fullname')
            dead_gender = customer.get('dead_gender')
            text_for_video = customer.get('text_for_video')
            dead_biography = customer.get('dead_biography')
            image_for_video_filename = if_file_is_image['image_for_video_filename']
            dead_images_filenames = if_file_is_image['dead_images_filenames']
            
            th1 = threading.Thread(target=self.__save_data_to_db, args=(
                user_id,
                user_fullname,
                user_email,
                user_phone,
                dead_fullname,
                dead_gender,
                text_for_video,
                dead_biography,
                image_for_video_filename,
                dead_images_filenames,
            ))
            
            th2 = threading.Thread(target=self.__send_mail, args=(
                user_id,
                user_fullname,
                user_email,
                user_phone,
            ))
            
            for th in [th1, th2]:
                th.start()
            
            await self.__save_images_to_bucket(user_id, all_files_list)
            response_json['status'] = 'success'
            
        except Exception as e:
            response_json['err_description'] = str(e)
            
        finally:
            logger.debug(response_json)
            return response_json
            
    def __exit__(self, *args):
        self.sns_client.close()
