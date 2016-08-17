#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: view.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""

import sys, os
from os import path
import logging
import time

sys.path.append(path.realpath(path.join(path.dirname(__file__), "..")))

from flask import request, jsonify, make_response

from app_v1_0_0 import api
from utils.auth_check import login_required, create_token, try_login
from zepservice import ZepService
from utils.schema import ZENOSS_QUEUE_SCHEMA
from utils.db_manager import DataManager
from utils.event import EventCompatInfo, EventCompatDetailInfo
from utils.marshallEvt import marshal
from utils.basic import send_success

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
def get_events():
    return events_query()


def events_query(limit=5, start=0, sort='lastTime', dir='desc', params=None, exclusion_filter=None,
                 keys=None, page=None, archive=False, uid=None, detailFormat=False):
    """Query for events.

    @type  limit: integer
    @param limit: (optional) Max index of events to retrieve (default: 0)
    @type  start: integer
    @param start: (optional) Min index of events to retrieve (default: 0)
    @type  sort: string
    @param sort: (optional) Key on which to sort the return results (default:
                 'lastTime')
    @type  dir: string
    @param dir: (optional) Sort order; can be either 'ASC' or 'DESC'
                (default: 'DESC')
    @type  params: dictionary
    @param params: (optional) Key-value pair of filters for this search.
                   (default: None)
    @type  history: boolean
    @param history: (optional) True to search the event history table instead
                    of active events (default: False)
    @type  uid: string
    @param uid: (optional) Context for the query (default: None)
    @rtype:   dictionary
    @return:  B{Properties}:
       - events: ([dictionary]) List of objects representing events
       - totalCount: (integer) Total count of events returned
       - asof: (float) Current time
    """

    zep_srv = ZepService()
    if uid == "/zport/dmd/Devices":
        uid = "/zport/dmd"

    filter = zep_srv._buildFilter(uid, params)
    if exclusion_filter is not None:
        exclusion_filter = zep_srv._buildFilter(uid, exclusion_filter)

    events = zep_srv.getEventSummaries(limit=limit, offset=start,
                                       sort=zep_srv._buildSort(sort, dir),
                                       filter=filter, exclusion_filter=exclusion_filter)

    eventFormat = EventCompatInfo
    if detailFormat:
        eventFormat = EventCompatDetailInfo

    eventObs = [eventFormat(e) for e in events['events']]
    eventDicts = [marshal(evt, keys) for evt in eventObs]

    dataRtn = {
        'events': eventDicts,
        'totalCount': len(eventDicts),
        'asof': time.time()
    }

    return send_success(dataRtn)
    # from pprint import pprint
    # pprint(dataRtn)
    # return dataRtn

if __name__ == '__main__':
    from zope.component import getGlobalSiteManager
    from zenoss.protocols.interfaces import IQueueSchema
    getGlobalSiteManager().registerUtility(ZENOSS_QUEUE_SCHEMA, IQueueSchema)
    events_query()
