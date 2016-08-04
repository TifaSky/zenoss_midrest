#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
app view control

"""

# built-in import
import time

# third-party import
from flask import Flask, request, jsonify

# this app-in import

__author__ = "fangfei"
__version__ = "1.0.0"
__maintainer__ = "fangfei"
__email__ = "fangfei@youku.com"
__status__ = "Debug"

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello World!"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)