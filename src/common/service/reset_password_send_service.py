import smtplib
from email.message import EmailMessage

import jinja2

from infrastructure.config import SMTPSettings, InfrastructureSettings
from infrastructure.database import PasswordResetToken, User


class PasswordResetSendService:
    template_name = 'password_reset_message.html'
    subject = 'Сервис бронирования коворкингов УрФУ. Смена пароля'

    def __init__(
            self,
            jinja_env: jinja2.Environment,
            smtp_settings: SMTPSettings,
            infra_settings: InfrastructureSettings
    ):
        self.jinja_env = jinja_env
        self.smtp_settings = smtp_settings
        self.infra_settings = infra_settings

    async def send(self, reset_token_data: PasswordResetToken, user: User) -> None:
        message = EmailMessage()
        message['From'] = self.smtp_settings.SMTP_EMAIL
        message['To'] = user.email
        message['Subject'] = self.subject
        link = self.__get_link(token=reset_token_data.id, email=user.email)
        rendered_template = await self.render_template(link=link)
        message.set_content(rendered_template, subtype='html')
        # aiosmtplib не хочет работать
        with smtplib.SMTP_SSL(
                host=self.smtp_settings.SMTP_SERVER,
                port=self.smtp_settings.SMTP_PORT
        ) as conn:
            conn.login(self.smtp_settings.SMTP_EMAIL, self.smtp_settings.SMTP_PASSWORD)
            conn.send_message(message)

    async def render_template(self, *, link: str) -> str:
        return await self.jinja_env.get_template(self.template_name).render_async(link=link)

    def __get_link(self, token: str, email: str) -> str:
        return f'{self.infra_settings.FRONTEND_URL}/password-recovery?token={token}&email={email}'
