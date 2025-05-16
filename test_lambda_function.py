import unittest
import json
from lambda_function import lambda_handler

class TestLambdaHandler(unittest.TestCase):
    def test_lambda_handler(self):
        event = {}
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'Hello from Lambda!')


if __name__ == '__main__':
    unittest.main()