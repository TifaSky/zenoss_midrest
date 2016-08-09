#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: __init__.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""

from flask import Blueprint

api = Blueprint('api_v1_0_0', __name__)

from . import view
