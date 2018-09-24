import logging
import logging.handlers
import sys

import config


_consolelog = logging.getLogger('hermes')
_errlog = logging.getLogger('hades')

_consolelog.setLevel(logging.DEBUG)
_errlog.setLevel(logging.DEBUG)

_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

_consoleStreamHandler = logging.StreamHandler(sys.stdout)
_errLogHandler = logging.StreamHandler(sys.stderr)

_consoleStreamHandler.setLevel(logging.DEBUG)
_consoleStreamHandler.setFormatter(_formatter)

_errLogHandler.setLevel(logging.DEBUG)
_errLogHandler.setFormatter(_formatter)

_consolelog.addHandler(_consoleStreamHandler)
_errlog.addHandler(_errLogHandler)


def LogConsoleInfo(message):
    _consolelog.info(message)


def LogConsoleInfoVerbose(message):
    if config.VerboseOutput:
        _consolelog.info(message)


def LogConsoleError(message):
    _errlog.error(message)


def LogConsoleErrorVerbose(message):
    if config.VerboseOutput:
        _errlog.error(message)


def LogSystemInfo(message):
    _consolelog.info(message)

def LogSystemInfoVerbose(message):
    if config.VerboseOutput:
        _consolelog.info(message)

def LogSystemWarn(message):
    _consolelog.warning(message)


def LogSystemError(message):
    _errlog.error(message)


def LogSystemErrorVerbose(message):
    if config.VerboseOutput:
        _errlog.error(message)