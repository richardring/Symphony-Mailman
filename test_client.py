import smtplib
from datetime import datetime
from email.headerregistry import Address
from email.mime.text import MIMEText
from email.message import EmailMessage

import config
import exceptions
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




def SendTestEmail(valid_sender: bool=True, valid_recipients: bool=True, valid_body: bool=True):
    # msg = MIMEText('Testing simultaneous forwarding of an email to several users and a room.')
    msg = EmailMessage()

    # to_list = (
    #     Address("Mark", "mark.koblenz", "corp.symphony.com"),
    #     Address("Kevin", "kevin.mcgrath", "corp.symphony.com"),
    #    Address("Rani", "rani.ibrahim", "corp.symphony.com"),
    #    Address("Biz Ops Team", "biz.ops.team", "corp.symphony.com")
    #)

    to_list = (Address("Olympus", "olympus", "corp.symphony.com"),
                 Address("Kevin", "kevin.mcgrath", "corp.symphony.com"))

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
        msg['From'] = Address('Ares', "bot.user6", "symphony.com")
    else:
        msg['From'] = Address('Hades', "invalid.user", "symphony.com")

    msg['Subject'] = 'Test Message - ' + datetime.now().strftime('%Y%m%d%H%M%S')

    if valid_body:
        msg.set_content('Testing simultaneous forwarding of an email to several users and a room.')
    else:
        msg.set_content('')

    server = smtplib.SMTP(config.SMTPServerHost, config.SMTPServerPort)
    # server = smtplib.SMTP('69.253.229.9', 25)
    server.set_debuglevel(True)

    try:
        server.send_message(msg)
        server.send_message(msg)
    except smtplib.SMTPSenderRefused as sender_ex:
        print('Sender refused: ' + str(sender_ex))
    except smtplib.SMTPRecipientsRefused as rcp_ex:
        print('Recipient refused: ' + str(rcp_ex))
    except smtplib.SMTPDataError as data_ex:
        print('Data submit error: ' + str(data_ex))
    except smtplib.SMTPException as smtp_ex:
        print('SMTP error: ' + str(smtp_ex))
    except Exception as ex:
        exceptions.LogException(ex)
        # print('Uncaught exception: ' + str(ex))
    finally:
        server.quit()


def SendEchoTest():
    msg = 'Sending Echo to Symphony'
    resp = messaging.SendEcho(msg)
    print(resp)


def SendTestIM():
    # corporate
    # stream_id = "RBdrToHDkKn2V1ArbCtlNn///qohSqxMdA=="
    # preview
    stream_id = "KRvoQEySsHtyFc1A+6MKjn///p6dRVXFdA=="
    msg = "Sending basic test message to Symphony"

    resp = messaging.SendSymphonyMessage(stream_id, msg)
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
        elif choice == "9":
            SendTestIM()
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
    prompt += "[9] Send a test message to Symphony\n"
    prompt += "[99] Send an echo test\n"

    prompt += "[0] Quit\n"

    return input(prompt)


if __name__ == '__main__':
    RunClient()