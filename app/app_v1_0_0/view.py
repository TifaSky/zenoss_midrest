#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: view.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""

import logging

from flask import request, jsonify, make_response

from . import api
from utils.auth_check import login_required, create_token, try_login

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
        rtn_code, msg = try_login(chk_username, chk_password)
        if rtn_code == 1:
            return jsonify({'token': 'TOK ' + create_token(chk_username)})
        else:
            return jsonify({'message': msg})

    response = make_response(jsonify({"message": "invalid username/password"}))
    response.status_code = 401
    return response


@api.route('/events', methods=['GET'])
@login_required
def get_events():
    pass
