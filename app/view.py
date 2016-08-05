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
from . import api

__author__ = "fangfei"
__version__ = "1.0.0"
__maintainer__ = "fangfei"
__email__ = "fangfei@youku.com"
__status__ = "Debug"


@api.route('/')
def index():
    return "Hello World!"

