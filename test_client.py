import mimetypes
import os
import smtplib
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
import symphony.messaging as messaging

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

    from_addy = Address('Mailman', 'kevin.mcgrath+mailman', 'preview.symphony.com')

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
        # server.send_message(msg)
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
    # corporate
    # stream_id = "RBdrToHDkKn2V1ArbCtlNn///qohSqxMdA=="
    # preview
    # Olympus on Corp
    # stream_id = "KRvoQEySsHtyFc1A+6MKjn///p6dRVXFdA=="
    # Mailman Test Room on Preview
    # stream_id = "AbkTBtsN9LcqW6c1/p3vxn///pnpWJS/dA=="
    stream_id = "oAaMJy8ff_hJIMdgU43jCH___pntjcm-dA"
    # stream_id = "oAaMJy8ff/hJIMdgU43jCH///pntjcm+dA=="
    msg = "Sending basic test message to Symphony"

    u1 = "70368744177761"
    u2 = "70368744178234"

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
        elif choice == "9":
            SendTestIM()
        elif choice == "91":
            SendTestIMwAtt()
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
    prompt += "[9] Send a test message to Symphony\n"
    prompt += "[91] Send a test message w/ attachment\n"
    prompt += "[99] Send an echo test\n"

    prompt += "[0] Quit\n"

    return input(prompt)


if __name__ == '__main__':
    RunClient()