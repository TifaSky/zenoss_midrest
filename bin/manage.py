#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Server run manager

Usage:
    manage.py [debug] [--config=<confname>] --host=<ip> [--port=<number>] [--workers=<number>] [--maxrequests=<number>] [--accesslog=<File>] [--errorlog=<File>]
    manage.py (-h | --help)

Options:
    -h --help                Show this screen
    debug                    run debug mode
    --config=<confname>      conig name [default: dev]
    --host=<ip>              host ip
    --port=<number>          port [default: 5001]
    --workers=<numnber>      the numnber of workers [default: 1]
    --maxrequests=<number>   max request limit [default: 10000]
    --accesslog=<File>       access log file name [default: ./access.log]
    --errorlog=<File>        error log file name [default: ./error.log]

"""

import sys, os
from os import path

sys.path.append(
    path.realpath(
        path.join(path.dirname(__file__), "../app")
    )
)
import multiprocessing
import logging
from logging import Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler

from docopt import docopt

# 根据环境变量激活配置
from utils.switch_env import get_env_var, refresh_config, config
import setting
from utils.outputdependhandler import OutputDependHandler


# 计算CPU核数，默认worker数量为2*CPU + 1
DEFAULT_WORKERS = multiprocessing.cpu_count() * 2 + 1


def init_app_logger(app):
    # DEBUG模式日志
    if app.debug:
        handler = OutputDependHandler(
            TimedRotatingFileHandler(
                config.DEFAULT_ERROR_LOG, 'D', 1, 30),
            (StreamHandler(sys.stdout)))
        handler.setLevel(config.LOG_APP_LEVEL)
        handler.setFormatter(Formatter(config.LOG_BASE_FORMAT))

        app.logger.addHandler(handler)

    handler_root = OutputDependHandler(
        TimedRotatingFileHandler(
            config.ROOT_LOG, 'D', 1, 30),
        (StreamHandler(sys.stdout)))
    handler_root.setLevel(config.ROOT_LOG_LEVEL)
    handler_root.setFormatter(Formatter(config.LOG_BASE_FORMAT))

    logging.getLogger().addHandler(handler_root)
    logging.getLogger().setLevel(config.ROOT_LOG_LEVEL)


def _prepare_flask_app(confname):
    os.environ[get_env_var()] = confname
    refresh_config()

    from main import create_app2
    app = create_app2(config)
    init_app_logger(app)

    # print app.config

    return app


def debug_server(config='dev', host='0.0.0.0', port=5001, **options):
    """调试运行Web API Service

    @=config, c
    @=host, h
    @=port, p
    """
    app = _prepare_flask_app(config)
    port = int(port)

    app.run(host=host, port=port, debug=app.debug)


def gunicorn_server(
        config='dev',
        host='0.0.0.0', port=5001,
        workers=DEFAULT_WORKERS,
        max_requests=10000,
        accesslog=config.DEFAULT_ACCESS_LOG,
        errorlog=config.DEFAULT_ERROR_LOG,
        **options):
    """以Gunicorn Application模式运行Service

    @=config, config
    @=host, handler
    @=port, port
    @=workers, w
    @=max_requests
    @=accesslog
    @=errorlog
    """
    del sys.argv[1:]

    port = int(port)
    print "listening at http://%s:%s" % (host, port,)
    print "request access logging file: %s" % accesslog
    print "request error logging file: %s" % errorlog

    from gunicorn.app.base import Application

    class FlaskApplication(Application):
        def init(self, parser, opts, args):
            gunicorn_options = {
                'bind': '{0}:{1}'.format(host, port),
                'workers': workers,
                'max_requests': max_requests,
                'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" %(p)s %(T)s.%(D)6s "%(i)s" "%(o)s"',
                'accesslog': accesslog,
                'errorlog': errorlog
            }
            #print gunicorn_options
            gunicorn_options.update(options)

            return gunicorn_options

        def load(self):
            return _prepare_flask_app(config)

    FlaskApplication().run()


def run(debug, config, host, port, **argv):
    """根据参数选择要执行的命令
    """
    # 取得要执行的函数
    if opts['debug'] is True:
        debug_server(config, host, port)
    else:
        gunicorn_server(config, host, port, argv['workers'], argv['maxrequests'], argv['accesslog'], argv['errorlog'])
        #gunicorn_server()
    return {}


def parseArgs(arguments):
    """去掉参数key中的--"""
    opts = {}
    for key, val in arguments.items():
        key = str(key).replace('--', '')
        if key == 'help':
            continue
        opts[key] = val

    return opts


if __name__ == "__main__":
    arguments = docopt(__doc__, version='manage 1.0.0')
    opts = parseArgs(arguments)
    run(**opts)
