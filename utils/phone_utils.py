def clean_phone_number(phone: str) -> str:
    """Centralized phone number cleaning - removes WhatsApp suffixes"""
    if not phone:
        return ""
    return phone.replace("@c.us", "").replace("@g.us", "").strip()
