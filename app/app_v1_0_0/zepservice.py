#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: zepservice.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""

import logging
import sys, os
from os import path
from functools import partial
from json import loads
import re

sys.path.append(path.realpath(path.join(path.dirname(__file__), "..")))

from zenoss.protocols.interfaces import IQueueSchema
from zenoss.protocols.services.zep import ZepServiceClient, ZepConfigClient
from zenoss.protocols.jsonformat import to_dict, from_dict
from zenoss.protocols.protobufs.zep_pb2 import EventSort, EventFilter
from zenoss.protocols.protobufutil import listify
from zope.component import getUtility

from utils.switch_env import config
import setting
from utils.basic import safeTuple, isoToTimestamp

logger = logging.getLogger('app_v1_0_0')


class InvalidQueryParameterException(Exception):
    """Raised when a query is attempted with invalid search criteria.
    """


class ZepService(object):

    DEFAULT_SORT_MAP = {
        'eventstate': {'field': EventSort.STATUS},
        'severity': {'field': EventSort.SEVERITY},
        'firsttime': {'field': EventSort.FIRST_SEEN},
        'lasttime': {'field': EventSort.LAST_SEEN},
        'eventclass': {'field': EventSort.EVENT_CLASS},
        'device': {'field': EventSort.ELEMENT_TITLE},
        'component': {'field': EventSort.ELEMENT_SUB_TITLE},
        'count': {'field': EventSort.COUNT},
        'summary': {'field': EventSort.EVENT_SUMMARY},
        'ownerid': {'field': EventSort.CURRENT_USER_NAME},
        'agent': {'field': EventSort.AGENT},
        'monitor': {'field': EventSort.MONITOR},
        'eventkey': {'field': EventSort.EVENT_KEY},
        'evid': {'field': EventSort.UUID},
        'statechange': {'field': EventSort.STATUS_CHANGE},
        'dedupid': {'field': EventSort.FINGERPRINT},
        'eventclasskey': {'field': EventSort.EVENT_CLASS_KEY},
        'eventgroup': {'field': EventSort.EVENT_GROUP},
    }

    SORT_DIRECTIONAL_MAP = {
        'asc': EventSort.ASCENDING,
        'desc': EventSort.DESCENDING,
    }

    ZENOSS_DETAIL_OLD_TO_NEW_MAPPING = {
        'prodState': "zenoss.device.production_state",
        'DevicePriority': "zenoss.device.priority",
        'ipAddress': 'zenoss.device.ip_address',
        'Location': 'zenoss.device.location',
        'DeviceGroups': 'zenoss.device.groups',
        'Systems': 'zenoss.device.systems',
        'DeviceClass': 'zenoss.device.device_class'
    }
    ZENOSS_DETAIL_NEW_TO_OLD_MAPPING = dict((new, old) for old, new in ZENOSS_DETAIL_OLD_TO_NEW_MAPPING.iteritems())

    COUNT_REGEX = re.compile(r'^(?P<from>\d+)?:?(?P<to>\d+)?$')

    def __init__(self):
        zep_url = config.ZEP_URI
        schema = getUtility(IQueueSchema)
        self.client = ZepServiceClient(zep_url, schema)

    def _create_identifier_filter(self, value):
        if not isinstance(value, (tuple, list, set)):
            value = (value,)
        return map(lambda s: str(s).strip(), value)

    def _createFullTextSearch(self, parameter):
        if not hasattr(parameter, '__iter__'):
            parameter = (parameter,)
        return map(lambda s: str(s).strip(), parameter)

    def _timeRange(self, timeRange):
        d = {
            'start_time': timeRange[0],
        }

        if len(timeRange) == 2:
            d['end_time'] = timeRange[1]

        return d

    def _timestampRange(self, timestampRange):
        try:
            values = []
            for t in timestampRange.split('/'):
                values.append(int(isoToTimestamp(t)) * 1000)
            return values
        except ValueError:
            logger.warning("Invalid timestamp: %s" % timestampRange)
            return ()

    def _createEventDetailFilter(self, details):
        """
        @param details: All details present in this filter request.

        Example: {
            'zenoss.device.production_state' = 4,
            'zenoss.device.priority' : 2
        }

        @type details: dict
        """

        detailFilterItems = []

        for key, val in details.iteritems():
            detailFilterItems.append({
                'key': key,
                'value': val,
            })

        logger.debug('Final detail filter: %r' % detailFilterItems)
        return detailFilterItems

    def _getEventSort(self, sortParam):
        eventSort = {}

        if isinstance(sortParam, (list, tuple)):
            field, direction = sortParam
            eventSort['direction'] = self.SORT_DIRECTIONAL_MAP[direction.lower()]
        else:
            field = sortParam

        eventSort.update(getDetailsInfo().getSortMap()[field.lower()])

        return from_dict(EventSort, eventSort)

    def _getEventSummaries(self, source, offset, limit=1000):
        response, content = source(offset=offset, limit=limit)

        return {
            'total': content.total,
            'limit': content.limit,
            'next_offset': content.next_offset if content.HasField('next_offset') else None,
            'events': (to_dict(event) for event in content.events),
        }

    def getEventSummaries(self, offset, limit=1000, sort=None, filter=None, exclusion_filter=None):
        client_fn = self.client.getEventSummaries

        if filter is not None and isinstance(filter, dict):
            filter = from_dict(EventFilter, filter)
        if exclusion_filter is not None and isinstance(exclusion_filter, dict):
            exclusion_filter = from_dict(EventFilter, exclusion_filter)
        if sort is not None:
            sort = tuple(self._getEventSort(s) for s in safeTuple(sort))

        result = self._getEventSummaries(source=partial(client_fn,
                                         filter=filter,
                                         exclusion_filter=exclusion_filter,
                                         sort=sort),
                                         offset=offset, limit=limit)

        return result

    def createEventFilter(self, severity=(), status=(), event_class=(),
                          first_seen=None, last_seen=None, status_change=None, update_time=None,
                          count_range=None, element_identifier=(), element_title=(),
                          element_sub_identifier=(), element_sub_title=(), uuid=(),
                          event_summary=None, tags=(), fingerprint=(), agent=(), monitor=(),
                          event_key=(), current_user_name=(), subfilter=(), operator=None,
                          details=None, event_class_key=(), event_group=(), message=()):
        """Creates a filter based on passed arguments.
        Caller is responsible for handling the include-zero-items case.
        For example, passing an empty uuid tuple won't filter by uuid so includes everything.
        """

        filter = {}

        if uuid:
            filter['uuid'] = uuid

        if event_summary:
            filter['event_summary'] = self._createFullTextSearch(event_summary)

        if event_class:
            filter['event_class'] = event_class

        if status:
            filter['status'] = status

        if severity:
            filter['severity'] = severity

        if first_seen:
            filter['first_seen'] = self._timeRange(first_seen)

        if last_seen:
            filter['last_seen'] = self._timeRange(last_seen)

        if status_change:
            filter['status_change'] = self._timeRange(status_change)

        if update_time:
            filter['update_time'] = self._timeRange(update_time)

        # These tags come from params, which means for some reason someone is filtering manually on a tag.
        if tags:
            filter['tag_filter'] = {'tag_uuids': tags}

        if count_range:
            if not isinstance(count_range, (tuple, list)):
                try:
                    count = int(count_range)
                    count_range = (count, count)
                except ValueError:
                    match = ZepService.COUNT_REGEX.match(count_range)
                    if not match:
                        raise ValueError('Invalid range: %s' % (count_range))
                    count_range = (match.group('from'), match.group('to'))

            filter['count_range'] = {}
            count_from, count_to = count_range
            if count_from is not None:
                filter['count_range']['from'] = int(count_from)
            if count_to is not None:
                filter['count_range']['to'] = int(count_to)

        if element_identifier:
            filter['element_identifier'] = self._create_identifier_filter(element_identifier)

        if element_title:
            filter['element_title'] = self._create_identifier_filter(element_title)

        if element_sub_identifier:
            filter['element_sub_identifier'] = self._create_identifier_filter(element_sub_identifier)

        if element_sub_title:
            filter['element_sub_title'] = self._create_identifier_filter(element_sub_title)

        if fingerprint:
            filter['fingerprint'] = fingerprint

        if agent:
            filter['agent'] = agent

        if monitor:
            filter['monitor'] = monitor

        if event_key:
            filter['event_key'] = event_key

        if current_user_name:
            filter['current_user_name'] = current_user_name

        if subfilter:
            filter['subfilter'] = subfilter

        if details:
            filter['details'] = self._createEventDetailFilter(details)

        if event_class_key:
            filter['event_class_key'] = event_class_key

        if event_group:
            filter['event_group'] = event_group

        if message:
            filter['message'] = self._createFullTextSearch(message)

        # Everything's repeated on the protobuf, so listify
        result = dict((k, listify(v)) for k, v in filter.iteritems())

        if operator:
            result['operator'] = operator

        return result

    def getDetailsMap(self):
        """Return a mapping of detail keys to dicts of detail items"""
        return getDetailsInfo().getDetailsMap()

    def parseParameterDetails(self, parameters):
        """Given grid parameters, split into keys that are details and keys that are other parameters"""

        params = {}
        details = {}

        detail_keys = self.getDetailsMap().keys()
        for k, v in parameters.iteritems():
            if k in self.ZENOSS_DETAIL_OLD_TO_NEW_MAPPING:
                k = self.ZENOSS_DETAIL_OLD_TO_NEW_MAPPING[k]
            if k in detail_keys:
                details[k] = v
            else:
                params[k] = v

        # verify parameters against known valid ones
        # If there's an extra, it either needs to be added or
        # is an invalid detail that can't be searched
        leftovers = set(s.lower() for s in params) - set(self.DEFAULT_SORT_MAP) - set(('tags',
                                                                                       'deviceclass',
                                                                                       'systems',
                                                                                       'location',
                                                                                       'devicegroups',
                                                                                       'message'))
        if leftovers:
            raise InvalidQueryParameterException("Invalid query parameters specified: %s" % ', '.join(leftovers))

        return params, details

    def _buildSort(self, sort='lastTime', dir='desc'):
        sort_list = [(sort, dir)]

        # Add secondary sort of last time descending
        if sort not in ('lastTime', 'evid'):
            sort_list.append(('lastTime', 'desc'))
        return sort_list

    def _buildFilter(self, uid, params, specificEventUuids=None):
        """Construct a dzictionary that can be converted into an EventFilter protobuf

        @type  uid: string
        @param uid: (optional) Context for the query (default: None)
        @type  params: dictionary
        @param params: (optional) Key-value pair of filters for this search(default: None)
        """

        if params:
            logger.debug('logging params for building filter: %s', params)
            if isinstance(params, basestring):
                params = loads(params)

            # params comes from the grid's filtering column -
            # some of these properties are normal properties on an event
            # while others are considered event details. Separate the two here
            params, details = self.parseParameterDetails(params)

            filterEventUuids = []
            # No specific event uuids passed in
            # check for event ids from the grid parameters
            if specificEventUuids is None:
                logger.debug('No specific event uuids were passed in.')

                # The evid's from params only ever mean anything for filtering
                # if specific uuids are passed in, this filter will ignore the grid
                # parameters and just act on or filter using these specific event uuids
                evid = params.get('evid')
                if evid:
                    if not isinstance(evid, (list, tuple)):
                        evid = [evid]
                    filterEventUuids.extend(evid)
            # Specific event uuids were passed in, use those for this filter
            else:
                logger.debug('Specific event uuids passed in: %s', specificEventUuids)
                if not isinstance(specificEventUuids, (list, tuple)):
                    filterEventUuids = [specificEventUuids]
                else:
                    filterEventUuids = specificEventUuids

            logger.debug('FilterEventUuids is: %s', filterEventUuids)

            event_filter = self.createEventFilter(
                severity=params.get('severity'),
                status=[i for i in params.get('eventState', [])],
                event_class=filter(None, [params.get('eventClass')]),
                first_seen=params.get('firstTime') and self._timestampRange(params.get('firstTime')),
                last_seen=params.get('lastTime') and self._timestampRange(params.get('lastTime')),
                status_change=params.get('stateChange') and self._timestampRange(params.get('stateChange')),
                uuid=filterEventUuids,
                count_range=params.get('count'),
                element_title=params.get('device'),
                element_sub_title=params.get('component'),
                event_summary=params.get('summary'),
                current_user_name=params.get('ownerid'),
                agent=params.get('agent'),
                monitor=params.get('monitor'),
                fingerprint=params.get('dedupid'),

                # 'tags' comes from managed object guids.
                # see Zuul/security/security.py
                tags=params.get('tags'),

                details=details,
                event_key=params.get('eventKey'),
                event_class_key=params.get('eventClassKey'),
                event_group=params.get('eventGroup'),
                message=params.get('message'),
            )
            logger.debug('Found params for building filter, ended up building  the following:')
            logger.debug(event_filter)

        elif specificEventUuids:
            # if they passed in specific uuids but not other parameters
            event_filter = self.createEventFilter(uuid=specificEventUuids)

        else:
            logger.debug('Did not get parameters, using empty filter.')
            event_filter = {}

        # TODO parameter uid process ?

        logger.debug('Final filter will be:')
        logger.debug(event_filter)

        return event_filter


class ZepDetailsInfo:
    """Contains information about the indexed event details on ZEP
    """

    def __init__(self):
        zep_url = config.ZEP_URI
        schema = getUtility(IQueueSchema)
        self._configClient = ZepConfigClient(zep_url, schema)
        self._initialized = False

    def _initDetails(self):
        self._sortMap = dict(ZepService.DEFAULT_SORT_MAP)
        response, content = self._configClient.getDetails()

        detailsResponseDict = to_dict(content)
        self._details = detailsResponseDict.get('details', [])
        self._unmappedDetails = []
        self._detailsMap = {}

        for detail_item in self._details:
            detailKey = detail_item['key']
            sortField = {'field': EventSort.DETAIL, 'detail_key': detailKey}

            mappedName = ZepService.ZENOSS_DETAIL_NEW_TO_OLD_MAPPING.get(detailKey, None)
            # If we have a mapped name, add it to the sort map to support sorting using old or new names
            if mappedName:
                self._sortMap[mappedName.lower()] = sortField
            else:
                self._unmappedDetails.append(detail_item)

            self._sortMap[detailKey.lower()] = sortField
            self._detailsMap[detailKey] = detail_item

        self._initialized = True

    def reload(self):
        """Reloads the event details configuration from ZEP
        """

        self._initialized = False
        self._initDetails()

    def getDetails(self):
        """Retrieve all of the indexed detail item
        @return type list of EventDetailItem dicts
        """

        if not self._initialized:
            self._initDetails()
        return self._details

    def getUnmappedDetails(self):
        """Return only non-zenoss details. This is used to get details that will not be mapped to another key
        (zenoss.device.production_state maps back to prodState, so will be excluded here)
        """

        if not self._initialized:
            self._initDetails()
        return self._unmappedDetails

    def getDetailsMap(self):
        """Return a mapping of detail keys to dicts of detail items
        """

        if not self._initialized:
            self._initDetails()
        return self._detailsMap

    def getSortMap(self):
        """Returns a mapping of a lowercase event field name to a dictionary which can be used
        to build the EventSort object to pass to ZEP
        """

        if not self._initialized:
            self._initDetails()
        return self._sortMap


# Lazy-loaded cache of event details from ZEP
_ZEP_DETAILS_INFO = []


def getDetailsInfo():
    if not _ZEP_DETAILS_INFO:
        _ZEP_DETAILS_INFO.append(ZepDetailsInfo())
    return _ZEP_DETAILS_INFO[0]
