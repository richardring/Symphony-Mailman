import config
import email_server.legacy_server as hermes_legacy
import email_server.smtp_server as hermes

if __name__ == '__main__':
    if config.UseLegacySMTPServer:
        hermes_legacy.start_server()
    else:
        hermes.start_server()
