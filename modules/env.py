import os
from loguru import logger

file_path = '.env'

def read_and_write() -> None:
    global file_path
    
    if not os.path.exists(file_path):
        logger.error('.env file did not found!')
        return None
        
    with open(file_path, 'r') as f:
        data = f.readlines()
        
    if len(data) == 0:
        logger.error('.env file is empty!')
        return None
        
    for pair in data:
        if '=' in pair:
            key_value = pair.split('=')
            key, value = key_value[0].strip(), key_value[1].replace('\n', '').strip()
            os.environ[key] = value
            
    logger.success('Environment created!')
    return None
