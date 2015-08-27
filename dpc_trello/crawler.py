
import functools

from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler

from dateutil import parser
from collections import namedtuple
import time
import requests
import json


"""
FIXME: for now it is not possible to pass an instance function
nor a static function of class TrelloCrawler in iter_crawl_tasks
parameters because Celery is not able to serialize it

  File "/goinfre/tristan/src/bitbucket/docido-contrib-crawlers/.env/lib/python2.7/site-packages/kombu/serialization.py"
  , line 357, in pickle_dumps
  return dumper(obj, protocol=pickle_protocol)
EncodeError: Can't pickle <type 'instancemethod'>: attribute lookup __builtin__.instancemethod failed
"""


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
            print response.text
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


def _create_trello_client(token):
    return TrelloClient(
        consumer_key=token.consumer_key,
        token=token.access_token
    )


def _date_to_timestamp(str_date):
    date = parser.parse(str_date)
    return time.mktime(date.utctimetuple()) * 1e3 + date.microsecond / 1e3


def _pick_preview(previews):
    def preview_size(preview):
        return preview.height + p.width
    if not any(previews):
        return None
    candidates = [p for p in previews if p.height < 300 and p.width < 300]
    if any(candidates):
        return max(candidates, key=preview_size)
    else:
        return min(previews, key=preview_size)


def _thumbnail_from_avatarHash(avatar):
    if not avatar:
        return
    return 'https://trello-avatars.s3.amazonaws.com/' + avatar + '/170.png'


def handle_board_members(board_id, push_api=None, token=None, logger=None):
    trello = _create_trello_client(token)
    members = []
    params = {'fields': 'all'}

    for member in trello.list_board_members(board_id, params=params):
        members.append({
            'id': member.id,
            'kind': 'contact',
            'description': member.bio,
            'name': member.fullName,
            'username': member.username,
            'thumbnail': _thumbnail_from_avatarHash(member.avatarHash)
        })
    push_api.push_cards(members)


def handle_board_cards(board_id, push_api=None, token=None, logger=None):
    trello = _create_trello_client(token)
    docido_cards = []
    params = {
        'actions': 'createCard,copyCard,convertToCardFromCheckItem',
        'attachments': 'true',
        'attachment_fields': 'all',
        'members': 'true',
        'member_fields': 'all'
    }

    for card in trello.list_board_cards(board_id, params=params):
        if not any(card.actions):
            # no card creation event, author cannot get inferred
            continue
        author = card.actions[0].memberCreator
        docido_card = {
            'attachments': [
                {
                    'type': 'link',
                    'url': card.shortUrl
                }
            ],
            'to': [
                {'username': card.email}
            ],
            'id': card.id,
            'title': card.name,
            'description': card.desc,
            'date': _date_to_timestamp(card.dateLastActivity),
            'created_at': _date_to_timestamp(card.actions[0].date),
            'author': {
                'name': author.fullName,
                'username': author.username
            },
            'favorited': card.subscribed,
            'labels': [l.name for l in card.labels],
            'kind': 'note'
        }
        formatted_attachments = [
            {
                'type': 'link',
                'title': a.name,
                'url': a.url,
                'date': _date_to_timestamp(a.date),
                'size': a.bytes,
                'preview': _pick_preview(a.previews)
            }
            for a in card.attachments
        ]
        formatted_members = [
            {
                'name': m.fullName,
                'username': m.username,
                'thumbnail': _thumbnail_from_avatarHash(m.avatarHash)
            }
            for m in card.members
        ]
        docido_card['attachments'].extend(formatted_attachments)
        docido_card['to'].extend(formatted_members)
        docido_cards.append(docido_card)
    push_api.push_cards(docido_cards)


class TrelloCrawler(Component):
    implements(ICrawler)

    def get_service_name(self):
        return 'trello'

    def get_account_login(self, token):
        return 'foo'

    def iter_crawl_tasks(self, index, token, logger, full=False):
        trello = _create_trello_client(token)
        boards = trello.list_boards()
        crawl_tasks = []
        fetch_cards_tasks = [
            functools.partial(
                handle_board_cards,
                board.id
            )
            for board in boards
        ]
        fetch_board_members = [
            functools.partial(
                handle_board_members,
                board.id
            )
            for board in boards
        ]
        # crawl_tasks.extend(fetch_cards_tasks)
        crawl_tasks.extend(fetch_board_members)
        return crawl_tasks
