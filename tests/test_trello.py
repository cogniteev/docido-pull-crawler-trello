import unittest
import mock
from dpc_trello.trello import TrelloClient, TrelloClientException


# Patch request.request to mock HTTP responses, an extra parameter will be
# supplied to each test case
@mock.patch('requests.request')
class TestTrelloClient(unittest.TestCase):
    TEST_CONSUMER_KEY = 'a_consumer_key'
    TEST_TOKEN = 'a_token'

    def test_invalid_status(self, mocked_request):
        mocked_request.return_value.status_code = 400
        client = TrelloClient(self.TEST_CONSUMER_KEY, self.TEST_TOKEN)
        with self.assertRaises(TrelloClientException):
            client.list_boards()

    def test_boards_listing(self, mocked_request):
        mocked_request.return_value.status_code = 200
        mocked_request.return_value.json = lambda: [
            {
                'id': 'toto'
            }
        ]
        client = TrelloClient(self.TEST_CONSUMER_KEY, self.TEST_TOKEN)
        boards = client.list_boards()
        self.assertEqual(1, len(boards))
        self.assertEqual(boards[0]['id'], 'toto')
        mocked_request.assert_called_once_with(
            data=None,
            method='get',
            params={'token': 'a_token', 'key': 'a_consumer_key'},
            url='https://api.trello.com/1/members/me/boards'
        )

    def test_board_members_listing(self, mocked_request):
        mocked_request.return_value.status_code = 200
        mocked_request.return_value.json = lambda: [
            {
                'id': 'toto',
                'data': {
                    'a_list': [{
                        'foo': 'bar'
                    }]
                }
            }
        ]
        client = TrelloClient(self.TEST_CONSUMER_KEY, self.TEST_TOKEN)
        boards = client.list_board_members('test_board')
        self.assertEqual(1, len(boards))
        self.assertEqual(boards[0]['id'], 'toto')
        mocked_request.assert_called_once_with(
            data=None,
            method='get',
            params={'token': 'a_token', 'key': 'a_consumer_key'},
            url='https://api.trello.com/1/boards/test_board/members'
        )

    def test_board_cards_listing(self, mocked_request):
        mocked_request.return_value.status_code = 200
        mocked_request.return_value.json = lambda: [
            {
                'id': 'toto',
                'an_empty_list': []
            }
        ]
        client = TrelloClient(self.TEST_CONSUMER_KEY, self.TEST_TOKEN)
        boards = client.list_board_cards('test_board')
        self.assertEqual(1, len(boards))
        self.assertEqual(boards[0]['id'], 'toto')
        mocked_request.assert_called_once_with(
            data=None,
            method='get',
            params={'token': 'a_token', 'key': 'a_consumer_key'},
            url='https://api.trello.com/1/boards/test_board/cards'
        )
