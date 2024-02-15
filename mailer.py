import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import json
import socks


class Mailer:
    try:
        with open(".secret.json", "r") as config_file:
            config_data: dict = json.load(config_file)
    except FileNotFoundError:
        print("ERROR: No config file found!")
        exit(0)

    LOGIN = config_data.get("LOGIN")
    MY_PASS = config_data.get("PASSWORD")
    FROM_ADDR = config_data.get("FROM_ADDR")
    PORT = config_data.get("PORT")
    HOSTNAME = config_data.get("MAILHOST")
    PROXY = config_data.get("PROXY_HOST", None)
    PROXY_PORT = config_data.get("PROXY_PORT", None)
    if PROXY is not None and PROXY_PORT is not None:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, PROXY, PROXY_PORT)
        socks.wrapmodule(smtplib)

    def __init__(self,
                 email_addr: str,
                 bcc: str | None) -> None:
        self.email_addr = email_addr
        self.bcc_addr = bcc
        self.msg = MIMEMultipart()
        # email_msg = EmailMessage()
        self.msg["From"] = Mailer.FROM_ADDR
        self.msg["To"] = self.email_addr
        if self.bcc_addr:
            self.msg["Bcc"] = self.bcc_addr
        self.msg["Subject"] = "Happy Birthday!"

    def send_mail(self,
                  content: str) -> None:
        print(f"Sending mail to {self.email_addr} from {Mailer.FROM_ADDR}")

        html_text = MIMEText(content, 'html', 'utf-8')
        self.msg.attach(html_text)
        # self.msg.add_alternative(content, subtype='html', charset='utf-8')

        with smtplib.SMTP(host=Mailer.HOSTNAME,
                          port=Mailer.PORT) as connection:
            connection.starttls()
            connection.login(Mailer.LOGIN, Mailer.MY_PASS)

            connection.send_message(self.msg)

    def attach_image_to_mail(self, image_path) -> None:
        with open(image_path, 'rb') as fp:
            # Create a MIME image part
            img_data = fp.read()
        img = MIMEImage(img_data)
        # Define the ID for the image
        img.add_header('Content-ID', '<image1>')
        self.msg.attach(img)
        self.msg.attach(MIMEText('<img src="cid:image1">', 'html'))
