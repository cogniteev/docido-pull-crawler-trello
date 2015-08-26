
import functools

from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler

from trello import TrelloClient
from dateutil import parser
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


def _create_trello_client(oauth_token):
    return TrelloClient(
        api_key=token.consumer_key,
        api_secret=token.token_secret,
        token=token.access_token
    )


def handle_board_cards(board_id, push_api=None, token=None, logger=None):
    trello = _create_trello_client(token)
    board = trello.get_board(board_id)
    docido_cards = []
    for card in board.get_cards():
        card.fetch_actions('createCard,copyCard,convertToCardFromCheckItem')
        if not any(card.actions):
            # no card creation event, author cannot get inferred
            continue
        date = parser.parse(card.actions[0]['date'])
        author = card.actions[0]['memberCreator']
        docido_card = {
            'attachments': [],
            'id': card.id,
            'title': card.name,
            'description': card.description,
            'date': time.mktime(date.utctimetuple()) * 1e3
            + date.microsecond / 1e3,
            'author': {
                # TODO: find a way to retrieve that information
            },
            'kind': 'note'
        }
        docido_cards.append(docido_card)
    push_api.push_cards(docido_cards)
    # print len(list(push_api.search_cards(None)))


class TrelloCrawler(Component):
    implements(ICrawler)

    def get_service_name(self):
        return 'trello'

    def get_account_login(self, token):
        return 'foo'

    def iter_crawl_tasks(self, index, token, logger, full=False):
        trello = _create_trello_client(token)
        return [
            functools.partial(
                handle_board_cards,
                board.id
            )
            for board in trello.list_boards()
        ][:1]
