import unittest
from loguru import logger

from modules.admin import Admin
from modules.env import read_and_write

class Tests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        pass
    
    def setUp(self):
        pass
        
    def test_1_create_env(self):
        read_and_write_response = read_and_write()
        self.assertTrue(isinstance(read_and_write_response, None))
        
    def test_1_customers(self):
        with Admin() as module:
            customers_response = module.customers()
            
        logger.debug(customers_response)
        self.assertTrue(isinstance(customers_response, dict))
        
    @classmethod
    def tearDownClass(cls):
        pass
        
if __name__ == '__main__':
    unittest.main()
