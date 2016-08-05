#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
jwt token processing and Authorization

"""

# built-in import
from datetime import datetime, timedelta
import os
import sys
from functools import wraps

# third-party importe
from flask import request, jsonify, g
import jwt
from jwt import DecodeError, ExpiredSignature

# this app-in import
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from config import Conf

__author__ = "fangfei"
__version__ = "1.0.0"
__maintainer__ = "fangfei"
__email__ = "fangfei@youku.com"
__status__ = "Debug"


def create_token(user_id):
    pay_load = {
        # subject id
        'sub': user_id,
        # issued at
        'iat': datetime.utcnow(),
        # expiry
        'exp': datetime.utcnow() + timedelta(days=1)
    }

    SECRET_KEY = Conf['SECRET_KEY']
    token = jwt.encode(pay_load, SECRET_KEY, algorithm='HS256')

    return token


def parse_token(req):
    token = req.headers.get('Authorization').split(' ')[1]
    SECRET_KEY = Conf['SECRET_KEY']

    return jwt.decode(token, SECRET_KEY, algorithms='HS256')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.headers.get('Authorization'):
            response = jsonify(message='Missing authorization header')
            response.status_code = 401

            return response

        try:
            payload = parse_token(request)

        except DecodeError:
            response = jsonify(message='Token is invalid')
            response.status_code = 401

            return response

        except ExpiredSignature:
            response = jsonify(message='Token has expired')
            response.status_code = 401

            return response

        g.user_id = payload['sub']

        return f(*args, **kwargs)

    return decorated_function
