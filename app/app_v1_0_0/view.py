#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
app view control

"""

# built-in import
import logging
# third-party import
from flask import request, jsonify, make_response

# this app-in import
from . import api
from utils.auth_check import login_required, create_token

__author__ = "fangfei"
__version__ = "1.0.0"
__maintainer__ = "fangfei"
__email__ = "fangfei@youku.com"
__status__ = "Debug"

logger = logging.getLogger('app_v1_0_0')


@api.route('/')
def index():
    logger.info('test-helloworld')
    return "Hello World!"


@api.route('/authenticate', methods=['POST'])
def auth_user():
    chk_username = request.form.get('username', '')
    chk_password = request.form.get('password', '')

    if chk_username != '' or chk_password != '':
        if chk_username == 'admin' and chk_password == 'admin':
            return jsonify({'token': 'TOK ' + create_token(chk_username)})

    response = make_response(jsonify({"message": "invalid username/password"}))
    response.status_code = 401
    return response


@api.route('/events', methods=['GET'])
@login_required
def get_events():
    pass
