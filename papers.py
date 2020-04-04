#!/usr/bin/env python

import json
import logging
import uuid
from wsgiref import simple_server

import falcon
import requests


class StorageEngine(object):

    def get_papers(self, query, limit):
        if query != 'test':
            papers = [
                {
                    'url': "https://www.medrxiv.org/content/10.1101/2020.03.09.20033357v1",
                    'title': "Estimates of the severity of COVID-19 disease",
                    'abstract': "A range of case fatality ratio (CFR) estimates for COVID 19 have been produced that differ substantially in magnitude. Methods: We used individual-case data from mainland China and cases detected outside mainland China to estimate the time between onset of symptoms and outcome (death or discharge from hospital). We next obtained age-stratified estimates of the CFR by relating the aggregate distribution of cases by dates of onset to the observed cumulative deaths in China, assuming a constant attack rate by age and adjusting for the demography of the population, and age and location-based under ascertainment. We additionally estimated the CFR from individual linelist data on 1,334 cases identified outside mainland China. We used data on the PCR prevalence in international residents repatriated from China at the end of January 2020 to obtain age-stratified estimates of the infection fatality ratio (IFR). Using data on age stratified severity in a subset of 3,665 cases from China, we estimated the proportion of infections that will likely require hospitalisation. Findings: We estimate the mean duration from onset-of-symptoms to death to be 17.8 days (95% credible interval, crI 16.9,19.2 days) and from onset-of-symptoms to hospital discharge to be 22.6 days (95% crI 21.1,24.4 days). We estimate a crude CFR of 3.67% (95% crI 3.56%,3.80%) in cases from mainland China. Adjusting for demography and under-ascertainment of milder cases in Wuhan relative to the rest of China, we obtain a best estimate of the CFR in China of 1.38% (95% crI 1.23%,1.53%) with substantially higher values in older ages. Our estimate of the CFR from international cases stratified by age (under 60 or 60 and above) are consistent with these estimates from China. We obtain an overall IFR estimate for China of 0.66% (0.39%,1.33%), again with an increasing profile with age. Interpretation: These early estimates give an indication of the fatality ratio across the spectrum of COVID-19 disease and demonstrate a strong age-gradient in risk.",
                    'score': 0.5943,
                    'date': "2020-03-13",
                    'language': "en"
                },
                {
                    'title': "Clinical determinants of the severity of Middle East respiratory syndrome (MERS): a systematic review and meta-analysis",
                    'abstract': "While the risk of severe complications of Middle East respiratory syndrome (MERS) and its determinants have been explored in previous studies, a systematic analysis of published articles with different designs and populations has yet to be conducted. The present study aimed to systematically review the risk of death associated with MERS as well as risk factors for associated complications. METHODS: PubMed and Web of Science databases were searched for clinical and epidemiological studies on confirmed cases of MERS. Eligible articles reported clinical outcomes, especially severe complications or death associated with MERS. Risks of admission to intensive care unit (ICU), mechanical ventilation and death were estimated. Subsequently, potential associations between MERS-associated death and age, sex, underlying medical conditions and study design were explored. RESULTS: A total of 25 eligible articles were identified. The case fatality risk ranged from 14.5 to 100%, with the pooled estimate at 39.1%. The risks of ICU admission and mechanical ventilation ranged from 44.4 to 100% and from 25.0 to 100%, with pooled estimates at 78.2 and 73.0%, respectively. These risks showed a substantial heterogeneity among the identified studies, and appeared to be the highest in case studies focusing on ICU cases. We identified older age, male sex and underlying medical conditions, including diabetes mellitus, renal disease, respiratory disease, heart disease and hypertension, as clinical predictors of death associated with MERS. In ICU case studies, the expected odds ratios (OR) of death among patients with underlying heart disease or renal disease to patients without such comorbidities were 0.6 (95% Confidence Interval (CI): 0.1, 4.3) and 0.6 (95% CI: 0.0, 2.1), respectively, while the ORs were 3.8 (95% CI: 3.4, 4.2) and 2.4 (95% CI: 2.0, 2.9), respectively, in studies with other types of designs. CONCLUSIONS: The heterogeneity for the risk of death and severe manifestations was substantially high among the studies, and varying study designs was one of the underlying reasons for this heterogeneity. A statistical estimation of the risk of MERS death and identification of risk factors must be conducted, particularly considering the study design and potential biases associated with case detection and diagnosis. ELECTRONIC SUPPLEMENTARY MATERIAL: The online version of this article (doi:10.1186/s12889-016-3881-4) contains supplementary material, which is available to authorized users.",
                    'score': 0.551,
                    'date': "2016-11-29",
                    'language': "en"
                },
                {
                    'title': "Middle East Respiratory Syndrome-Coronavirus (MERS-CoV) Infection",
                    'abstract': "MERS-CoV infection is an emerging infectious disease with a high mortality rate. The exact incidence and prevalence of the disease is not known as we do not have yet reliable serologic tests. The diagnosis of MERS-CoV infection relies on detection of the virus using real-time RT-PCR. Currently, the origin of the virus and the source is not known and future studies are needed to elucidate possible sources and the best therapeutic options.",
                    'score': 0.549,
                    'date': "2014-12-31",
                    'language': "en"
                },
                {
                    'url': "https://www.medrxiv.org/content/10.1101/2020.03.21.20040121v1",
                    'title': "Myocardial injury is associated with in-hospital mortality of confirmed or suspected COVID-19 in Wuhan, China: A single center retrospective cohort study",
                    'abstract': "[Background] Since December 2019, a cluster of coronavirus disease 2019 (COVID-19) occurred in Wuhan, Hubei Province, China and spread rapidly from China to other countries. In-hospital mortality are high in severe cases and cardiac injury characterized by elevated cardiac troponin are common among them. The mechanism of cardiac injury and the relationship between cardiac injury and in-hospital mortality remained unclear. Studies focused on cardiac injury in COVID-19 patients are scarce. [Objectives] To investigate the association between cardiac injury and in-hospital mortality of patients with confirmed or suspected COVID-19. [Methods] Demographic, clinical, treatment, and laboratory data of consecutive confirmed or suspected COVID-19 patients admitted in Wuhan No.1 Hospital from 25th December, 2019 to 15th February, 2020 were extracted from electronic medical records and were retrospectively reviewed and analyzed. Univariate and multivariate Cox regression analysis were used to explore the risk factors associated with in-hospital death. [Results] A total of 110 patients with confirmed (n=80) or suspected (n=30) COVID-19 were screened and 48 patients (female 31.3%, mean age 70.58±13.38 year old) among them with high-sensitivity cardiac troponin I (hs-cTnI) test within 48 hours after admission were included, of whom 17 (17/48, 35.4%) died in hospital while 31 (31/48, 64.6%) were discharged or transferred to other hospital. High-sensitivity cardiac troponin I was levated in 13 (13/48, 27.1%) patents. Multivariate Cox regression analysis showed pulse oximetry of oxygen saturation (SpO2) on admission (HR 0.704, 95% CI 0.546-0.909, per 1% decrease, p=0.007), elevated hs-cTnI (HR 10.902, 95% 1.279-92.927, p=0.029) and elevated d-dimer (HR 1.103, 95%CI 1.034-1.176, per 1mg/L increase, p=0.003) on admission were independently associated with in-hospital mortality. [Conclusions] Cardiac injury defined by hs-cTnI elevation and elevated d-dimer on admission were risk factors for in-hospital death, while higher SpO2 could be seen as a protective factor, which could help clinicians to identify patients with adverse outcome at the early stage of COVID-19.",
                    'score': 0.5489,
                    'date': "2020-03-24",
                    'language': "en"
                },
                {
                    'title': "Oligomerization of the carboxyl terminal domain of the human coronavirus 229E nucleocapsid protein.",
                    'abstract': "The coronavirus (CoV) N protein oligomerizes via its carboxyl terminus. However, the oligomerization mechanism of the C-terminal domains (CTD) of CoV N proteins remains unclear. Based on the protein disorder prediction system, a comprehensive series of HCoV-229E N protein mutants with truncated CTD was generated and systematically investigated by biophysical and biochemical analyses to clarify the role of the C-terminal tail of the HCoV-229E N protein in oligomerization. These results indicate that the last C-terminal tail plays an important role in dimer–dimer association. The C-terminal tail peptide is able to interfere with the oligomerization of the CTD of HCoV-229E N protein and performs the inhibitory effect on viral titre of HCoV-229E. This study may assist the development of anti-viral drugs against HCoV. Structured summary of protein interactions N and C-terminal tail peptide bind by cosedimentation in solution (View interaction) N and N bind by cosedimentation in solution (View Interaction: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12) C-terminal tail peptide and N bind by fluorescence technology (View interaction) N and N bind by cross-linking study (View interaction) N and N bind by cross-linking study (View Interaction: 1, 2, 3, 4)",
                    'score': 0.5474,
                    'date': "2013-01-16",
                    'language': "en"
                }
            ]
        else:
            papers = [
                {
                    'title': "How",
                    'abstract': "A range of case fatality ratio (CFR) estimates for COVID 19 have been produced that differ substantially in magnitude. Methods: We used individual-case data from mainland China and cases detected outside mainland China to estimate the time between onset of symptoms and outcome (death or discharge from hospital). We next obtained age-stratified estimates of the CFR by relating the aggregate distribution of cases by dates of onset to the observed cumulative deaths in China, assuming a constant attack rate by age and adjusting for the demography of the population, and age and location-based under ascertainment. We additionally estimated the CFR from individual linelist data on 1,334 cases identified outside mainland China. We used data on the PCR prevalence in international residents repatriated from China at the end of January 2020 to obtain age-stratified estimates of the infection fatality ratio (IFR). Using data on age stratified severity in a subset of 3,665 cases from China, we estimated the proportion of infections that will likely require hospitalisation. Findings: We estimate the mean duration from onset-of-symptoms to death to be 17.8 days (95% credible interval, crI 16.9,19.2 days) and from onset-of-symptoms to hospital discharge to be 22.6 days (95% crI 21.1,24.4 days). We estimate a crude CFR of 3.67% (95% crI 3.56%,3.80%) in cases from mainland China. Adjusting for demography and under-ascertainment of milder cases in Wuhan relative to the rest of China, we obtain a best estimate of the CFR in China of 1.38% (95% crI 1.23%,1.53%) with substantially higher values in older ages. Our estimate of the CFR from international cases stratified by age (under 60 or 60 and above) are consistent with these estimates from China. We obtain an overall IFR estimate for China of 0.66% (0.39%,1.33%), again with an increasing profile with age. Interpretation: These early estimates give an indication of the fatality ratio across the spectrum of COVID-19 disease and demonstrate a strong age-gradient in risk.",
                    'score': 0.5943,
                    'date': "2020-03-13",
                    'language': "en"
                },
                {
                    'title': "are",
                    'abstract': "While the risk of severe complications of Middle East respiratory syndrome (MERS) and its determinants have been explored in previous studies, a systematic analysis of published articles with different designs and populations has yet to be conducted. The present study aimed to systematically review the risk of death associated with MERS as well as risk factors for associated complications. METHODS: PubMed and Web of Science databases were searched for clinical and epidemiological studies on confirmed cases of MERS. Eligible articles reported clinical outcomes, especially severe complications or death associated with MERS. Risks of admission to intensive care unit (ICU), mechanical ventilation and death were estimated. Subsequently, potential associations between MERS-associated death and age, sex, underlying medical conditions and study design were explored. RESULTS: A total of 25 eligible articles were identified. The case fatality risk ranged from 14.5 to 100%, with the pooled estimate at 39.1%. The risks of ICU admission and mechanical ventilation ranged from 44.4 to 100% and from 25.0 to 100%, with pooled estimates at 78.2 and 73.0%, respectively. These risks showed a substantial heterogeneity among the identified studies, and appeared to be the highest in case studies focusing on ICU cases. We identified older age, male sex and underlying medical conditions, including diabetes mellitus, renal disease, respiratory disease, heart disease and hypertension, as clinical predictors of death associated with MERS. In ICU case studies, the expected odds ratios (OR) of death among patients with underlying heart disease or renal disease to patients without such comorbidities were 0.6 (95% Confidence Interval (CI): 0.1, 4.3) and 0.6 (95% CI: 0.0, 2.1), respectively, while the ORs were 3.8 (95% CI: 3.4, 4.2) and 2.4 (95% CI: 2.0, 2.9), respectively, in studies with other types of designs. CONCLUSIONS: The heterogeneity for the risk of death and severe manifestations was substantially high among the studies, and varying study designs was one of the underlying reasons for this heterogeneity. A statistical estimation of the risk of MERS death and identification of risk factors must be conducted, particularly considering the study design and potential biases associated with case detection and diagnosis. ELECTRONIC SUPPLEMENTARY MATERIAL: The online version of this article (doi:10.1186/s12889-016-3881-4) contains supplementary material, which is available to authorized users.",
                    'score': 0.551,
                    'date': "2016-11-29",
                    'language': "en"
                },
                {
                    'url': "https://www.google.com/search?q=covid-19",
                    'title': "you?",
                    'abstract': "MERS-CoV infection is an emerging infectious disease with a high mortality rate. The exact incidence and prevalence of the disease is not known as we do not have yet reliable serologic tests. The diagnosis of MERS-CoV infection relies on detection of the virus using real-time RT-PCR. Currently, the origin of the virus and the source is not known and future studies are needed to elucidate possible sources and the best therapeutic options.",
                    'score': 0.549,
                    'date': "2014-12-31",
                    'language': "en"
                }
            ]
        return {'query': query, 'papers': papers}

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
