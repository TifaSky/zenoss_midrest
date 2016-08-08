#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: run.py
Author: fangfei
Email: fangfei@youku.com
Description: simple development lancher
"""

from flask import Flask

from app.config import Conf


def create_app():
    app = Flask(__name__)

    app.config.from_object(Conf)
    app.sercret_key = app.config['SECRET_KEY']
    app.debug = app.config['DEBUG']

    from app import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.debug, host='0.0.0.0', port=5001)
