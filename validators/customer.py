from pydantic import BaseModel, Field, root_validator, field_validator
from enum import Enum
import re
import json

class Gender(Enum):
    M = 'чоловік'
    W = 'жінка'

class Customer(BaseModel):
    user_fullname: str = Field(default='Арсеній Яценюк')
    user_email: str = Field(default='example@gmail.com')
    user_phone: str = Field(default='+380954321000')
    dead_fullname: str = Field(default='Микола Тищенко')
    dead_gender: Gender = Field(default='жінка')
    text_for_video: str = Field(default='Микола народився 17 травня 1972 року ...')
    dead_biography: str = Field(default='Микола народився 17 травня 1972 року ...')
    
    @root_validator(pre=True)
    def validator(cls, values):
        values = json.loads(values)
        
        for key in values.keys():
            value = values.get(key)
            
            if len(value) < 1:
                raise ValueError(f'Недостатня кількість символів!')
                
            if key == 'text_for_video' and len(value) > 450:
                raise ValueError(f'Максимальна кількість символів для відеопрезентації дорівнює 450!')
        
        return values
        
    @field_validator('user_email')
    def email_validator(cls, email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        result = re.match(email_regex, email) is not None
        if not result:
            raise ValueError('Пошта не є валідною!')
        
        return email
        
    @field_validator('user_phone')
    def phone_validator(cls, phone):
        pattern = r'^\+380\d{9}$'
        if not bool(re.match(pattern, phone)):
            raise ValueError('Номер телефону не є валідним!')
        
        return phone

    def to_json(self):
        return {
            'user_fullname': self.user_fullname,
            'user_email': self.user_email,
            'user_phone': self.user_phone,
            'dead_fullname': self.dead_fullname,
            'dead_gender': self.dead_gender.value,
            'text_for_video': self.text_for_video,
            'dead_biography': self.dead_biography
        }
