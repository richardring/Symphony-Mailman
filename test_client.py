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


def SendTestWithAttachment():
    outer = EmailMessage()  # MIMEMultipart('alternative')

    outer['To'] = (Address("Mailman Test Room", "mailman.test.room", "corp.symphony.com"),
               Address("Kevin", "kevin.mcgrath", "corp.symphony.com"))

    # outer['From'] = Address('Ares', "bot.user6", "symphony.com")
    outer['From'] = Address('Mailman', 'kevin.mcgrath+mailman', 'corp.symphony.com')

    outer['Subject'] = 'Test Message - ' + datetime.now().strftime('%Y%m%d%H%M%S')

    txt = "This is the text part of the message"
    html = """\
    <html>
        <head></head>
        <body>
            <p>This is the <b>HTML</b> <i>portion</i> of the message</p>
        </body>
    </html>"""

    # Set text content
    # part1 = MIMEText(txt, 'plain')
    # outer.attach(part1)
    outer.set_content(txt)

    # Sent HTML content
    # part2 = MIMEText(html, 'html')
    # outer.attach(part2)
    outer.add_alternative(html)

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
    outer.attach(att_msg)

    SendEmailMessageToServer(outer)


def SendSingleUserTestEmail():
    msg = EmailMessage()
    msg['To'] = (Address("Me", "kevin.mcgrath", "corporate.symphony.com"))
    msg['From'] = Address("Kevin", "kevin.mcgrath", "symphony.com")

    msg['Subject'] = 'Test Message - ' + datetime.now().strftime('%Y%m%d%H%M%S')
    body = 'Testing sending with only a single user. Including bad characters: \n\n'
    body += '* Greater Than: >\n'
    body += '* Less Than: <\n'
    body += '* Ampersand: &\n'
    body += '* Single quotes: ' + "How are you? I'm great. 'blue' \n"
    body += '* Double quotes: "blah blah blah"'
    msg.set_content(body)

    SendEmailMessageToServer(msg)


def SendTestEmail(valid_sender: bool=True, valid_recipients: bool=True, valid_body: bool=True):
    # msg = MIMEText('Testing simultaneous forwarding of an email to several users and a room.')
    msg = EmailMessage()

    # to_list = (
    #     Address("Mark", "mark.koblenz", "corp.symphony.com"),
    #     Address("Kevin", "kevin.mcgrath", "corp.symphony.com"),
    #    Address("Rani", "rani.ibrahim", "corp.symphony.com"),
    #    Address("Biz Ops Team", "biz.ops.team", "corp.symphony.com")
    #)

    #to_list = (Address("Olympus", "olympus", "corp.symphony.com"),
    #             Address("Kevin", "kevin.mcgrath", "corp.symphony.com"))

    to_list = (Address("Kevin", "kevin.mcgrath", "corp.symphony.com"),
               Address("Mailman Test Room", "mailman_test_room", "corp.symphony.com"))

    # This param can take a tuple and then correctly format it for the message send method
    if valid_recipients:
        msg['To'] = to_list
    else:
        # I want at least one valid recipient.
        msg['To'] = (
            Address("Kevin", "kevin.mcgrath", "corp.symphony.com"),
            Address("Bob User", "bob.username", "corp.symphony.com"),
            # This is an invalid address. Underscores, maybe? I need to figure out why this blew up.
            # Address("Totally fake room jfjlkajslkjf", "totally_fake_room_jfjlkajslkjf", "corp.symphony.com")
        )

    if valid_sender:
        # msg['From'] = Address('Ares', "bot.user6", "symphony.com")
        msg['From'] = Address('Mailman', 'kevin.mcgrath+mailman', 'symphony.com')
    else:
        msg['From'] = Address('Hades', "invalid.user", "symphony.com")

    msg['Subject'] = 'Test Message - ' + datetime.now().strftime('%Y%m%d%H%M%S')

    if valid_body:
        msg.set_content('Testing simultaneous forwarding of an email to several users and a room.')
    else:
        msg.set_content('')

    SendEmailMessageToServer(msg)


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
            SendTestEmail()
        elif choice == "2":
            SendTestEmail(False)
        elif choice == "3":
            SendTestEmail(True, False)
        elif choice == "4":
            SendTestEmail(True, True, False)
        elif choice == "5":
            SendEHLO()
        elif choice == "6":
            SendTestWithAttachment2()
        elif choice == "7":
            SendSingleUserTestEmail()
        elif choice == "9":
            SendTestIM()
        elif choice == "91":
            SendTestIMwAtt()
        elif choice == "92":
            SendOBOTest()
        elif choice == "93":
            RoomSearchOBOTest()
        elif choice == "99":
            SendEchoTest()
        elif choice == "0":
            exit_flag = True
            print('Exiting')
        else:
            input("That's not a valid option, stupid. Press any key to continue.")


def MenuPrompt():
    prompt = "What do you want to do today? \n\n"
    prompt += "[1] Send a test email to the local SMTP Server\n"
    prompt += "[2] Send a test email with an invalid sender \n"
    prompt += "[3] Send a test email with an invalid recipient \n"
    prompt += "[4] Send a test email with a malformed body \n"
    prompt += "[5] Send an EHLO\n"
    prompt += "[6] Send a test email with an attachment\n"
    prompt += "[7] Send a test email with a single user\n"
    prompt += "[9] Send a test message to Symphony\n"
    prompt += "[91] Send a test message w/ attachment\n"
    prompt += "[92] Send an OBO test message \n"
    prompt += "[93] Send an OBO Room Search test\n"
    prompt += "[99] Send an echo test\n"

    prompt += "[0] Quit\n"

    return input(prompt)


if __name__ == '__main__':
    RunClient()