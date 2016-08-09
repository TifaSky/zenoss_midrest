#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from utils.switch_env import ConfigBase

"""
File: config.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""


class Config(ConfigBase):
    SECRET_KEY = 's0me secret key string'
    DEBUG = True

    DEFAULT_ACCESS_LOG = './logs/access.log'
    DEFAULT_ERROR_LOG = './logs/error.log'
    ROOT_LOG = './logs/app.log'
    ROOT_LOG_LEVEL = logging.DEBUG
    LOG_BASE_FORMAT = "%(asctime)s %(levelname)s (%(filename)s:%(lineno)s) - %(message)s"
    LOG_APP_LEVEL = logging.WARNING


class DevelopmentConfig(Config):
    __confname__ = "dev"


class ProductionConfig(Config):
    __confname__ = "prod"
    DEBUG = False

Conf = DevelopmentConfig
