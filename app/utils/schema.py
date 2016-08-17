##############################################################################
#
# Copyright (C) Zenoss, Inc. 2011, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


import os
from os import path
import json
import logging
from cStringIO import StringIO
from ConfigParser import ConfigParser
from zope.component import getUtility
from zenoss.protocols.queueschema import Schema
from zenoss.protocols.data.queueschema import SCHEMA
from zenoss.protocols.interfaces import IQueueSchema, IAMQPConnectionInfo


def _parseMessagingConf(file_path=path.join(path.dirname(__file__), "./messaging.conf")):
    s = StringIO()
    try:
        # Need a fake section to parse with ConfigParser
        with open(file_path) as f:
            s.write("[fakesection]\n")
            s.write(f.read())
            s.seek(0)
    except IOError:
        log = logging.getLogger('zen.ZenMessaging')
        log.debug("No user configuration of queues at {path}".format(path=path))
        return {}
    parser = ConfigParser()
    # Prevent lowercasing of option names
    parser.optionxform = str
    parser.readfp(s)
    return dict(parser.items('fakesection'))


def _loadZenossQueueSchemas():
    schemas = [SCHEMA]  # Load the compiled schema
    schema = Schema(*schemas)
    schema.loadProperties(_parseMessagingConf())
    return schema

ZENOSS_QUEUE_SCHEMA = _loadZenossQueueSchemas()
