# -*- coding: utf-8 -*-
"""
    eve-swagger.validation
    ~~~~~~~~~~~~~~~~~~~~~~
    swagger.io extension for Eve-powered REST APIs.

    :copyright: (c) 2015 by Nicola Iarocci.
    :license: BSD, see LICENSE for more details.
"""
from eve.exceptions import ConfigException
from flask import current_app as app
from cerberus import Validator

import eve_swagger

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


def validate_info():
    v = Validator()
    schema = {
        'title': {'required': True, 'type': 'string'},
        'version': {'required': True, 'type': 'string'},
        'description': {'type': 'string'},
        'termsOfService': {'type': 'string'},
        'contact': {
            'type': 'dict',
            'schema': {
                'name': {'type': 'string'},
                'url': {'type': 'string', 'validator': _validate_url},
                'email': {
                    'type': 'string',
                    'regex':
                    '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                }
            }
        },
        'license': {
            'type': 'dict',
            'schema': {
                'name': {'type': 'string', 'required': True},
                'url': {'type': 'string', 'validator': _validate_url}
            }
        },
    }
    if eve_swagger.INFO not in app.config:
        raise ConfigException('%s setting is required in Eve configuration.' %
                              eve_swagger.INFO)

    if not v.validate(app.config[eve_swagger.INFO], schema):
        raise ConfigException('%s is misconfigured: %s' % (
            eve_swagger.INFO, v.errors))


def validate_security_definitions():
    v = Validator()
    schema = {
        'securityDefinitions': {
            'type': 'dict',
            'valueschema': {'type': 'dict', 'oneof': [
                {  # basic
                    'schema': {
                        'type': {'required': True, 'type': 'string',
                                 'allowed': ['basic']},
                        'description': {'type': 'string'}
                    }
                },
                {  # apiKey
                    'schema': {
                        'type': {'required': True, 'type': 'string',
                                 'allowed': ['apiKey']},
                        'description': {'type': 'string'},
                        'name': {'required': True, 'type': 'string'},
                        'in': {'required': True, 'type': 'string'}
                    }
                },
                {  # oauth2: 'implicit',
                    'schema': {
                        'type': {'required': True, 'type': 'string',
                                 'allowed': ['oauth2']},
                        'description': {'type': 'string'},
                        'flow': {'required': True, 'type': 'string',
                                 'allowed': ['implicit']},
                        'authorizationUrl': {'required': True,
                                             'type': 'string',
                                             'validator': _validate_url},
                        # TODO probably too weak
                        'scopes': {'required': True, 'type': 'dict'}
                    }
                },
                {  # oauth2: 'password', 'application'
                    'schema': {
                        'type': {'required': True, 'type': 'string',
                                 'allowed': ['oauth2']},
                        'description': {'type': 'string'},
                        'flow': {'required': True, 'type': 'string',
                                 'allowed': ['password', 'application']},
                        'tokenUrl': {'required': True, 'type': 'string',
                                     'validator': _validate_url},
                        # TODO probably too weak
                        'scopes': {'required': True, 'type': 'dict'}
                    }
                },
                {  # oauth2 'accessCode'
                    'schema': {
                        'type': {'required': True, 'type': 'string',
                                 'allowed': ['oauth2']},
                        'description': {'type': 'string'},
                        'flow': {'required': True, 'type': 'string',
                                 'allowed': ['accessCode']},
                        'authorizationUrl': {'required': True,
                                             'type': 'string',
                                             'validator': _validate_url},
                        'tokenUrl': {'required': True, 'type': 'string',
                                     'validator': _validate_url},
                        # TODO probably too weak
                        'scopes': {'required': True, 'type': 'dict'}
                    }
                }]
            }
        }
    }
    if eve_swagger.SECURITY_DEFINITIONS in app.config:
        document = {
            'securityDefinitions': app.config[eve_swagger.SECURITY_DEFINITIONS]
        }
        if not v.validate(document, schema):
            raise ConfigException('%s is misconfigured: %s definitions: %s' % (
                eve_swagger.SECURITY_DEFINITIONS, v.errors,
                app.config[eve_swagger.SECURITY_DEFINITIONS]))


def _validate_url(field, value, error):
    # TODO probably too weak
    o = urlparse(value)
    if not bool(o.scheme):
        error(field, 'Invalid URL')
