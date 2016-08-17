#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: main.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""

from flask import Flask
from zope.component import getGlobalSiteManager
from zenoss.protocols.interfaces import IQueueSchema

from utils.switch_env import config
import setting
from utils.schema import ZENOSS_QUEUE_SCHEMA


def create_app():
    getGlobalSiteManager().registerUtility(ZENOSS_QUEUE_SCHEMA, IQueueSchema)

    app = Flask(__name__)

    app.config.from_object(config)
    app.sercret_key = app.config['SECRET_KEY']
    app.debug = app.config['DEBUG']

    from app_v1_0_0 import api as api_blueprint_v1_0_0
    app.register_blueprint(api_blueprint_v1_0_0, url_prefix='/api_v1_0_0')

    return app


def create_app2(ConfObj):
    getGlobalSiteManager().registerUtility(ZENOSS_QUEUE_SCHEMA, IQueueSchema)

    app = Flask(__name__)

    app.config.from_object(ConfObj)
    app.sercret_key = app.config['SECRET_KEY']
    app.debug = app.config['DEBUG']
    app.log_files = []

    from app_v1_0_0 import api as api_blueprint_v1_0_0
    app.register_blueprint(api_blueprint_v1_0_0, url_prefix='/api_v1_0_0')
    app.log_files.append('app_v1_0_0')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.debug, host='0.0.0.0', port=5001)
