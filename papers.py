#!/usr/bin/env python

import json
import logging
import uuid
from wsgiref import simple_server

import falcon
import requests

import os
import pickle

from sentence_transformers import SentenceTransformer
import scipy

HOST = '0.0.0.0'
PORT = 8000
RETURN_DEFAULT = 500
RETURN_LIMIT = 2000

DATA_PATH = 'data'
MODELS_PATH = 'models'
MODEL_NAME = 'scibert-nli'
CORPUS_PATH = os.path.join(DATA_PATH, 'corpus.pkl')
MODEL_PATH = os.path.join(MODELS_PATH, MODEL_NAME)
EMBEDDINGS_PATH = os.path.join(DATA_PATH, f'{MODEL_NAME}-embeddings.pkl')

UID_LEN = 8


class AnswerEngine(object):

    def __init__(self, corpus_path, model_path, embeds_path):
        print(f'Load corpus from "{corpus_path}"...')
        if not os.path.exists(corpus_path):
            raise AnswerError(f'Can\'t find corpus.')
        with open(corpus_path, 'rb') as f:
            self.corpus = pickle.load(f)
        item0_cord_uuid = self.corpus[0][7]
        if not AnswerEngine.is_cord_uid(item0_cord_uuid):
            raise AnswerError('Wrong corpus or corrupted data.')

        print(f'Load model from "{model_path}"...')
        if not os.path.exists(model_path):
            raise AnswerError(f'Can\'t find model.')
        self.model = SentenceTransformer(model_path)

        print(f'Load embeddings from "{embeds_path}"...')
        if not os.path.exists(embeds_path):
            raise AnswerError(f'Can\'t find embeddings.')
        with open(embeds_path, 'rb') as f:
            self.embeds = pickle.load(f)

        print('Answer engine initialized.')

    def ask_question(self, query, filters={}, top_k=RETURN_DEFAULT):
        queries = [query]  # only one query at the moment
        query_embeds = self.model.encode(queries, show_progress_bar=False)
        results = []
        count = 0
        for query, query_embed in zip(queries, query_embeds):
            distances = scipy.spatial.distance.cdist(
                [query_embed], self.embeds, "cosine")[0]
            distances = zip(range(len(distances)), distances)
            distances = sorted(distances, key=lambda x: x[1])
            for idx, distance in distances:
                item_raw = self.corpus[idx]
                if not AnswerEngine.is_cord_uid(item_raw[7]):
                    # skip invalid item
                    continue
                item = dict(
                    cord_uid=item_raw[7],
                    title=item_raw[3],
                    abstract=item_raw[0],
                    date=item_raw[1],
                    # random.choice(['en','zh','fr','de','es','it','pt','ja']),
                    lang=item_raw[2],
                    url=item_raw[4],
                    theme=item_raw[5],
                    sub_theme=item_raw[6],
                )
                if self.check_constraints(item, filters):
                    count += 1
                    results.append({
                        'score': round((1 - distance)*10, 3),  # 0.000 - 10.000
                        **item
                    })
                if count >= top_k:
                    break
        return results

    def check_constraints(self, data, filters):
        for key in data.keys() & filters.keys():
            if not filters[key](data[key]):
                return False
        return True

    def format_results(self, results):
        papers = []
        langs = {}
        for item in results:
            papers.append({
                'cord_uid': item['cord_uid'],
                'score': item['score'],
                ** ({'title': item['title']} if not AnswerEngine.is_null(item['title']) else {}),
                # strip abstract
                ** ({'abstract': item['abstract'].strip()} if not AnswerEngine.is_null(item['abstract']) else {}),
                ** ({'date': item['date']} if not AnswerEngine.is_null(item['date']) else {}),
                ** ({'lang': item['lang']} if not AnswerEngine.is_null(item['lang']) else {}),
                ** ({'url': item['url']} if not AnswerEngine.is_null(item['url']) else {}),
                ** ({'theme': item['theme']} if not AnswerEngine.is_null(item['theme']) else {}),
                ** ({'sub_theme': item['sub_theme']} if not AnswerEngine.is_null(item['sub_theme']) else {}),
            })
            if item['lang'] in langs:
                langs[item['lang']] += 1
            else:
                langs[item['lang']] = 1
        return {
            'langs': langs,
            'papers': papers,
        }

    @staticmethod
    def is_cord_uid(uid):
        return type(uid) is str and len(uid) == UID_LEN

    @staticmethod
    def is_null(data):
        return data == None or data != data


class AnswerError(Exception):

    @staticmethod
    def handle(ex, req, resp, params):
        description = format(ex)
        # :) https://github.com/joho/7XX-rfc
        raise falcon.HTTPError(falcon.HTTP_725,
                               'Answer Engine Error',
                               description)


# class StorageEngine(object):

#     def get_things(self, marker, limit):
#         return [{'id': str(uuid.uuid4()), 'color': 'green'}]

#     def add_thing(self, thing):
#         thing['id'] = str(uuid.uuid4())
#         return thing


# class StorageError(Exception):

#     @staticmethod
#     def handle(ex, req, resp, params):
#         description = ('Sorry, couldn\'t write your thing to the '
#                        'database. It worked on my box.')

#         raise falcon.HTTPError(falcon.HTTP_725,
#                                'Database Error',
#                                description)


class HealthSink(object):

    def __call__(self, req, resp):

        resp.content_type = 'text/plain'
        resp.body = 'Papers-19'
        resp.set_header('Powered-By', 'Papers')
        resp.status = falcon.HTTP_200


# class SinkAdapter(object):

#     engines = {
#         'ddg': 'https://duckduckgo.com',
#         'y': 'https://search.yahoo.com/search',
#     }

#     def __call__(self, req, resp, engine):
#         url = self.engines[engine]
#         params = {'q': req.get_param('q', True)}
#         result = requests.get(url, params=params)

#         resp.status = str(result.status_code) + ' ' + result.reason
#         resp.content_type = result.headers['content-type']
#         resp.body = result.text


class AuthMiddleware(object):

    def process_request(self, req, resp):

        if not (
            req.method == 'OPTIONS'
            or req.path == '/health' or req.path.startswith('/health/')
        ):
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


# class ThingsResource(object):

#     def __init__(self, db):
#         self.db = db
#         self.logger = logging.getLogger('thingsapp.' + __name__)

#     def on_get(self, req, resp, user_id):
#         marker = req.get_param('marker') or ''
#         limit = req.get_param_as_int('limit') or 50

#         try:
#             result = self.db.get_things(marker, limit)
#         except Exception as ex:
#             self.logger.error(ex)

#             description = ('Aliens have attacked our base! We will '
#                            'be back as soon as we fight them off. '
#                            'We appreciate your patience.')

#             raise falcon.HTTPServiceUnavailable(
#                 'Service Outage',
#                 description,
#                 30)

#         # An alternative way of doing DRY serialization would be to
#         # create a custom class that inherits from falcon.Request. This
#         # class could, for example, have an additional 'doc' property
#         # that would serialize to JSON under the covers.
#         #
#         # NOTE: Starting with Falcon 1.3, you can simply
#         # use resp.media for this instead.
#         resp.context.result = result

#         resp.set_header('Powered-By', 'Falcon')
#         resp.status = falcon.HTTP_200

#     @falcon.before(max_body(64 * 1024))
#     def on_post(self, req, resp, user_id):
#         try:
#             doc = req.context.doc
#         except AttributeError:
#             raise falcon.HTTPBadRequest(
#                 'Missing thing',
#                 'A thing must be submitted in the request body.')

#         proper_thing = self.db.add_thing(doc)

#         resp.status = falcon.HTTP_201
#         resp.location = '/%s/things/%s' % (user_id, proper_thing['id'])


class PapersResource(object):

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('papersapp.' + __name__)

    def on_get(self, req, resp):
        query = req.get_param('q') or ''
        limit = req.get_param_as_int('limit') or RETURN_DEFAULT
        if limit > RETURN_LIMIT:
            limit = RETURN_LIMIT

        # TODO: implement filters
        filters = {
            # 'lang': lambda lang: lang == 'en'
        }

        try:
            result = {
                'query': query,
                ** self.db.format_results(
                    self.db.ask_question(query, filters, limit)
                ),
            }
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

db = AnswerEngine(CORPUS_PATH, MODEL_PATH, EMBEDDINGS_PATH)
papers = PapersResource(db)
app.add_route('/papers', papers)
app.add_error_handler(AnswerError, AnswerError.handle)
health = HealthSink()
app.add_sink(health, r'/health(?:/.*)?\Z')

# db = StorageEngine()
# things = ThingsResource(db)
# app.add_route('/{user_id}/things', things)

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
    print(f'Serving at {HOST}:{PORT}')
    httpd = simple_server.make_server(HOST, PORT, app)
    httpd.serve_forever()
