# Docico pull crawler trello

[![Build Status](https://travis-ci.org/cogniteev/docido-pull-crawler-trello.svg?branch=develop)](https://travis-ci.org/cogniteev/docido-pull-crawler-trello)
[![Coverage Status](https://coveralls.io/repos/cogniteev/docido-pull-crawler-trello/badge.svg?branch=develop&service=github)](https://coveralls.io/github/cogniteev/docido-pull-crawler-trello?branch=develop)
[![Code Climate](https://codeclimate.com/github/cogniteev/docido-pull-crawler-trello/badges/gpa.svg)](https://codeclimate.com/github/cogniteev/docido-pull-crawler-trello)
[![Code Health](https://landscape.io/github/cogniteev/docido-pull-crawler-trello/develop/landscape.svg?style=flat)](https://landscape.io/github/cogniteev/docido-pull-crawler-trello/develop)

A trello crawler to make trello data available in
[Docido](http://www.docido.com/).
The development is done using the
[docido-python-sdk](https://github.com/cogniteev/docido-python-sdk).

Crawlers documentation is available
[here](https://cogniteev.github.io/docido-python-sdk/)

# Prerequisites

As we need to make some real requests to elasticsearch, a real elasticsearch
must be available either running on the machine or in a docker container.
The base configuration is located in the ```settings-es.yml``` file and can be
rewritten be setting the ```ELASTICSEARCH_HOST``` environnment variable.

# Run the crawler code

The docido's SDK come with a script that will build the required environnment
(as defined in the ```settings-es.yml``` file) and attempt to run the tasks
generated in the crawler.

To install the docido SDK simply run ```$ pip install -U .``` as its a
dependency of this project. Then a dcc-run script will be available (if not try
to run ```$ hash -r```, to update the shell paths).

# Tests & Code quality

Some unit tests and code linters are available and configured for the project
and can easily be run by *pip installing* tox and running it.


Please refer to

for further instructions.
