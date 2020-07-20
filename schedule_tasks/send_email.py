import os

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import parseaddr, formataddr


import smtplib


class EmailTools:
    def __init__(self, from_user: str, from_addr: str, password: str, to_user: str, to_addrs: list, smtp_server: str):
        '''
        :param from_user: 发件用户名
        :param from_addr: 发件地址
        :param password: 发件用户登录密码
        :param to_user: 收件用户名
        :param to_addr: 收件地址
        :param smtp_server: smtp.163.com/...
        '''
        self.from_user = from_user
        self.from_addr = from_addr
        self.password = password
        self.to_user = to_user
        self.to_addrs = to_addrs
        self.smtp_server = smtp_server

    def _format_addr(self, s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    def _send_server(self, msg):
        server = smtplib.SMTP(self.smtp_server, 25)
        server.set_debuglevel(3)
        server.login(self.from_addr, self.password)
        server.sendmail(self.from_addr, self.to_addrs, msg.as_string())
        server.quit()

    def _email_body(self, subject):
        msg = MIMEMultipart('test')
        msg['From'] = self._format_addr('%s <%s>' % (self.from_user, self.from_addr))
        # msg['To'] = self._format_addr('%s <%s>' % (self.to_user, self.to_addr))
        msg['To'] = Header(self.to_user, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8').encode()
        return msg

    def send_email(self, plain_content, subject):
        msg = MIMEText(plain_content, 'plain', 'utf-8')
        msg['From'] = self._format_addr('%s <%s>' % (self.from_user, self.from_addr))
        # msg['To'] = self._format_addr('%s <%s>' % (self.to_user, self.to_addr))
        msg['To'] = Header(self.to_user, 'utf-8').encode()
        msg['Subject'] = Header(subject, 'utf-8').encode()
        self._send_server(msg)

    def send_plain_html_email(self, subject, plain_content=None, html_content=None):
        assert plain_content or html_content
        msg = self._email_body(subject)
        if plain_content:
            msg.attach(MIMEText(plain_content, 'plain', 'utf-8'))
        if html_content:
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        self._send_server(msg)

    def send_attachment_email(self, subject, text, filepath):
        # 邮件对象:
        msg = self._email_body(subject)
        # 邮件正文是MIMEText:
        msg.attach(MIMEText(text, 'plain', 'utf-8'))
        filename = os.path.split(filepath)[1]
        part = MIMEApplication(open(filepath, 'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)
        self._send_server(msg)

if __name__ == '__main__':
    # email.send_attachment_email('测试', '看看好使不', '/Users/AMiner/AMiner/EItools/EItools/libs/utils/stopword.txt')
    # email.send_plain_html_email('测试', '看看好使不')
    em = EmailTools('苏平', 'ping.su@aminer.cn', 'cxsp.1119', '测试者', ['su752143565@163.com','bing.lun@aminer.cn', '752143565@qq.com', 'xiaowen.shi@aminer.cn'], 'smtp.mxhichina.com')
    em.send_email('测试', '测试')