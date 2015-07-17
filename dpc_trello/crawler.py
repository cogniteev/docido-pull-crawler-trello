
from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler

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
            functools.partial(self.subtask, foo='fooparam1', bar='barparam1'),
            functools.partial(self.subtask, foo='fooparam2', bar='barparam2'),
        ]

    def subtask(self, index=None, oauth_token=None, foo=None, bar=None):
        print 'start sub-task'
        print '  index=%r' % index
        print '  oauth_token=%r' % oauth_token
        print '  foo=%r' % foo
        print '  bar=%r' % bar
