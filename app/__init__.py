#!/usr/bin/env python
# -*- coding: utf-8 -*-

# built-in import

# third-party import
from flask import Blueprint

# this app-in import

__author__ = "fangfei"
__version__ = "1.0.0"
__maintainer__ = "fangfei"
__email__ = "fangfei@youku.com"
__status__ = "Debug"

api = Blueprint('api', __name__)

from . import view
