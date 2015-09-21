"""Basic trello client"""

import requests


class TrelloClientException(Exception):
    """An exception to throw for trello errors"""
    pass


class TrelloClient(object):
    """ A basic client for trello REST API based on requests
    """

    def __init__(self, consumer_key, token):
        """ Create a new trello client with given credentials

        :param consumer_key: The trello API consumer key to use
        :param token: A docido SDK defined token
        """
        self.__consumer_key = consumer_key
        self.__token = token
        self.__api_url = 'https://api.trello.com/1'

    def _call_api(self, method, path, params=None, data=None):
        """ Perform an API call

        :param method: The http method to use
        :param path: The ressources REST path
        :param params: url params to pass in the call
        :param data: HTTP payload to send
        """
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
        """ List all boards the user have access to
        """
        resp = self._call_api('get', '/members/me/boards')
        return resp.json()

    def list_board_members(self, board_id, params=None):
        """ List all members of a given board

        :param board_id: The board's to list members from ID
        :param params: Parameters as listed on the trello API documentation
        """
        resp = self._call_api(
            'get',
            '/boards/{}/members'.format(board_id),
            params=params
        )
        return resp.json()

    def list_board_cards(self, board_id, params=None):
        """ List all cards of a given board

        :param board_id: The board's to list cards from ID
        :param params: Parameters as listed on the trello API documentation
        """
        resp = self._call_api(
            'get',
            '/boards/{}/cards'.format(board_id),
            params=params
        )
        return resp.json()
