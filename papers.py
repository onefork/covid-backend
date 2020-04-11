#!/usr/bin/env python

from interactive_search import cache_corpus
from interactive_search import EMBEDDINGS_PATH
from interactive_search import MODEL_PATH
from interactive_search import CORPUS_PATH
from interactive_search import ask_question, COVID_BROWSER_INTRO
import numpy as np
from sentence_transformers import SentenceTransformer
import scipy
import pandas as pd
import json
import logging
import uuid
from wsgiref import simple_server

import falcon
import requests

import os
import tqdm
import textwrap
import json
import prettytable
import logging
import pickle
import warnings
warnings.simplefilter('ignore')


os.system('cls' if os.name == 'nt' else 'clear')
if not os.path.exists(CORPUS_PATH):
    print("Caching the corpus for future use...")
    corpus = cache_corpus()
else:
    print("Loading the corpus from", CORPUS_PATH, '...')
    with open(CORPUS_PATH, 'rb') as corpus_pt:
        corpus = pickle.load(corpus_pt)

corpus_abstract = []
model = SentenceTransformer(MODEL_PATH)
for i in range(len(corpus)):
    corpus_abstract.append(corpus[i][0])

print(EMBEDDINGS_PATH)
if not os.path.exists(EMBEDDINGS_PATH):
    print("Computing and caching model embeddings for future use...")
    embeddings = model.encode(corpus_abstract, show_progress_bar=True)
    with open(EMBEDDINGS_PATH, 'wb') as file:
        pickle.dump(embeddings, file)
else:
    print("Loading model embeddings from", EMBEDDINGS_PATH, '...')
    with open(EMBEDDINGS_PATH, 'rb') as file:
        embeddings = pickle.load(file)
    print('done')


# transform the search result to a dict with the right format
def format_answers(results):
    dict_result = {}
    for i in range(len(results)):
        rank = results[i][0]
        abstract = results[i][1]
        score = results[i][2]
        date = results[i][3]
        language = results[i][4]

        dict_result[str(rank)] = []
        dict_result[str(rank)] = {
            'abstract': abstract,
            'score': score,
            'date': date,
            'language': language
        }

    return dict_result


def format_answers1(results):
    dict_result = []
    for i in range(len(results)):
        rank = results[i][0]
        abstract = results[i][1]
        score = results[i][2]
        date = results[i][3]
        language = results[i][4]
        title = results[i][5]
        url = results[i][6]
        theme = results[i][7]
        sub_theme = results[i][8]
        u_id = results[i][9]

        if type(url) == str:
            new = {
                'url': url,
                'title': title,
                'abstract': abstract,
                'score': score,
                'date': date,
                'language': language,
                'theme': theme,
                'sub_topic': sub_theme,
                'u_id': u_id
            }
        else:  # url missing
            new = {
                'title': title,
                'abstract': abstract,
                'score': score,
                'date': date,
                'language': language,
                'theme': theme,
                'sub_topic': sub_theme,
                'u_id': u_id
            }

        dict_result.append(new)

        print(url)

    return dict_result


class StorageEngine(object):

    def get_papers(self, query, limit):

        # FIXME: filters for the search - the query shouly be a dict with the actual filters + the values from the filters
        filters = [None, None, None]
        results = format_answers1(ask_question(
            query, model, corpus, embeddings, filters, top_k=2000))

        return {'query': query, 'papers': results}

    def get_things(self, marker, limit):
        return [{'id': str(uuid.uuid4()), 'color': 'green'}]

    def add_thing(self, thing):
        thing['id'] = str(uuid.uuid4())
        return thing


class StorageError(Exception):

    @staticmethod
    def handle(ex, req, resp, params):
        description = ('Sorry, couldn\'t write your thing to the '
                       'database. It worked on my box.')

        raise falcon.HTTPError(falcon.HTTP_725,
                               'Database Error',
                               description)


class SinkAdapter(object):

    engines = {
        'ddg': 'https://duckduckgo.com',
        'y': 'https://search.yahoo.com/search',
    }

    def __call__(self, req, resp, engine):
        url = self.engines[engine]
        params = {'q': req.get_param('q', True)}
        result = requests.get(url, params=params)

        resp.status = str(result.status_code) + ' ' + result.reason
        resp.content_type = result.headers['content-type']
        resp.body = result.text


class AuthMiddleware(object):

    def process_request(self, req, resp):

        if req.method != 'OPTIONS':
            token = req.get_header('Authorization')
            account_id = req.get_header('Account-ID')

            challenges = ['Token type="Fernet"']

            if token is None:
                description = ('Please provide an auth token '
                               'as part of the request.')

                raise falcon.HTTPUnauthorized('Auth token required',
                                              description,
                                              challenges,
                                              href='http://docs.example.com/auth')

            if not self._token_is_valid(token, account_id):
                description = ('The provided auth token is not valid. '
                               'Please request a new token and try again.')

                raise falcon.HTTPUnauthorized('Authentication required',
                                              description,
                                              challenges,
                                              href='http://docs.example.com/auth')

    def _token_is_valid(self, token, account_id):
        return account_id == 'bin' and token == 'ZHANG'


class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')


class JSONTranslator(object):
    # NOTE: Starting with Falcon 1.3, you can simply
    # use req.media and resp.media for this instead.

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context.doc = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource, req_succeeded):
        if not hasattr(resp.context, 'result'):
            return

        resp.body = json.dumps(resp.context.result)


def max_body(limit):

    def hook(req, resp, resource, params):
        length = req.content_length
        if length is not None and length > limit:
            msg = ('The size of the request is too large. The body must not '
                   'exceed ' + str(limit) + ' bytes in length.')

            raise falcon.HTTPPayloadTooLarge(
                'Request body is too large', msg)

    return hook


class CORSComponent(object):
    def process_response(self, req, resp, resource, req_succeeded):
        resp.set_header('Access-Control-Allow-Origin', '*')

        if (req_succeeded
            and req.method == 'OPTIONS'
            and req.get_header('Access-Control-Request-Method')
            ):
            # NOTE(kgriffs): This is a CORS preflight request. Patch the
            #   response accordingly.

            allow = resp.get_header('Allow')
            resp.delete_header('Allow')

            allow_headers = req.get_header(
                'Access-Control-Request-Headers',
                default='*'
            )

            resp.set_headers((
                ('Access-Control-Allow-Methods', allow),
                ('Access-Control-Allow-Headers', allow_headers),
                ('Access-Control-Max-Age', '86400'),  # 24 hours
            ))


class ThingsResource(object):

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('thingsapp.' + __name__)

    def on_get(self, req, resp, user_id):
        marker = req.get_param('marker') or ''
        limit = req.get_param_as_int('limit') or 50

        try:
            result = self.db.get_things(marker, limit)
        except Exception as ex:
            self.logger.error(ex)

            description = ('Aliens have attacked our base! We will '
                           'be back as soon as we fight them off. '
                           'We appreciate your patience.')

            raise falcon.HTTPServiceUnavailable(
                'Service Outage',
                description,
                30)

        # An alternative way of doing DRY serialization would be to
        # create a custom class that inherits from falcon.Request. This
        # class could, for example, have an additional 'doc' property
        # that would serialize to JSON under the covers.
        #
        # NOTE: Starting with Falcon 1.3, you can simply
        # use resp.media for this instead.
        resp.context.result = result

        resp.set_header('Powered-By', 'Falcon')
        resp.status = falcon.HTTP_200

    @falcon.before(max_body(64 * 1024))
    def on_post(self, req, resp, user_id):
        try:
            doc = req.context.doc
        except AttributeError:
            raise falcon.HTTPBadRequest(
                'Missing thing',
                'A thing must be submitted in the request body.')

        proper_thing = self.db.add_thing(doc)

        resp.status = falcon.HTTP_201
        resp.location = '/%s/things/%s' % (user_id, proper_thing['id'])


class PapersResource(object):

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('papersapp.' + __name__)

    def on_get(self, req, resp):
        query = req.get_param('q') or ''
        limit = req.get_param_as_int('limit') or 50

        try:
            result = self.db.get_papers(query, limit)
        except Exception as ex:
            self.logger.error(ex)

            description = ('Aliens have attacked our base! We will '
                           'be back as soon as we fight them off. '
                           'We appreciate your patience.')

            raise falcon.HTTPServiceUnavailable(
                'Service Outage',
                description,
                30)

        # An alternative way of doing DRY serialization would be to
        # create a custom class that inherits from falcon.Request. This
        # class could, for example, have an additional 'doc' property
        # that would serialize to JSON under the covers.
        #
        # NOTE: Starting with Falcon 1.3, you can simply
        # use resp.media for this instead.
        resp.context.result = result

        # TODO currently only CORS if succsess, change to output friendlier error messages
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Powered-By', 'Papers')
        resp.status = falcon.HTTP_200


# Configure your WSGI server to load "things.app" (app is a WSGI callable)
app = falcon.API(middleware=[
    CORSComponent(),
    AuthMiddleware(),
    RequireJSON(),
    JSONTranslator(),
])

db = StorageEngine()

# things = ThingsResource(db)
# app.add_route('/{user_id}/things', things)

papers = PapersResource(db)
app.add_route('/papers', papers)

# If a responder ever raised an instance of StorageError, pass control to
# the given handler.
# app.add_error_handler(StorageError, StorageError.handle)

# Proxy some things to another service; this example shows how you might
# send parts of an API off to a legacy system that hasn't been upgraded
# yet, or perhaps is a single cluster that all data centers have to share.
# sink = SinkAdapter()
# app.add_sink(sink, r'/search/(?P<engine>ddg|y)\Z')

# Useful for debugging problems in your API; works with pdb.set_trace(). You
# can also use Gunicorn to host your app. Gunicorn can be configured to
# auto-restart workers when it detects a code change, and it also works
# with pdb.

if __name__ == '__main__':
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()
