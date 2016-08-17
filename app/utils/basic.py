#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: basic.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""
import os
import sys
import datetime
import time

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import pytz
from tzlocal import get_localzone
from flask import jsonify

from utils.switch_env import config
import setting


local_tz = get_localzone()


def safeTuple(arg):
    """
    >>> safeTuple(["foo", "blam"])
    ('foo', 'blam')
    >>> safeTuple([])
    ()
    >>> safeTuple(None)
    ()
    >>> safeTuple("foo")
    ('foo',)
    """
    if arg is not None:
        return tuple(arg) if hasattr(arg, '__iter__') else (arg,)
    else:
        return ()


def _maybenow(gmtSecondsSince1970):
    if gmtSecondsSince1970 is None:
        return time.time()
    return int(gmtSecondsSince1970)


def isoToTimestamp(value):
    """converts a iso time string that does not contain a timezone, ie.
    YYYY-MM-DD HH:MM:SS, to a timestamp in seconds since 1970; uses the system timezone.
    """

    timeStr = value.replace('T', ' ')
    timeTuple = time.strptime(timeStr, '%Y-%m-%d %H:%M:%S')
    timestamp = time.mktime(timeTuple)

    return timestamp


def isoDateTime(gmtSecondsSince1970=None):
    value = _maybenow(gmtSecondsSince1970)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(value))


def isoDateTimeFromMilli(milliseconds):
    """
    @param milliseconds:: UTC timestamp in milliseconds
    """
    return isoDateTime(milliseconds / 1000)


def convertAttribute(numbValue, conversions):
    if numbValue is None:
        return 'Unkown'

    numbValue = int(numbValue)
    for line in conversions:
        line = line.rstrip()
        (name, number) = line.split(':')
        if int(number) == numbValue:
            return name

    return numbValue


def convertProdState(prodState):
    return convertAttribute(prodState, config.PRODSTATECONVERSIONS)


def convertPriority(DevicePriority):
    return convertAttribute(DevicePriority, config.PRIORITYCONVERSIONS)


def convert_data(val):
    """将Python数据转化为json时,日期类型数据转化
    date/datetime -> iso字符串
    """

    if type(val) == dict:
        converted = {}

        for k in val:
            if type(k) != unicode and type(k) != str:
                raise TypeError('The key of dict must be strings.')
            converted[k] = convert_data(val[k])

        return converted
    elif type(val) == list or type(val) == set:
        converted = []

        for v in val:
            converted.append(convert_data(v))

        return converted
    elif type(val) == datetime.datetime or type(val) == datetime.date:
        return utc_isoformat(val)
    else:
        return val


def utc_isoformat(date):
    """把日期值转化为utc ISO 8601标准格式
    以便js能够简单的转化 new Date(date_str)
    """

    aware = local_tz.localize(date, is_dist=None)
    aware.astimezone(pytz.utc)

    return aware.isoformat()


# API接口调用后,返回json
# 调用成功: sucess=True, date=respose
# 调用失败: sucess=False, msg=error msg
def send_success(data=None):
    """调用成功返回数据到前端
    数据字典的key必须是字符型
    """

    return jsonify({
        'sucess': True,
        'data': convert_data(data)
    })


def send_error(msg=""):

    return jsonify({
        'sucess': False,
        'msg': msg or "request failed on the server!"
    })
