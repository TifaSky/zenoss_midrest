#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: marshallEvt.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""


def getPublicProperties(obj):
    """
    Get all public __get__'ables like @property's.
    Note: This intentionally ignores regular properties and methods
    """

    keys = [
        key for key in dir(obj) if not key.startswith('_') and not callable(getattr(obj, key))
    ]
    # print keys

    return keys


def _marshalImplicitly(obj):
    """
    Return a dictionary with all the attributes of obj except methods, and
    those that begin with '_'
    """
    data = {}
    for key in getPublicProperties(obj):
        value = getattr(obj, key)
        data[key] = value
    return data


def _marshalExplicitly(obj, keys):
    """
    Convert obj to a dict filtering the results based on a list of keys that is passed in
    """
    data = {}
    for key in keys:
        try:
            value = getattr(obj, key)
        except AttributeError:
            pass
        else:
            if callable(value):
                value = value()
            data[key] = value

    return data


def marshal(obj, keys=None):
    if keys is None:
        data = _marshalImplicitly(obj)
    else:
        data = _marshalExplicitly(obj, keys)

    return data
