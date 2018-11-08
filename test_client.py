from enum import Enum
import mimetypes
import os
import smtplib
import time

from datetime import datetime
from email import encoders
from email.headerregistry import Address
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage

import config
import exceptions
from email_server.models import MessageAttachment
import symphony.connection as conn
import symphony.messaging as messaging
import symphony.chatroom as chatroom
import symphony.user as user


class SymphonyTarget(Enum):
    DEVELOP = 1
    PREVIEW = 2
    CORPORATE = 3


from_rcpt_me = Address("Kevin", "kevin.mcgrath", "symphony.com")
from_rcpt_rani = Address("Rani", "rani.ibrahim", "symphony.com")

to_rcpt = {
    SymphonyTarget.PREVIEW: (Address("Mailman Test Room", "mailman.test.room", "preview.symphony.com"),
                             Address("Kevin", "kevin.mcgrath", "preview.symphony.com"),
                             Address("catchall", "catch_all", "preview.symphony.com")),
    SymphonyTarget.DEVELOP: (Address("Postmaster OBO Test", "postmaster.obo.test", "develop.symphony.com"),
                             Address("Kevin", "kevin.mcgrath", "develop.symphony.com")),
    SymphonyTarget.CORPORATE: (Address("Olympus", "olympus", "corporate.symphony.com"),
                               Address("Kevin", "kevin.mcgrath", "corporate.symphony.com"),
                               Address("Rani", "rani.ibrahim", "corporate.symphony.com")),
}

cc_rcpt = {
    SymphonyTarget.PREVIEW: (Address("Miguel", "miguel.clark", "preview.symphony.com"),
                             Address("Mark", "mark.koblenz", "preview.symphony.com")),
    SymphonyTarget.DEVELOP: (Address("Miguel", "miguel.clark", "develop.symphony.com"),
                             Address("Mark", "mark.koblenz", "develop.symphony.com")),
    SymphonyTarget.CORPORATE: (Address("Miguel", "miguel.clark", "corporate.symphony.com"),
                             Address("Mark", "mark.koblenz", "corporate.symphony.com")),
}

symphony_user_ids = {
    SymphonyTarget.PREVIEW: [{"name": "Miguel", "id": "70368744177987"},
                             {"name": "Rani", "id": "70368744178195"},
                             {"name": "Kevin", "id": "70368744177761"}],
    SymphonyTarget.DEVELOP: [{"name": "Miguel", "id": "347583113331377"},
                             {"name": "Rani", "id": "347583113330829"},
                             {"name": "Kevin", "id": "347583113330901"},
                             {"name": "Mark", "id": "347583113331592"}],
    SymphonyTarget.CORPORATE: [{"name": "Miguel", "id": "71811853189845"},
                             {"name": "Rani", "id": "71811853189403"},
                             {"name": "Kevin", "id": "71811853189474"},
                             {"name": "Mark", "id": "71811853189290"}],
}

stream_ids = {
    SymphonyTarget.PREVIEW: {"name": "Client Support", "id": "E4Tgra3jtNKw0wl0QjAc33___pnVVEzfdA",
                             "email": "client.support@preview.symphony.com"},
    SymphonyTarget.DEVELOP: {"name": "Postmaster OBO Test", "id": "P4pJ0vKyVaoK29t41a7px3___pkhmTRNdA",
                             "email": "postmaster.obo.test@develop.symphony.com"},
    SymphonyTarget.CORPORATE: {"name": "Olympus", "id": "RBdrToHDkKn2V1ArbCtlNn___qohSqxMdA",
                               "email": "olympus@corporate.symphony.com"}
}


def GetCurrentConfigType():
    if 'config_preview.json' in config.config_path:
        return SymphonyTarget.PREVIEW
    elif 'config_corp.json' in config.config_path:
        return SymphonyTarget.CORPORATE
    else:
        return SymphonyTarget.DEVELOP


def SendEHLO():
    server = smtplib.SMTP('35.237.41.20', 1025)
    # server = smtplib.SMTP('192.168.0.190', 25)

    server.set_debuglevel(True)

    try:
        response = server.ehlo('symphony.com')
        print(response)
    except Exception as ex:
        print(str(ex))


def SendTestWithAttachment2():
    msg = MIMEMultipart()

    to_addys = (Address("Mailman Test Room", "mailman.test.room", "preview.symphony.com"),
                Address("Kevin", "kevin.mcgrath", "preview.symphony.com"),
                Address("catchall", "catch_all", "preview.symphony.com"))

    #from_addy = Address('Mailman', 'kevin.mcgrath+mailman', 'preview.symphony.com')

    from_addy = Address('Me', 'kevinmcgr', 'gmail.com')

    cc_addys = (Address("Mark", "mark.koblenz", "preview.symphony.com"),
                Address("SFDC bot", "sfdcbot", "preview.symphony.com"))
                # Address("Miguel", "miguel.clark", "preview.symphony.com"))

    msg['From'] = str(from_addy)
    msg['To'] = ', '.join([str(addy) for addy in to_addys])
    msg['CC'] = ', '.join([str(addy) for addy in cc_addys])

    msg['Subject'] = 'Test Message - ' + datetime.now().strftime('%Y%m%d%H%M%S')

    txt = "This is the text part of the message"
    html = """\
        <html>
            <head></head>
            <body>
                <p>This is the <b>HTML</b> <i>portion</i> of the message</p>
            </body>
        </html>"""

    msg.attach(MIMEText(txt, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    file_path = os.path.abspath("./client/Powershell_Reference.pdf")
    fp = open(file_path, 'rb')
    ctype, encoding = mimetypes.guess_type(file_path)
    maintype, subtype = ctype.split('/', 1)
    att_msg = MIMEBase(maintype, subtype)
    att_msg.set_payload(fp.read())
    fp.close()

    # base64 encode the payload. Christ only knows if Symphony will know what to do with it.
    encoders.encode_base64(att_msg)
    att_msg.add_header('Content-Disposition', 'attachment', filename="Powershell_Reference.pdf")

    msg.attach(att_msg)

    SendEmailMessageToServer(msg)





def CreateTextBody():
    body = 'Testing sending with only a single user. Including bad characters: \n\n'
    body += '* Greater Than: >\n'
    body += '* Less Than: <\n'
    body += '* Ampersand: &\n'
    body += '* Single quotes: ' + "How are you? I'm great. 'blue' \n"
    body += '* Double quotes: "blah blah blah"'

    return body


def CreateHTMLBody():
    html = """\
        <html>
            <head></head>
            <body>
                <p>This is the <b>HTML</b> <i>portion</i> of the message</p>
                <a href="https://www.google.com" target=_blank>Google</a>
            </body>
        </html>"""

    return html


def SendTestEmail():
    cfg_type = GetCurrentConfigType()
    SendEmail(from_rcpt_me, to_rcpt[cfg_type], 'Test Subject', None, )


def SendEmail(from_address: Address, to_list, subject: str, body_text: str,  cc_list=None,
              body_html: str=None, attachment_paths: list=None):

    if attachment_paths:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body_text, 'plain'))

        if body_html:
            msg.attach(MIMEText(body_html, 'html'))

        for att_path in attachment_paths:
            msg.attach(CreateAttachment(att_path))
    else:
        msg = EmailMessage()
        msg.set_content(body_text)

    msg['From'] = from_address
    msg['To'] = to_list
    msg['Subject'] = subject + ' - ' + datetime.now().strftime('%Y%m%d%H%M%S')

    if cc_list:
        msg['CC'] = cc_list

    SendEmailMessageToServer(msg)


def CreateAttachment(file_path: str):
    abs_path = os.path.abspath(file_path)
    fp = open(file_path, 'rb')
    ctype, encoding = mimetypes.guess_type(abs_path)
    maintype, subtype = ctype.split('/', 1)

    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(fp.read())
    fp.close()

    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(abs_path))

    return attachment


def SendEmailMessageToServer(msg):
    # server = smtplib.SMTP(config.SMTPServerHost, config.SMTPServerPort)
    # server = smtplib.SMTP('69.253.229.9', 25)
    server = smtplib.SMTP('192.168.0.190', 25)
    server.set_debuglevel(True)

    smtp_conn_open = True

    try:

        server.send_message(msg)

        time.sleep(5)

        print('Sending duplicate message 1')
        server.send_message(msg)

        time.sleep(5)

        print('Sending duplicate message 2')
        server.send_message(msg)
    except smtplib.SMTPSenderRefused as sender_ex:
        print('Sender refused: ' + str(sender_ex))
        smtp_conn_open = False
    except smtplib.SMTPRecipientsRefused as rcp_ex:
        print('Recipient refused: ' + str(rcp_ex))
    except smtplib.SMTPDataError as data_ex:
        print('Data submit error: ' + str(data_ex))
    except smtplib.SMTPServerDisconnected as disconn_ex:
        print('STMP server disconnected. ' + str(disconn_ex))
        smtp_conn_open = False
    except smtplib.SMTPException as smtp_ex:
        print('SMTP error: ' + str(smtp_ex))
    except Exception as ex:
        exceptions.LogException(ex, suppress_stack_trace=True)
    finally:
        if smtp_conn_open:
            server.quit()


def SendEchoTest():
    msg = 'Sending Echo to Symphony'
    resp = messaging.SendEcho(msg)
    print(resp)


def SendTestIM():
    # corporate (Olympus)
    # stream_id = "RBdrToHDkKn2V1ArbCtlNn___qohSqxMdA"
    # preview
    # Olympus on Corp
    # stream_id = "KRvoQEySsHtyFc1A+6MKjn///p6dRVXFdA=="
    # Mailman Test Room on Preview
    # stream_id = "AbkTBtsN9LcqW6c1/p3vxn///pnpWJS/dA=="

    # stream_id = "oAaMJy8ff/hJIMdgU43jCH///pntjcm+dA=="

    # Working 10/28/2018 (on Preview)
    stream_id = "oAaMJy8ff_hJIMdgU43jCH___pntjcm-dA"
    msg = "Sending basic test message to Symphony"

    # preview users
    u1 = "70368744177761"  # Kevin (Preview)
    u2 = "70368744177987"  # Miguel (Preview)
    u3 = "70368744178234"  # Postmaster (Preview)


    # corp users
    # u1 = "71811853189474"  # Kevin
    # u2 = "71811853189555"  # Ares

    uids = [u1, u2]

    body = "<messageML>Forwarded e-mail message from: Mailman (kevin.mcgrath+mailman@symphony.com)<br/>"
    body += "<b>To</b>: Kevin McGrath (kevin.mcgrath@symphony.com)<br/>"
    body += "<b>Subject</b>: Test Message - " + datetime.now().strftime('%Y%m%d%H%M%S') + "<br/>"
    body += "<b>Body</b>: Testing simultaneous forwarding of an email to several users and a room.<br/>"
    body += "</messageML>"

    # resp = messaging.SendSymphonyMessageV2(stream_id, body)
    resp = messaging.SendUserIMv2(uids, body)
    print(resp)


def SendTestIMwAtt():
    # Olympus on Corp
    # stream_id = "KRvoQEySsHtyFc1A+6MKjn///p6dRVXFdA=="
    # Mailman Test Room on Preview
    stream_id = "AbkTBtsN9LcqW6c1/p3vxn///pnpWJS/dA=="
    msg = "Sending basic test message (with attachments) to Symphony"

    att_obj = MessageAttachment()
    att_obj.Filename = "Powershell_Reference.pdf"
    att_obj.Extension = "pdf"

    file_path = os.path.abspath("./client/Powershell_Reference.pdf")
    fp = open(file_path, 'rb')
    ctype, encoding = mimetypes.guess_type(file_path)
    # maintype, subtype = ctype.split('/', 1)
    att_obj.Data = fp.read()
    att_obj.MIME = ctype
    fp.close()

    att_obj2 = MessageAttachment()
    att_obj2.Filename = "Default_Router_Admin.pdf"
    att_obj2.Extension = "pdf"

    file_path = os.path.abspath("./client/Default_Router_Admin.pdf")
    fp = open(file_path, 'rb')
    ctype, encoding = mimetypes.guess_type(file_path)
    # maintype, subtype = ctype.split('/', 1)
    att_obj2.Data = fp.read()
    att_obj2.MIME = ctype
    fp.close()

    resp = messaging.SendSymphonyMessageV2(stream_id, msg, None, [att_obj, att_obj2])
    print(resp)


def SendOBOTest():

    conn.Authenticate()

    obo_user_id_corp = "71811853189403"  # Rani (Corporate)

    u1_corp = "71811853189845"  # Miguel (Corporate)
    u2_corp = "71811853189403"  # Rani (Corporate)
    u3_corp = "71811853189474"  # Kevin (Corporate)
    u4_corp = "71811853189290"  # Mark (Corporate)

    stream_id_corp = "PyhRxVl8jJwqYLyOnDtb2X___qyJ6N2qdA"

    obo_user_id_pre = "70368744177761"  # Kevin (preview)

    u1_pre = "70368744177987"  # Miguel (Preview)
    u2_pre = "70368744178195"  # Rani (Preview)

    stream_id_pre = "E4Tgra3jtNKw0wl0QjAc33___pnVVEzfdA"

    obo_user_id = "347583113330901"  # Kevin (develop)

    u1 = "347583113331377"  # Miguel (develop)
    u2 = "347583113330829"  # Rani (develop)
    u3 = "347583113331592"  # Mark (develop)

    stream_id = "P4pJ0vKyVaoK29t41a7px3___pkhmTRNdA"  # Postmaster OBO Test (develop)

    body = "<messageML>Forwarded e-mail message from: Postmaster on behalf of "
    body += '<mention uid="' + obo_user_id +'"/><br/>'
    body += "<b>To</b>: Miguel Clark (miguel.clark@symphony.com)<br/>"
    body += "<b>Subject</b>: Test Message - " + datetime.now().strftime('%Y%m%d%H%M%S') + "<br/>"
    body += "<b>Body</b>: Testing simultaneous forwarding of an email to several users and a room.<br/>"
    body += "</messageML>"

    # presence test

    # resp_presence = user.SetUserPresence("BUSY", obo_user_id_corp)
    # resp_presence = user.SetUserPresence("BUSY", obo_user_id_pre)
    # resp_presence = user.SetUserPresence("BUSY", obo_user_id)

    # print('Presence Response: ' + resp_presence.text)

    # resp = messaging.SendUserIMv2([obo_user_id, u1, u2], body, obo_user_id=obo_user_id)

    # resp = messaging.SendSymphonyMessageV2(stream_id_pre, body, obo_user_id=obo_user_id_pre)

    body_corp = "<messageML>I have to let my true feelings out.</messageML>"
    resp = messaging.SendSymphonyMessageV2(stream_id_corp, body_corp, obo_user_id=obo_user_id_corp)

    # This is DEFINITELY working - and does not require the Postmaster KM token
    # (commented out KM token from connection_obo.py 11/4/2018 7:18am)
    # resp = messaging.SendSymphonyMessageV2(stream_id, body, obo_user_id=u2)  # obo_user_id
    print(resp)


def RoomSearchOBOTest():
    obo_user_id = "70368744177761"  # Kevin (preview)

    stream_id, room_name = chatroom.SearchRoomByName("Client Supp", obo_user_id=obo_user_id)

    print(stream_id, room_name)


def RunClient():
    cli_text = ''
    exit_flag = False

    while not exit_flag:
        # supposedly this garbage nonsense will clear the terminal screen
        print("\033[H\033[J")

        choice = MenuPrompt()

        if choice == "1":
            SendEHLO()
        elif choice == "2":
            SendTestEmail()
        elif choice == "3":
            SendTestIM()
        elif choice == "0":
            exit_flag = True
            print('Exiting')
        else:
            input("That's not a valid option, stupid. Press any key to continue.")


def MenuPrompt():
    prompt = "Configuration: " + str(GetCurrentConfigType()) + " - Select Option: \n\n"
    prompt += "[1] Send EHLO\n"
    prompt += "[2] Send a test email\n"
    prompt += "[3] Send a test IM\n"

    prompt += "[0] Quit\n"

    return input(prompt)


if __name__ == '__main__':
    RunClient()