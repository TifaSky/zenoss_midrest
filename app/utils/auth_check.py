#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: auth_check.py
Author: fangfei
Email: fangfei@youku.com
Description: jwt token processing and ldap Authorization
"""

from datetime import datetime, timedelta
import os
import sys
from functools import wraps
import logging

from flask import request, jsonify, g
import jwt
from jwt import DecodeError, ExpiredSignature
import ldap

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from utils.switch_env import get_env_var, refresh_config, config
import setting

logger = logging.getLogger('app')


def try_login(user_id, passwd):
    rtn_code = 0
    msg = ''

    try:
        ld_conn = ldap.initialize(config.LDAP_URI)
        ld_conn.protocol_version = ldap.VERSION3

        ld_conn.simple_bind(config.LDAP_USR, config.LDAP_CREDENTIALS)
        search_filter = "(%s=%s)" % (config.LDAP_SEARCH_FILTER, user_id)
        retrieveAttrs = None

        ld_rs_id = ld_conn.search(config.LDAP_SEARCH_BASE, ldap.SCOPE_SUBTREE, search_filter, retrieveAttrs)
        rs_type, rs_data = ld_conn.result(ld_rs_id, 1)
        if(not len(rs_data) == 0):
            rs_route, rs_detail = rs_data[0]
            if rs_route is not None:
                # get real dn
                user_dn = rs_route

                # valid password
                ld_conn.simple_bind_s(user_dn, passwd)

                rtn_code = 1
                msg = 'Login success'
            else:
                rtn_code = 0
                msg = 'User not found'
                logger.warn("User[%s] not found" % user_id)
        else:
            rtn_code = 0
            msg = 'User not found'
            logger.warn("User[%s] not found" % user_id)
    except ldap.INVALID_CREDENTIALS, e:
        rtn_code = 0
        msg = 'Invalid credentials'
        logger.warn("User[%s] login faild: %s" % (user_id, str(e)))
    except ldap.LDAPError, e:
        print e
        rtn_code = 0
        msg = 'Login failed'
        logger.error("User[%s] login faild: %s" % (user_id, str(e)))
    except Exception, e:
        rtn_code = 0
        msg = 'Login failed'
        logger.error("User[%s] login faild: %s" % (user_id, str(e)))
    finally:
        ld_conn.unbind()
        del ld_conn

    return rtn_code, msg


def create_token(user_id):
    pay_load = {
        # subject id
        'sub': user_id,
        # issued at
        'iat': datetime.utcnow(),
        # expiry
        'exp': datetime.utcnow() + timedelta(days=1)
    }

    SECRET_KEY = config.SECRET_KEY
    token = jwt.encode(pay_load, SECRET_KEY, algorithm='HS256')

    return token


def parse_token(req):
    token = req.headers.get('Authorization').split(' ')[1]
    SECRET_KEY = config.SECRET_KEY

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


if __name__ == '__main__':
    os.environ[get_env_var()] = 'dev'
    refresh_config()
    print create_token('feifei')
