import requests
import sys
import traceback

import botlog as log


def LogException(ex: Exception, custom_message: str=''):
    LogError(str(ex) + custom_message)


def LogRequestException(conn_ex: requests.exceptions.RequestException, custom_message: str=''):
    errorStr = "REST Exception: " + str(conn_ex) + ' - ' + custom_message

    if conn_ex.response:
        log.LogSystemErrorVerbose("Response Code: " + str(conn_ex.response.status_code))
        log.LogSystemErrorVerbose("Response Message: " + conn_ex.response.text)

    LogError(errorStr)


def LogWebException(http_ex: requests.exceptions.HTTPError, custom_message: str=''):
    errorStr = "HTTP Error: " + str(http_ex)

    if custom_message != '':
        log.LogSystemError('Custom Message: ' + custom_message)

    if http_ex.response:
        log.LogSystemErrorVerbose("Response Code: " + str(http_ex.response.status_code))
        log.LogSystemErrorVerbose("Response Message: " + http_ex.response.text)

    LogError(errorStr)


def LogError(message):
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame

    ex_filename = f.f_code.co_filename
    ex_line_no = tb.tb_lineno

    stack_trace = ''.join(traceback.format_stack())

    errorStr = "Exception (" + ex_filename + " [" + str(ex_line_no) + "]" + "): \n" + message
    stackTrace = 'Stack Trace: \n\n' + stack_trace
    log.LogSystemError(errorStr)
    log.LogSystemErrorVerbose(stackTrace)

