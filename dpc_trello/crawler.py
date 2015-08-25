
import functools

from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler

from trello import TrelloClient

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
        api_key='AN_API_KEY',
        api_secret='AN_API_SECRET',
        token=oauth_token
    )


def handle_board_cards(board_id, index=None, oauth_token=None):
    trello = _create_trello_client(oauth_token)
    board = trello.get_board(board_id)
    for card in board.get_cards():
        docido_card = {
            'id': card.id,
            'title': card.name,
            'description': card.description,
            'author': {
                # TODO: find a way to retrieve that information
            },
            'kind': 'activity'
        }
        import json
        print json.dumps(docido_card, indent=1)


class TrelloCrawler(Component):
    implements(ICrawler)

    def get_service_name(self):
        return 'trello'

    def get_account_login(self, oauth_token):
        return 'foo'

    def iter_crawl_tasks(self, index, token, logger, full=False):
        trello = _create_trello_client(token)
        return [
            functools.partial(
                handle_board_cards,
                board.id,
                index=index,
                oauth_token=oauth_token
            )
            for board in trello.list_boards()
        ][:1]
