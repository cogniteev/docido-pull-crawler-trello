
import functools

from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler


class Crawler(Component):
    implements(ICrawler)

    def get_service_name(self):
        return '@NAME@' # same as settings.yml in 'pull_crawlers:crawlers'

    def iter_crawl_tasks(self, index, token, logger, full=False):
        """Split the crawl in smaller independant actions,
        and returns them for delayed execution.

        :param docido_sdk.push.api.IndexAPI: index
          To manipulate Docido index

        :param docido_sdk.oauth.OAuthToken oauth_token:
          OAuth credentials

        :param logging.Logger logger:
          to emit messages

        :param bool full:
          whether the entire account must be pushed or only
          changes that occured since previous crawl.

        :return: a dictionary instance containing the following keys:

        - 'tasks' (mandatory): generator of :py:func:`functools.partial` tasks
          to execute to perform the account synchronization.
          partial objects may accept 3 arguments:

              - push_api (:py:class:`docido_sdk.push.IndexAPI`)
              - oauth_token (:py:class:`docido_sdk.oauth.OAuthToken`)
              - previous_result (:py:class:`object`) previous task result,
                if any.
              - logger (:py:class:`logging.Logger`)

        - 'epilogue' (optional): a :py:func:`functools.partial` instance
          to execute when all sub-tasks have been executed. The partial
          instance may accept the following arguments:

              - push_api (:py:class:`docido_sdk.push.IndexAPI`)
              - oauth_token (:py:class:`docido_sdk.oauth.OAuthToken`)
              - results (a result or a list of results)
              providing what the sub-tasks returned.
              - logger (:py:class:`logging.Logger`)

        A task cannot be instance, class, or static method
        of a :py:func:`docido_sdk.core.Component` object.
        Therefore you may provide functions defined outside
        your crawler class definition.
        """

    def clear_account(self, index, token, logger):
        """ Remove account data (key-value store and indexed data) """
        index.delete_cards()
        index.delete_thumbnails()
        index.delete_kvs()
