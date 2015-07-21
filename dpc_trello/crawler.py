
import functools

from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler

"""
FIXME: for now it is not possible to pass an instance function
nor a static function of class TrelloCrawler in iter_crawl_tasks
parameters because Celery is not able to serialize it

  File "/goinfre/tristan/src/bitbucket/docido-contrib-crawlers/.env/lib/python2.7/site-packages/kombu/serialization.py"
, line 357, in pickle_dumps
    return dumper(obj, protocol=pickle_protocol)
EncodeError: Can't pickle <type 'instancemethod'>: attribute lookup __builtin__.instancemethod failed
"""

def subtask(index=None, oauth_token=None, foo=None, bar=None):
    print 'start sub-task'
    print '  index=%r' % index
    print '  oauth_token=%r' % oauth_token
    print '  foo=%r' % foo
    print '  bar=%r' % bar

class TrelloCrawler(Component):
    implements(ICrawler)

    def get_service_name(self):
        return 'trello'

    def get_account_login(self, oauth_token):
        return 'foo'

    def iter_crawl_tasks(self, index, oauth_token, full=False):
        print 'start indexing'
        print '  index=%r' % index
        print '  oauth_token=%r' % oauth_token
        print '  full=%r' % full
        return [
            functools.partial(subtask, foo='fooparam1', bar='barparam1'),
            functools.partial(subtask, foo='fooparam2', bar='barparam2'),
        ]


