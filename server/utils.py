def mail_serv(message, location):

    config_file = open(CONFIG_FILE, 'r')
    config = json.loads(config_file.read())
    config_file.close()
    mail_id = config['EMAIL_ID']
    password = config['PASSWORD']
    receiver = config['RECEIVER']
    # location = config['LOCATION']

    s = smtplib.SMTP('smtp.gmail.com', 587)

    s.starttls()
    s.login(mail_id, password)
    message += f'\n\nLocation: {location}'
    try:
        s.sendmail(mail_id, receiver, message)
    except Exception:
        pass

    s.quit()
