"""Actual crawler core code"""

import functools
import mimetypes
import os.path as osp
import time

import markdown

from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler
from dateutil import parser
from dpc_trello.trello import TrelloClient


def create_trello_client(token):
    """ Create and return a trello client from a provided oauth token

    :param token: a docido_sdk specified OauthToken

    :return: a trello client instance
    """
    return TrelloClient(
        consumer_key=token.consumer_key,
        token=token.access_token
    )


def date_to_timestamp(str_date):
    """ Convert an str formatted date to an UNIX timestamp

    :param str str_date: An str formatted date

    :return: A valid UNIX timestamp
    :rtype: int
    """
    # As pylint cannot infer parser.parse return type because multiple return
    # types are possible the specific induced error is disabled
    # pylint: disable=no-member
    date = parser.parse(str_date)
    return int(
        time.mktime(date.utctimetuple()) * 1e3 + date.microsecond / 1e3
    )


def pick_preview(previews, full=False):
    """ Given a list of preview will pick the one matching specs or the closest

    The returned previews (if any) will respect the following conditions:
        * Biggest one among those which heights and width are lesser than 300
        * Smallest available one if no suitable candidate for first case is
        found

    :param list previews: A list of trello obtained item previews

    :return: The closest specs matching preview or None if no previews is
    available
    """
    def preview_size(preview):
        """ Compute a size for image by adding height and width so previews can
        easily be filtered and ordered

        :param previwe: A preview to compute size for

        :return: The computed size
        :rtype: int
        """
        return preview['height'] + preview['width']
    if not any(previews):
        return None
    candidates = [
        p for p in previews if p['height'] < 300 and p['width'] < 300
    ]
    if any(candidates):
        preview = max(candidates, key=preview_size)
    else:
        preview = min(previews, key=preview_size)
    if full:
        return preview
    return preview[u'url']


class file_type(object):
    TYPE_CHECK = {
        '3gp': 'video',
        'aaf': 'video',
        'aiff': 'sound',
        'ami': 'document',
        'ape': 'sound',
        'asc': 'document',
        'asf': 'video',
        'ast': 'sound',
        'au': 'sound',
        'avchd': 'video',
        'avi': 'video',
        'bmp': 'image',
        'bwf': 'sound',
        'cdda': 'sound',
        'csv': 'document',
        'doc': 'document',
        'docm': 'document',
        'docx': 'document',
        'dot': 'document',
        'dotx': 'document',
        'epub': 'document',
        'flac': 'sound',
        'flv': 'video',
        'gdoc': 'document',
        'gif': 'image',
        'gslides': 'slide',
        'jpeg': 'image',
        'jpg': 'image',
        'key': 'slide',
        'keynote': 'slide',
        'm4a': 'sound',
        'm4p': 'sound',
        'm4v': 'video',
        'mkv': 'video',
        'mng': 'video',
        'mov': 'video',
        'movie': 'video',
        'mp3': 'sound',
        'mp4': 'video',
        'mpe': 'video',
        'mpeg': 'video',
        'mpg': 'video',
        'nb': 'slide',
        'nbp': 'slide',
        'nsv': 'video',
        'odm': 'document',
        'odp': 'slide',
        'ods': 'document',
        'odt': 'document',
        'ott': 'document',
        'pages': 'document',
        'pdf': 'document',
        'pez': 'slide',
        'png': 'image',
        'pot': 'slide',
        'pps': 'slide',
        'ppt': 'slide',
        'pptx': 'slide',
        'rtf': 'document',
        'sdw': 'document',
        'shf': 'slide',
        'shn': 'sound',
        'show': 'slide',
        'shw': 'slide',
        'swf': 'video',
        'thmx': 'slide',
        'txt': 'document',
        'wav': 'sound',
        'wma': 'sound',
        'wmv': 'video',
        'wpd': 'document',
        'wps': 'document',
        'wpt': 'document',
        'wrd': 'document',
        'wri': 'document',
        'xls': 'document',
        'xlsx': 'document'
    }

    MIMETYPE_CHECK = {
        'image/png': 'image',
        'image/jpeg': 'image',
        'image/jpg': 'image',
        'image/gif': 'image',
        'application/pdf': 'document',
        'application/vnd.google-apps.document': 'document',
        'application/vnd.google-apps.spreadsheet': 'document',
        'application/vnd.google-apps.photo': 'image',
        'application/vnd.google-apps.drawing': 'image',
        'application/vnd.google-apps.presentation': 'slide',
        'application/vnd.google-apps.video': 'video'
    }

    @classmethod
    def guess_filetype(cls, filename, mime_type=None):
        if filename:
            _, extension = osp.splitext(filename)
            extension = extension[1:]
            return cls.TYPE_CHECK.get(extension, 'other')
        else:
            return cls.MIMETYPE_CHECK.get(mime_type, 'other')


def pick_mime_type(attachment):
    mime_type = attachment.get('mimeType')
    if mime_type is not None:
        return mime_type
    mime_type, _ = mimetypes.guess_type(attachment['name'])
    return mime_type


def pick_filetype(attachment):
    return file_type.guess_filetype(attachment['name'])


def thumbnail_from_avatar_hash(avatar_hash):
    """ Generate thumbnail url from avatar hash

    :param str avatar_hash: An avatar hash obtained from trello's API

    :return: the thumbnail url associated with the supplied hash
    :rtype: str
    """
    if not avatar_hash:
        return u''
    return u'https://trello-avatars.s3.amazonaws.com/{}/170.png'.format(
        avatar_hash
    )


def get_last_gen(push_api):
    """ Retrieve last stored generation from kv store

    :param push_api: The IndexAPI to use to query and retrieve last generation

    :return: Last stored generation for trello cards
    :rtype: int
    """
    last_gen = push_api.get_kv('last_gen')
    if last_gen is not None:
        return int(last_gen)
    return 0


def set_last_gen(push_api, last_gen):
    """ Set last kv stored generation to the supplied value


    :param push_api: The IndexAPI to use to set last generation
    :param int last_gen: The last generation to store in kv store
    """
    push_api.set_kv('last_gen', str(last_gen))


def generate_last_gen_query(last_gen):
    """ Generate an elasticsearch query to select all document from a previous
    generation

    :param int last_gen: The generation to select

    :return: A query to select all document with a generation <= to provided
    last_gen_value
    """
    return {
        'query': {
            'range': {
                'private.twitter_id': {
                    'lt': last_gen
                },
            },
        },
    }


def remove_old_gen(push_api, token, prev_results, logger):
    """ Create a docido_sdk compliant task to remove old documents from index
    (this function should be called for incremental crawls)

    :param push_api: The IndexAPI to use to set last generation
    :param token: an OauthToken object
    :param prev_results: Previous tasks results
    :param logger: A logging.logger instance
    """
    # prev result and token are not used but needed to work with docido SDK
    # pylint: disable=unused-argument
    logger.info('removing last generation items')
    last_gen = get_last_gen(push_api)
    last_gen_query = generate_last_gen_query(last_gen)
    push_api.delete_cards(last_gen_query)
    set_last_gen(push_api, last_gen + 1)


def handle_board_members(board_id, push_api, token, prev_result, logger):
    """ Function template to generate a trello board's members fetch from its
    ID. The docido_sdk compliant task should be created with functools.partial
    with a trello obtained board id.

    :param str board_id: the boards' to fetch members IDs
    :param push_api: The IndexAPI to use
    :param token: an OauthToken object
    :param prev_results: Previous tasks results
    :param logger: A logging.logger instance
    """
    # prev result is not used but needed to work with docido SDK
    # pylint: disable=unused-argument
    logger.info('fetching members for board: {}'.format(board_id))
    current_gen = get_last_gen(push_api) + 1
    trello = create_trello_client(token)
    members = []
    params = {'fields': 'all'}
    try:
        embed = markdown.markdown(member['bio'])
    except:
        embed = None

    for member in trello.list_board_members(board_id, params=params):
        members.append({
            'id': member['id'],
            'kind': u'contact',
            'title': member['fullName'],
            'date': None,
            'description': member['bio'],
            'embed': embed,
            'author': {
                'username': member['username'],
                'thumbnail': thumbnail_from_avatar_hash(member['avatarHash']),
                'name': member['fullName'],
            },
            'private': dict(twitter_id=current_gen),
            'attachments': [
                {
                    'type': u'link',
                    '_analysis': False,
                    'url': member['url'],
                    'title': 'View user on Trello',
                },
            ]
        })
    logger.info('indexing {} members for board: {}'.format(
        len(members), board_id))
    push_api.push_cards(members)


def handle_board_cards(board_id, push_api, token, prev_result, logger):
    """ Function template to generate a trello board's cards fetch from its
    ID. The docido_sdk compliant task should be created with functools.partial
    with a trello obtained board id.

    :param str board_id: the boards' to fetch members IDs
    :param push_api: The IndexAPI to use
    :param token: an OauthToken object
    :param prev_results: Previous tasks results
    :param logger: A logging.logger instance
    """
    # prev result is not used but needed to work with docido SDK
    # pylint: disable=unused-argument
    logger.info('fetching cards for board: {}'.format(board_id))
    current_gen = get_last_gen(push_api) + 1
    trello = create_trello_client(token)
    docido_cards = []
    params = {
        'actions': 'createCard,copyCard,convertToCardFromCheckItem',
        'attachments': 'true',
        'attachment_fields': 'all',
        'members': 'true',
        'member_fields': 'all'
    }
    url_attachment_label = u'View {kind} {name} on Trello'

    for card in trello.list_board_cards(board_id, params=params):
        if not any(card['actions']):
            # no card creation event, author cannot get inferred
            continue
        author = card['actions'][0]['memberCreator']
        author_thumbnail = thumbnail_from_avatar_hash(author.get('avatarHash'))
        labels = [l['name'] for l in card['labels']]
        labels = filter(lambda l: any(l), labels)
        try:
            embed = markdown.markdown(card['desc'])
        except:
            embed = None
        docido_card = {
            'attachments': [
                {
                    'type': u'link',
                    'url': card['shortUrl'],
                    '_analysis': False,
                    'title': 'View card on Trello'
                }
            ],
            'id': card['id'],
            'title': card['name'],
            'private': dict(twitter_id=current_gen),
            'description': card['desc'],
            'embed': embed,
            'date': date_to_timestamp(card['dateLastActivity']),
            'favorited': card['subscribed'],
            'created_at': date_to_timestamp(card['actions'][0]['date']),
            'author': {
                'name': author['fullName'],
                'username': author['username'],
                'thumbnail': author_thumbnail,
            },
            'labels': labels,
            'flags': 'closed' if card.get('closed', False) else 'open',
            'kind': u'note'
        }

        for kind, link in card['actions'][0].get('data', {}).iteritems():
            if kind != 'card' and 'shortLink' in link:
                docido_card['attachments'].append(dict(
                    type=u'link',
                    _analysis=False,
                    url='https://trello.com/{kind}/{url}'.format(
                        kind=kind,
                        url=link['shortLink']
                    ),
                    title=url_attachment_label.format(kind=kind,
                                                      name=link['name'])
                ))
                if kind == 'board':
                    docido_card['attachments'].append(dict(
                        type=u'notebook',
                        name=link['name']
                    ))

        docido_card['attachments'].extend([
            {
                'type': u'file',
                'origin_id': a['id'],
                'title': a['name'],
                'url': a['url'],
                'date': date_to_timestamp(a['date']),
                'size': a['bytes'],
                'preview': pick_preview(a['previews']),
                'mime_type': pick_mime_type(a),
                'filetype': pick_filetype(a),
            }
            for a in card['attachments']
        ])
        docido_card['attachments'].extend([
            dict(type=u'tag', name=label)
            for label in labels
        ])
        docido_card['to'] = [
            {
                'name': m['fullName'],
                'username': m['username'],
                'thumbnail': thumbnail_from_avatar_hash(m['avatarHash'])
            }
            for m in card['members']
        ]
        docido_cards.append(docido_card)
    logger.info('indexing {} cards for board: {}'.format(
        len(docido_cards), board_id))
    push_api.push_cards(docido_cards)


class TrelloCrawler(Component):
    """ The ICrawler implementing class
    """
    # implements Icrawler Interface to make it available in the environnment
    implements(ICrawler)
    service_name = 'trello'

    def get_service_name(self):
        """ Simply return the service_name associated with the crawler

        :return: the service name
        :rtype: str
        """
        return self.service_name

    def iter_crawl_tasks(self, index, token, logger, full=False):
        """ Method responsible of generating all tasks needed for trello fetch

        :param index: The IndexAPI to use
        :param token: an OauthToken object
        :param logger: A logging.logger instance
        :param full: Whether to perform a full or incremental crawl

        :return: A dictionnary containing a "tasks" and an optionnal "epilogue"
        fields (see docido_sdk)
        :rtype: dict
        """
        # index is not used but needed to work with docido SDK
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        logger.info('generating crawl tasks')
        trello = create_trello_client(token)
        boards = trello.list_boards()
        crawl_tasks = {
            'tasks': []
        }
        fetch_cards_tasks = [
            functools.partial(
                handle_board_cards,
                board['id']
            )
            for board in boards
        ]
        fetch_board_members = [
            functools.partial(
                handle_board_members,
                board['id']
            )
            for board in boards
        ]
        crawl_tasks['tasks'].extend(fetch_cards_tasks)
        crawl_tasks['tasks'].extend(fetch_board_members)
        logger.info('{} tasks generated'.format(len(crawl_tasks['tasks'])))
        if not full:
            crawl_tasks['epilogue'] = remove_old_gen
        return crawl_tasks
