#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
app lancher

"""

# built-in import

# third-party import
from flask import Flask

# this app-in import
from app.config import Conf

__author__ = "fangfei"
__version__ = "1.0.0"
__maintainer__ = "fangfei"
__email__ = "fangfei@youku.com"
__status__ = "Debug"

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
