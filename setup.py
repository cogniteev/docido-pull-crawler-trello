from setuptools import setup, find_packages

source = 'Trello'
module_name = 'dpc_' + source.lower()
project = 'docido-pull-crawler-' + source.lower()
root_url = 'https://bitbucket.org/cogniteev/' + project
author = 'Firstname Lastname'

if __name__ == '__main__':
    exec(open('{}/__init__.py'.format(module_name)).read())
    setup(
        name=module_name,
        version=__version__,
        description='Docido Pull Crawler for ' + source,
        author=author,
        author_email='john.doe@acme.com',
        url=root_url,
        download_url=root_url + '/tarball/v' + __version__,
        license='Apache license version 2.0',
        keywords='cogniteev docido crawler ' + source.lower(),
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Topic :: Software Development :: Libraries',
            'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Operating System :: OS Independent',
            'Natural Language :: English',
        ],
        packages=find_packages(exclude=['*.tests']),
        #test_suite='docido.sdk.test.suite',
        zip_safe=True,
        install_requires=[
            'setuptools>=0.6',
        ]
    )
