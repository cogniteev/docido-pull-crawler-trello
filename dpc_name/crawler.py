
from docido_sdk.core import Component, implements
from docido_sdk.crawler import ICrawler


class Crawler(Component):
    implements(ICrawler)

    def get_service_name(self):
        return '@NAME@'  # same as settings.yml in 'pull_crawlers:crawlers'

    def iter_crawl_tasks(self, index, token, config, logger):
        """Split the crawl in smaller independant actions,
        and returns them for delayed execution.

        :param docido_sdk.push.api.IndexAPI: index
          To manipulate Docido index

        :param docido_sdk.oauth.OAuthToken oauth_token:
          OAuth credentials

        :param docido_sdk.toolbox.collections_ext.nameddict config:
          crawl configuration. Every crawler may expect the following
          keys to be set:
          - bool `full`:
              whether the entire account must be pushed or only
              changes that occured since previous crawl. Default
              value is `False`.

        :param logging.Logger logger:
          to emit messages

        :return: a dictionary instance containing the following keys:

        - 'tasks' (mandatory): generator of :py:func:`functools.partial` tasks
          to execute to perform the account synchronization.
          partial objects may accept the following arguments:

              - push_api (:py:class:`docido_sdk.push.IndexAPI`)
              - oauth_token (:py:class:`docido_sdk.oauth.OAuthToken`)
              - previous_result (:py:class:`object`) previous task result,
                if any.
              - config
                (:py:class:`docido_sdk.toolbox.collections_ext.nameddict`)
                crawler configuration
              - logger (:py:class:`logging.Logger`)

          If a list of tasks is returned, then they are executed concurrently,
          and the tasks order is not honored.
          If a list of list of tasks is returned, then every list is executed
          concurrently and task order among a list is respected. the
          `prev_result` parameter of a sub-task will be given what the
          previous sub-task of the same list returns. `None` is given to the
          first task of every sequence.

        - 'epilogue' (optional): a :py:func:`functools.partial` instance
          to execute when all sub-tasks have been executed. The partial
          instance may accept the following arguments:

              - push_api (:py:class:`docido_sdk.push.IndexAPI`)
              - oauth_token (:py:class:`docido_sdk.oauth.OAuthToken`)
              - results (a result or a list of results)
                providing what the sub-tasks returned.
              - config
                (:py:class:`docido_sdk.toolbox.collections_ext.nameddict`)
                crawler configuration
              - logger (:py:class:`logging.Logger`)

        - 'max_concurrent_tasks' (optional): an integer greater than 0 and
          less than 10 (the default value) used to limit number of tasks
          executed concurrently.

        A task cannot be instance, class, or static method
        of a :py:func:`docido_sdk.core.Component` object.
        Therefore you may provide functions defined outside
        your crawler class definition.
        """
