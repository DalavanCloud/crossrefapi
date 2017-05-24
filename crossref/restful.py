import requests
import json

from crossref import validators

LIMIT = 20
MAXOFFSET = 40
API = "api.crossref.org"


class CrossrefAPIError(Exception):
    pass


class MaxOffsetError(CrossrefAPIError):
    pass


class UrlSyntaxError(CrossrefAPIError, ValueError):
    pass


def do_http_request(method, endpoint, data=None, files=None, timeout=10, only_headers=False):

    if method == 'post':
        action = requests.post
    else:
        action = requests.get

    if only_headers is True:
        return requests.head(endpoint)

    if method == 'post':
        result = action(endpoint, data=data, files=files, timeout=timeout)
    else:
        result = action(endpoint, params=data, timeout=timeout)

    return result


def build_url_endpoint(parts):
    return 'http://%s' % '/'.join([str(i) for i in parts if i is not None])


class Endpoint:

    def __init__(self, request_url=None, request_params=None):
        self.request_url = build_url_endpoint(self.ENDPOINT)
        self.request_params = request_params or dict()

    def _escaped_pagging(self):
        escape_pagging = ['offset', 'rows']
        request_params = dict(self.request_params)

        for item in escape_pagging:
            try:
                del(request_params[item])
            except KeyError:
                pass

        return request_params

    @property
    def url(self):
        request_params = self._escaped_pagging()
        req = requests.Request(
            'get', self.request_url, params=request_params).prepare()

        return req.url

    def all(self):
        request_url = build_url_endpoint(self.ENDPOINT)
        request_params = {}

        return iter(self.__class__(request_url, request_params))

    def __iter__(self):

        if 'sample' in self.request_params:
            request_params = self._escaped_pagging()
            result = do_http_request(
                'get', self.request_url, data=request_params).json()

            for item in result['message']['items']:
                yield item

            return

        self.request_params['offset'] = 0
        self.request_params['rows'] = LIMIT

        while True:
            result = do_http_request(
                'get', self.request_url, data=self.request_params).json()

            if len(result['message']['items']) == 0:
                return

            for item in result['message']['items']:
                yield item

            self.request_params['offset'] += LIMIT + 1

            if self.request_params['offset'] >= MAXOFFSET:
                raise MaxOffsetError(
                    'Offset exceded the max offset of %d',
                    MAXOFFSET
                )


class Works(Endpoint):

    ENDPOINT = [API, 'works']

    ORDER_VALUES = ['asc', 'desc', '1', '-1']

    SORT_VALUES = [
        'created',
        'deposited',
        'indexed',
        'is-referenced-by-count',
        'issued',
        'published',
        'published-online',
        'published-print',
        'references-count',
        'relevance',
        'score',
        'submitted',
        'updated'
    ]

    FIELDS_QUERY = [
        'affiliation',
        'author',
        'bibliographic',
        'chair',
        'container_title',
        'contributor',
        'editor',
        'event_acronym',
        'event_location',
        'event_name',
        'event_sponsor',
        'event_theme',
        'funder_name',
        'publisher_location',
        'publisher_name',
        'title',
        'translator'
    ]

    FILTER_VALIDATOR = {
        'alternative_id': None,
        'archive': None,
        'article_number': None,
        'assertion': None,
        'assertion-group': None,
        'award.funder': None,
        'award.number': None,
        'category-name': None,
        'clinical-trial-number': None,
        'container-title': None,
        'content-domain': None,
        'directory': None,
        'doi': None,
        'from-accepted_date': validators.is_date,
        'from-created-date': validators.is_date,
        'from-deposit-date': validators.is_date,
        'from-event-end-date': validators.is_date,
        'from-event-start-date': validators.is_date,
        'from-index-date': validators.is_date,
        'from-issued-date': validators.is_date,
        'from-online-pub-date': validators.is_date,
        'from-posted-date': validators.is_date,
        'from-print-pub-date': validators.is_date,
        'from-pub-date': validators.is_date,
        'from-update-date': validators.is_date,
        'full-text.application': None,
        'full-text.type': None,
        'full-text.version': None,
        'funder': None,
        'funder-doi-asserted-by': None,
        'group-title': None,
        'has_abstract': validators.is_bool,
        'has-affiliation': validators.is_bool,
        'has-archive': validators.is_bool,
        'has-assertion': validators.is_bool,
        'has-authenticated-orcid': validators.is_bool,
        'has-award': validators.is_bool,
        'has-clinical-trial-number': validators.is_bool,
        'has-content-domain': validators.is_bool,
        'has-domain-restriction': validators.is_bool,
        'has-event': validators.is_bool,
        'has-full-text': validators.is_bool,
        'has-funder': validators.is_bool,
        'has-funder-doi': validators.is_bool,
        'has-license': validators.is_bool,
        'has-orcid': validators.is_bool,
        'has-references': validators.is_bool,
        'has-relation': validators.is_bool,
        'has-update': validators.is_bool,
        'has-update-policy': validators.is_bool,
        'is-update': validators.is_bool,
        'isbn': None,
        'issn': None,
        'license.delay': validators.is_integer,
        'license.url': None,
        'license.version': None,
        'member': None,
        'orcid': None,
        'prefix': None,
        'relation.object': None,
        'relation.object-type': None,
        'relation.type': None,
        'type': None,
        'type-name': None,
        'until-accepted-date': validators.is_bool,
        'until-created-date': validators.is_bool,
        'until-deposit-date': validators.is_bool,
        'until-event-end-date': validators.is_bool,
        'until-event-start-date': validators.is_bool,
        'until-index-date': validators.is_bool,
        'until-issued-date': validators.is_bool,
        'until-online-pub-date': validators.is_bool,
        'until-posted-date': validators.is_bool,
        'until-print-pub-date': validators.is_bool,
        'until-pub-date': validators.is_bool,
        'until-update-date': validators.is_bool,
        'update-type': None,
        'updates': None
     }

    def order(self, order='asc'):
        request_url = build_url_endpoint(self.ENDPOINT)
        request_params = dict(self.request_params)

        if order not in self.ORDER_VALUES:
            raise UrlSyntaxError(
                'Sort order specified as %s but must be one of: %s' % (
                    str(order),
                    ', '.join(self.ORDER_VALUES)
                )
            )

        request_params['order'] = order

        return self.__class__(request_url, request_params)

    def sort(self, sort='score'):
        request_url = build_url_endpoint(self.ENDPOINT)
        request_params = dict(self.request_params)

        if sort not in self.SORT_VALUES:
            raise UrlSyntaxError(
                'Sort field specified as %s but must be one of: %s' % (
                    str(sort),
                    ', '.join(self.SORT_VALUES)
                )
            )

        request_params['sort'] = sort

        return self.__class__(request_url, request_params)

    def filter(self, **kwargs):
        parts = [self.ENDPOINT]
        request_url = build_url_endpoint(self.ENDPOINT)
        request_params = dict(self.request_params)

        for fltr, value in kwargs.items():

            if fltr not in self.FILTER_VALIDATOR.keys():
                raise UrlSyntaxError(
                    'Filter %s specified but there is no such filter for this route. Valid filters for this route are: %s' % (
                        str(fltr),
                        ', '.join(self.FILTER_VALIDATOR.keys())
                    )
                )

            if self.FILTER_VALIDATOR[fltr] is not None:
                self.FILTER_VALIDATOR[fltr](str(value).lower())

            if 'filter' not in request_params:
                request_params['filter'] = fltr.replace('_', '-') + ':' + str(value).lower()
            else:
                request_params['filter'] += ','+fltr.replace('_', '-') + ':' + str(value).lower()

        return self.__class__(request_url, request_params)

    def query(self, *args, **kwargs):

        request_url = build_url_endpoint(self.ENDPOINT)
        request_params = dict(self.request_params)

        if args:
            request_params['query'] = ' '.join(list(args))

        for field, value in kwargs.items():
            if field not in self.FIELDS_QUERY:
                raise UrlSyntaxError(
                    'Field query %s specified but there is no such field query for this route. Valid field queries for this route are: %s' % (
                        str(field), ', '.join(self.FIELDS_QUERY)
                    )
                )
            request_params['query.%s' % field.replace('_', '-')] = value

        return self.__class__(request_url, request_params)

    def sample(self, sample_size=20):
        request_url = build_url_endpoint(self.ENDPOINT)
        request_params = {}
        try:
            if sample_size > 100:
                raise UrlSyntaxError(
                    'Integer specified as %s but must be a positive integer less than or equal to 100.' % str(sample_size)
                )
        except TypeError:
            raise UrlSyntaxError(
                'Integer specified as %s but must be a positive integer less than or equal to 100.' % str(sample_size)
            )

        request_params['sample'] = sample_size

        return self.__class__(request_url, request_params)

    def doi(self, doi):
        self.ENDPOINT.append(doi)
        parts = self.ENDPOINT
        request_url = build_url_endpoint(parts)
        request_params = {}

        result = do_http_request(
            'get', request_url, data=request_params).json()

        return result['message']


class Funders(Endpoint):

    ENDPOINT = [API, 'funders']

    def query(self, *args):

        request_url = build_url_endpoint(self.ENDPOINT)
        request_params = dict(self.request_params)

        if args:
            request_params['query'] = ' '.join(list(args))

        return self.__class__(request_url, request_params)

    def funder(self, funder_id):
        self.ENDPOINT.append(funder_id)
        parts = self.ENDPOINT
        request_url = build_url_endpoint(parts)
        request_params = {}

        result = do_http_request(
            'get', request_url, data=request_params).json()

        return result['message']


class RestfulClient(Works):

    def rate_limits(self):

        endpoint = build_url_endpoint(['members', '1'])

        result = do_http_request('get', endpoint, only_headers=True)

        rate_limits = {
            'X-Rate-Limit-Limit': result.headers.get('X-Rate-Limit-Limit', 'undefined'),
            'X-Rate-Limit-Interval': result.headers.get('X-Rate-Limit-Interval', 'undefined')
        }

        return rate_limits

    @property
    def x_rate_limit_limit(self):

        return self.rate_limits['X-Rate-Limit-Limit']

    @property
    def x_rate_limit_interval(self):

        return self.rate_limits['X-Rate-Limit-Interval']

    @property
    def works(self):

        return Works()
