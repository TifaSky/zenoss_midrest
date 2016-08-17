#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: db_manager.py
Author: fangfei
Email: fangfei@youku.com
Description:
"""

import os
import sys
import logging

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

import MySQLdb
import memcache

from utils.switch_env import config
import setting

logger = logging.getLogger('app')


class DataManager(object):
    """connect to mysql
    """

    def __init__(self):
        self._loadMysqlConfig()
        self._loadMemcacheConfig()

    def _loadMysqlConfig(self):
        self.dbhost = config.DB_HOST
        self.dbport = config.DB_PORT
        self.dbuser = config.DB_USER
        self.dbname = config.DB_NAME
        self.passwd = 'YW20080707yw'

    def _loadMemcacheConfig(self):
        self.memhost = '127.0.0.1'
        self.memport = 11211

    def _connect(self):
        try:
            self.conn = MySQLdb.connect(db=self.dbname, user=self.dbuser, passwd=self.passwd,
                                        host=self.dbhost, port=int(self.dbport))
        except Exception, e:
            print e
            logger.warn(e)

    def _disconnect(self):
        self.conn.close()

    def queryDB(self, sql, sqlPara=None):
        dataRtn = {'flag': 0, 'message': []}

        try:
            self._connect()
            self.cur = self.conn.cursor()
            self.cur.execute(sql, sqlPara)
            data = self.cur.fetchall()
            dataRtn = {'flag': 0, 'message': data}

        except Exception, e:
            logger.warn(e)
            return {'flag': 1, 'message': str(e)}
        finally:
            self.cur.close()
            self._disconnect()

        return dataRtn

    def queryCache(self, key_str):
        cache_uri = "%s:%s" % (self.memhost, self.memport)
        dataRtn = None

        try:
            self.mc = memcache.Client([cache_uri], debug=0)
            dataRtn = self.mc.get(key_str)
        except Exception, e:
            print e
            logger.warn(e)

        return dataRtn

    def getPathFromUuid(self, uuid_str):
        dataRtn = None
        cache_rs = self.queryCache(uuid_str)

        if cache_rs is None:
            sql = """ select path, name, key_error
                      from uuid_to_pathname
                      where uuid = %s
                  """
            rs_sql = self.queryDB(sql, (uuid_str,))
            if rs_sql['flag'] == 0 and len(rs_sql['message']) > 0:
                rs_path = rs_sql['message'][0][0]
                rs_name = rs_sql['message'][0][1]

                self.mc.set(uuid_str, rs_path)
                if str(rs_name).strip() != '':
                    self.mc.set(rs_path, rs_name)

                dataRtn = rs_path

        return dataRtn

    def getNameFromPath(self, path_str):
        dataRtn = None
        cache_rs = self.queryCache(path_str)

        if cache_rs is None:
            sql = """ select path, name, key_error, uuid
                      from uuid_to_pathname
                      where path = %s
                  """
            rs_sql = self.queryDB(sql, (path_str,))
            if rs_sql['flag'] == 0 and len(rs_sql['message']) > 0:
                rs_path = rs_sql['message'][0][0]
                rs_name = rs_sql['message'][0][1]
                uuid_str = rs_sql['message'][0][3]

                self.mc.set(uuid_str, rs_path)
                if str(rs_name).strip() != '':
                    self.mc.set(rs_path, rs_name)
                    dataRtn = rs_name

        return dataRtn

    def getNameFromUuid(self, uuid_str):
        rs_path = self.getPathFromUuid(uuid_str)
        if rs_path is not None:
            cache_rs = self.queryCache(rs_path)
            if cache_rs is not None:
                return cache_rs

        return None
