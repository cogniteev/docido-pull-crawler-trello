import os.path as osp
from setuptools import setup, find_packages

source = 'name'  # 'Trello' for instance
author = 'lol'  # Firstname Lastname
author_email = 'Lol'

# You should not have to edit content below but:
#
# - 'install_requires' section if you need additional dependencies
# - 'docido.plugins' entrypoints if you want to provide multiple crawlers.
#    Names don't matter, but values but references every modules
#    providing classes extending `docido_sdk.core.Component`

for v in [source, author, author_email]:
    if v.startswith('@'):
        raise Exception(
            "setup.py seems unconfigured. "
            "Please open and edit variables at the top of the file!")

module_name = 'dpc_' + source.lower()
module_dir = module_name.replace('-', '_').lower()
if not osp.isdir(module_dir):
    raise Exception(
        "Cannot find directory '{}'".format(module_dir) +
        " You may run the following shell command: " +
        " mv dpc_name {}".format(module_dir)
    )
project = 'docido-pull-crawler-' + source.lower()
root_url = 'https://bitbucket.org/cogniteev/' + project
# Extract version from module __init__.py
init_file = osp.join(module_dir, '__init__.py')
__version__ = None
with open(init_file) as istr:
    for l in istr:
        if l.startswith('__version__ = '):
            exec(l)
            break
version = '.'.join(map(str, __version__))

if __name__ == '__main__':
    exec(open('{}/__init__.py'.format(module_name)).read())
    setup(
        name=module_name,
        version=version,
        description='Docido Pull Crawler for ' + source,
        author=author,
        author_email=author_email,
        url=root_url,
        download_url=root_url + '/get/' + version,
        license='Apache license version 2.0',
        keywords='cogniteev docido crawler ' + source.lower(),
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Topic :: Software Development :: Libraries',
            'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Operating System :: OS Independent',
            'Natural Language :: English',
        ],
        packages=find_packages(exclude=['*.tests']),
        zip_safe=True,
        install_requires=[
            'docido-sdk>=0.0.19',
        ],
        entry_points="""
          [docido.plugins]
          {source}-pull-crawler = dpc_{source}.crawler
        """.format(source=source.lower())
    )
