import os
from datetime import datetime


def SaveInboundEmail(from_email: str, data):
    filename = from_email + '_%s.eml' % (datetime.now().strftime('%Y%m%d%H%M%S.%f'))
    email_path = os.path.abspath('./messages/' + filename)

    file_handle = open(email_path, 'w')
    file_handle.write(str(data))
    file_handle.close()