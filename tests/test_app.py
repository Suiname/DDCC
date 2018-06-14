import unittest
import json
from app import create_response, get_json
from unittest.mock import patch

mock_get_repsonse = {'mock': True}

def mock_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'http://badurl.com':
        return MockResponse(None, 404)

    return MockResponse(mock_get_repsonse, 200)

class AppTests(unittest.TestCase):
  def test_create_json(self):
    assert callable(create_response)
    response = create_response()
    expected_response = {
      'account_size': 0,
      'commits': 0,
      'languages': {
        'count': 0,
        'list': []
      },
      'open_issues': 0,
      'repo_count': {
        'forked': 0,
        'original': 0
      },
      'repo_topics': {
        'count': 0,
        'list': []
      },
      'repo_watchers': 0,
      'stars': {
        'given': 0,
        'received': 0
      },
      'user_watchers': 0
    }
    self.assertDictEqual(response, expected_response)


  @patch('requests.get', side_effect=mock_requests_get)
  def test_requests(self, request_mock):
    assert callable(get_json)
    url = 'https://someurl.com'
    result = get_json(url)
    self.assertDictEqual(result, mock_get_repsonse)
    