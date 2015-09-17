
from dpc_trello.crawler import (
    TrelloCrawler,
    handle_board_members,
    handle_board_cards,
    pick_preview,
    get_last_gen,
    set_last_gen,
    remove_old_gen
)
from dpc_trello.trello import TrelloClient as client
from docido_sdk.core import ComponentManager

import unittest
import mock
import types
import datetime


class TestTrelloCrawler(unittest.TestCase):

    @mock.patch.object(client, 'list_boards')
    def test_crawler_tasks_generation(self, list_boards):
        list_boards.return_value = [{'id': 'test'}]
        logger = mock.Mock()
        token = mock.Mock()
        push_api = mock.Mock()
        crawler = TrelloCrawler(ComponentManager())

        # Full Crawl
        tasks = crawler.iter_crawl_tasks(push_api, token, logger, full=True)
        self.assertIn('tasks', tasks)
        self.assertEqual(2, len(tasks['tasks']))

        # Incremental Crawl
        tasks_and_epilogue = crawler.iter_crawl_tasks(push_api, token, logger)
        self.assertIn('tasks', tasks_and_epilogue)
        self.assertEqual(2, len(tasks['tasks']))
        self.assertIn('epilogue', tasks_and_epilogue)
        self.assertIsInstance(
            tasks_and_epilogue['epilogue'],
            types.FunctionType
        )

    def test_pick_preview(self):
        self.assertEqual(None, pick_preview([]))

        preview_with_candidates = [
            {'height': 250, 'width': 250},
            {'height': 299, 'width': 299},
            {'height': 301, 'width': 301},
        ]
        self.assertDictEqual(
            pick_preview(preview_with_candidates),
            {'height': 299, 'width': 299}
        )

        preview_without_candidates = [
            {'height': 350, 'width': 350},
            {'height': 400, 'width': 400},
        ]
        self.assertDictEqual(
            pick_preview(preview_without_candidates),
            {'height': 350, 'width': 350}
        )

    def test_crawler_service_name(self):
        crawler = TrelloCrawler(ComponentManager())
        self.assertEqual(crawler.get_service_name(), 'trello')

    def test_get_last_gen(self):
        push_api = mock.Mock()
        push_api.get_kv.return_value = 1
        self.assertEqual(get_last_gen(push_api), 1)
        push_api.get_kv.assert_called_once_with('last_gen')

        push_api.reset_mock()
        push_api.get_kv.return_value = None
        self.assertEqual(get_last_gen(push_api), 0)
        push_api.get_kv.assert_called_once_with('last_gen')

    def test_set_last_gen(self):
        push_api = mock.Mock()
        set_last_gen(push_api, 1)
        push_api.set_kv.assert_called_once_with('last_gen', 1)

    def test_remove_old_gen(self):
        logger = mock.Mock()
        token = mock.Mock()
        push_api = mock.Mock()
        push_api.get_kv.return_value = 0

        remove_old_gen(push_api, token, None, logger)

        push_api.get_kv.assert_called_once_with('last_gen')
        push_api.set_kv.assert_called_once_with('last_gen', 1)
        push_api.delete_cards.assert_called_once_with({
            'query': {
                'range': {
                    'gen': {
                        'lt': 0
                    }
                }
            }
        })

    @mock.patch.object(client, 'list_board_members')
    def test_crawler_fetch_board_members(self, list_board_members):
        mocked_members = [
            {
                'id': 'aMemberId',
                'bio': 'YOLO',
                'fullName': 'aFullName',
                'username': 'aUserName',
                'avatarHash': None
            }
        ]
        logger = mock.Mock()
        token = mock.Mock()
        push_api = mock.Mock()
        push_api.get_kv.return_value = 0
        list_board_members.return_value = mocked_members

        handle_board_members('aBoard', push_api, token, None, logger)
        list_board_members.assert_called_once_with(
            'aBoard', params={'fields': 'all'}
        )

        calls = push_api.push_cards.mock_calls
        self.assertEqual(len(calls), 1)
        # call[0] is the first and unique call, it is a tuple of the form:
        # (name, args, kwargs), so it's second member is the args list
        # we'll introspect the first and only argument supplied to push_cards
        # in order to do that we then retrieve calls[0][1][0]
        call_arg = calls[0][1][0]
        first_card = call_arg[0]
        self.assertEqual(first_card['thumbnail'], None)
        # last_gen + 1
        self.assertEqual(first_card['gen'], 1)

    @mock.patch.object(client, 'list_board_cards')
    def test_crawler_fetch_board_cards(self, list_cards):
        date = str(datetime.datetime.now())

        logger = mock.Mock()
        token = mock.Mock()
        push_api = mock.Mock()
        mocked_cards = [
            {
                'shortUrl': 'aShortUrl',
                'email': 'anEmail',
                'id': '1234',
                'name': 'aName',
                'desc': 'aDesc',
                'dateLastActivity': date,
                'subscribed': True,
                'actions': [
                    {
                        'date': date,
                        'memberCreator': {
                            'fullName': 'aFullName',
                            'username': 'aUserName',
                            'avatarHash': 'hsah'
                        }
                    }
                ],
                'fullName': 'aFullName',
                'username': 'aUsername',
                'labels': [{'name': 'foo'}, {'name': 'bar'}],
                'attachments': [
                    {
                        'id': 'anId',
                        'bytes': '\x13',
                        'name': 'aName',
                        'title': 'aTitle',
                        'url': 'anUrl',
                        'date': date,
                        'size': 1345,
                        'previews': []
                    }
                ],
                'members': [
                    {
                        'fullName': 'aFullName',
                        'username': 'aUserName',
                        'avatarHash': 'hsah'
                    }
                ],
            },
            # This card should be skipped and thus do not requires to be
            # complete
            {'actions': []}
        ]

        push_api.get_kv.return_value = 0
        list_cards.return_value = mocked_cards

        handle_board_cards('test_boards', push_api, token, None, logger)

        list_cards.assert_called_once_with('test_boards', params={
            'attachment_fields': 'all',
            'members': 'true',
            'attachments': 'true',
            'actions': 'createCard,copyCard,convertToCardFromCheckItem',
            'member_fields': 'all'
        })
        calls = push_api.push_cards.mock_calls
        self.assertEqual(len(calls), 1)
        # call[0] is the first and unique call, it is a tuple of the form:
        # (name, args, kwargs), so it's second member is the args list
        # we'll introspect the first and only argument supplied to push_cards
        # in order to do that we then retrieve calls[0][1][0]
        call_arg = calls[0][1][0]
        first_card = call_arg[0]
        self.assertEqual(len(first_card['attachments']), 2)
        self.assertEqual(len(first_card['to']), 2)
        self.assertEqual(first_card['labels'], ['foo', 'bar'])
        # last_gen + 1
        self.assertEqual(first_card['gen'], 1)
