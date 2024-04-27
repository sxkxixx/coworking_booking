def parse_email_to_user_id(email: str) -> str:
    """
    Splits email to user id:

    parse_email_to_user_id(name.surname@gmail.com) = "name.surname"
    """
    return email[:email.rfind('@')]


def is_student(email: str) -> bool:
    return email.endswith('urfu.me')
