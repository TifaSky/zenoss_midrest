#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
app setting file

"""

# built-in import

# third-party import

# this app-in import

__author__ = "fangfei"
__version__ = "1.0.0"
__maintainer__ = "fangfei"
__email__ = "fangfei@youku.com"
__status__ = "Debug"


class Config(object):
    SECRET_KEY = 's0me secret key string'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

Conf = DevelopmentConfig
