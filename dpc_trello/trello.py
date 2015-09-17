
import requests


class TrelloClientException(Exception):
    pass


class TrelloClient(object):

    def __init__(self, consumer_key, token):
        self.__consumer_key = consumer_key
        self.__token = token
        self.__api_url = 'https://api.trello.com/1'

    def _call_api(self, method, path, params=None, data=None):
        request_params = {
            'key': self.__consumer_key,
            'token': self.__token
        }
        request_params.update(params if params else {})
        response = requests.request(
            method=method,
            url=self.__api_url + path,
            params=request_params,
            data=data
        )
        if response.status_code is not 200:
            raise TrelloClientException(
                'API answered with {} status_code'.format(response.status_code)
            )
        return response

    def list_boards(self):
        resp = self._call_api('get', '/members/me/boards')
        return resp.json()

    def list_board_members(self, board_id, params=None):
        resp = self._call_api(
            'get',
            '/boards/{}/members'.format(board_id),
            params=params
        )
        return resp.json()

    def list_board_cards(self, board_id, params=None):
        resp = self._call_api(
            'get',
            '/boards/{}/cards'.format(board_id),
            params=params
        )
        return resp.json()
