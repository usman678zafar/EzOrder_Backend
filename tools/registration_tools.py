from datetime import datetime
from agents import function_tool
from config.database import db
from utils.phone_utils import clean_phone_number

@function_tool
def validate_and_save_user(phone_number: str, name: str, address: str, city: str, postal_code: str = "") -> str:
    """Saves user information with minimal validation - let the LLM handle validation logic"""
    try:
        cleaned_phone = clean_phone_number(phone_number)

        cleaned_name = name.strip() if name else ""
        cleaned_address = address.strip() if address else ""
        cleaned_city = city.strip() if city else ""
        cleaned_postal = postal_code.strip() if postal_code else ""

        if not cleaned_name:
            return " ⚠ Name is required for registration."
        if not cleaned_address:
            return " ⚠ Address is required for delivery."
        if not cleaned_city:
            return " ⚠ City is required for delivery."

        user_doc = {
            "phone_number": cleaned_phone,
            "name": cleaned_name,
            "address": cleaned_address,
            "city": cleaned_city,
            "postal_code": cleaned_postal,
            "is_verified": True,
            "is_active": True,
            "updated_at": datetime.utcnow(),
        }

        existing = db.users.find_one({"phone_number": cleaned_phone})
        if existing:
            db.users.update_one({"phone_number": cleaned_phone}, {"$set": user_doc})
        else:
            user_doc["created_at"] = datetime.utcnow()
            user_doc.setdefault("role", "customer")
            db.users.update_one({"phone_number": cleaned_phone}, {"$set": user_doc}, upsert=True)

        return f""" ✅ *Registration Successful!*
Welcome *{cleaned_name}*! 🎉

Your delivery details:
📍 *Address:* {cleaned_address}
🏙 *City:* {cleaned_city}{f"""
📮 *Postal Code:* {cleaned_postal}""" if cleaned_postal else ""}

You're all set! I'll show you our menu now... 🍕 """
    except Exception as e:
        print(f"Error in validate_and_save_user: {str(e)}")
        return " ⚠ Sorry, there was an error saving your details. Please try again."

@function_tool
def validate_name(name: str) -> str:
    if not name or not name.strip():
        return " ⚠ Please provide a name."
    return f" ✅ Name '{name.strip()}' looks good!"

@function_tool
def validate_address(address: str, city: str, postal_code: str = "") -> str:
    if not address or not address.strip():
        return " ⚠ Please provide an address."
    if not city or not city.strip():
        return " ⚠ Please provide a city."
    return f""" ✅ Address looks complete!
📍 *Address:* {address.strip()}
🏙 *City:* {city.strip()}{f"""
📮 *Postal Code:* {postal_code.strip()}""" if postal_code and postal_code.strip() else ""}"""
