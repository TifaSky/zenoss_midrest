#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
app setting file

"""


class Config(object):
    SECRET_KEY = 's0me secret key string'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

Conf = DevelopmentConfig
