
from collections import namedtuple
import requests
import json


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

    @staticmethod
    def _convert_to_nameTuple(obj):
        def filter_keys(obj):
            new_obj = {}
            for k, v in obj.iteritems():
                if type(v) == dict:
                    v = filter_keys(v)
                elif type(v) == list:
                    if any(v) and type(v[0]) == dict:
                        v = [filter_keys(entry) for entry in v]
                new_obj[k if k != '_id' else 'id'] = v
            return new_obj

        def named_tuple_from_obj(obj):
            name = 'TrelloObject'
            return namedtuple(name, obj.keys())(*obj.values())

        return json.loads(
            json.dumps(filter_keys(obj)),
            object_hook=named_tuple_from_obj
        )

    def list_boards(self):
        resp = self._call_api('get', '/members/me/boards')
        return [
            self._convert_to_nameTuple(b)
            for b in resp.json()
        ]

    def list_board_members(self, board_id, params=None):
        resp = self._call_api(
            'get',
            '/boards/{}/members'.format(board_id),
            params=params
        )
        return [
            self._convert_to_nameTuple(b)
            for b in resp.json()
        ]

    def list_board_cards(self, board_id, params=None):
        resp = self._call_api(
            'get',
            '/boards/{}/cards'.format(board_id),
            params=params
        )
        return [
            self._convert_to_nameTuple(c)
            for c in resp.json()
        ]
