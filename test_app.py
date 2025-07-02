import unittest
import io
from unittest.mock import patch
from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_upload_file(self):
       
        data = {
            'file': (io.BytesIO(b"This is a test document for upload."), 'test.txt')
        }
        response = self.app.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn('doc_id', response.get_json())
        self.assertIn('num_chunks', response.get_json())

    @patch('chroma_setup.query_similar')
    def test_query_vector_store(self, mock_query_similar):
        
        mock_query_similar.return_value = {
            'documents': [["Relevant chunk 1", "Relevant chunk 2"]],
            'ids': [["docid_0", "docid_1"]]
        }
        response = self.app.post('/query', json={'text': 'test query'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('documents', response.get_json())

    @patch('requests.post')
    def test_generate_gemini(self, mock_post):
      
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "Gemini response text"}]}}
            ]
        }
        response = self.app.post('/generate', json={'prompt': 'Say hello'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('response', response.get_json())
        self.assertEqual(response.get_json()['response'], 'Gemini response text')

if __name__ == '__main__':
    unittest.main() 