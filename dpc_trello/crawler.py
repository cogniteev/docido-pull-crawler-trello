
import functools

from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler
from dateutil import parser
from trello import TrelloClient

import time


"""
FIXME: for now it is not possible to pass an instance function
nor a static function of class TrelloCrawler in iter_crawl_tasks
parameters because Celery is not able to serialize it

  File "/goinfre/tristan/src/bitbucket/docido-contrib-crawlers/.env/lib/python2.7/site-packages/kombu/serialization.py"
  , line 357, in pickle_dumps
  return dumper(obj, protocol=pickle_protocol)
EncodeError: Can't pickle <type 'instancemethod'>: attribute lookup __builtin__.instancemethod failed
"""


def _create_trello_client(token):
    return TrelloClient(
        consumer_key=token.consumer_key,
        token=token.access_token
    )


def _date_to_timestamp(str_date):
    date = parser.parse(str_date)
    return int(time.mktime(date.utctimetuple()) * 1e3 + date.microsecond / 1e3)


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


def _get_last_gen(push_api):
    return push_api.get_kv('last_gen') or 0


def _set_last_gen_query(push_api, last_gen):
    push_api.set_kv('last_gen', last_gen)


def _generate_last_gen_query(last_gen):
    return {
        'query': {
            'range': {
                'gen': {
                    'gt': last_gen
                }
            }
        }
    }


def remove_old_gen(push_api=None, token=None, logger=None):
    last_gen = _get_last_gen(push_api)
    last_gen_query = _generate_last_gen_query(last_gen)
    push_api.delete_cards(last_gen_query)
    _set_last_gen_query(push_api, last_gen + 1)


def handle_board_members(board_id, push_api=None, token=None, logger=None):
    current_gen = _get_last_gen(push_api) + 1
    trello = _create_trello_client(token)
    members = []
    params = {'fields': 'all'}

    for member in trello.list_board_members(board_id, params=params):
        members.append({
            'id': member.id,
            'kind': 'contact',
            'description': member.bio,
            'name': member.fullName,
            'gen': current_gen,
            'username': member.username,
            'thumbnail': _thumbnail_from_avatarHash(member.avatarHash)
        })
    push_api.push_cards(members)


def handle_board_cards(board_id, push_api=None, token=None, logger=None):
    current_gen = _get_last_gen(push_api) + 1
    trello = _create_trello_client(token)
    docido_cards = []
    params = {
        'actions': 'createCard,copyCard,convertToCardFromCheckItem',
        'attachments': 'true',
        'attachment_fields': 'all',
        'members': 'true',
        'gen': current_gen,
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
            'favorited': card.subscribed,
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
        crawl_tasks.extend(fetch_cards_tasks)
        crawl_tasks.extend(fetch_board_members)
        if full:
            return crawl_tasks
        else:
            return crawl_tasks, remove_old_gen

    def clear_account(self, index, token, logger):
        """ Remove account data (key-value store and indexed data) """
