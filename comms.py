"""Contacts, WhatsApp and email."""
import smtplib
from email.message import EmailMessage

from .. import config, store
from ..router import skill


def _contacts():
    return store.load("contacts", {})


@skill(r"^add contact (\w+) (phone|number|email) (\S+)")
def add_contact(m, ctx):
    name, kind, value = m.group(1).lower(), m.group(2), m.group(3)
    kind = "email" if kind == "email" else "phone"
    contacts = _contacts()
    contacts.setdefault(name, {})[kind] = value.replace(" ", "")
    store.save("contacts", contacts)
    return f"Saved {name}'s {kind}."


@skill(r"\bwhats ?app(?: message)?(?: to)? (\w+)(?: saying| that| message)? (.+)", r"^(?:message|text) (\w+)(?: saying| that)? (.+)")
def whatsapp(m, ctx):
    name, body = m.group(1).lower(), m.group(2)
    phone = _contacts().get(name, {}).get("phone")
    if not phone:
        return f"I don't have a number for {name}. Say: add contact {name} phone, followed by the number with country code."
    if not ctx.confirm(f"Send {body} to {name} on WhatsApp?"):
        return "Cancelled."
    import pywhatkit
    pywhatkit.sendwhatmsg_instantly(phone, body, wait_time=15, tab_close=True)
    return f"Message sent to {name}."


@skill(r"^send (?:an )?e-?mail to (\w+)(?: saying| about| that)? (.+)")
def email(m, ctx):
    name, body = m.group(1).lower(), m.group(2)
    to = _contacts().get(name, {}).get("email")
    if not to:
        return f"I don't have an email for {name}. Say: add contact {name} email, followed by the address."
    if not (config.EMAIL_ADDRESS and config.EMAIL_APP_PASSWORD):
        return "Email isn't set up. Add your address and app password to the dot env file."
    if not ctx.confirm(f"Send that email to {name}?"):
        return "Cancelled."
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = config.EMAIL_ADDRESS, to, "Message from Jarvis"
    msg.set_content(body)
    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as s:
        s.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
        s.send_message(msg)
    return f"Email sent to {name}."
