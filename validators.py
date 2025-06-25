import re
from datetime import datetime
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from nameparser import HumanName
import requests
import time
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DataValidator:
    @staticmethod
    def validate_and_format_full_name(value):
        """Validate and format full name using nameparser."""
        logger.debug(f"Validating name: {value}")
        
        if not value or not isinstance(value, str):
            logger.debug("Invalid input: empty or not string")
            return None, "Invalid name format", "wrong"

        try:
            # Clean the input
            value = value.strip()
            logger.debug(f"Cleaned input: {value}")
            
            # Parse the name using nameparser
            name = HumanName(value)
            logger.debug(f"Parsed name components: {name}")
            
            # Basic validation
            if not name.first and not name.last:
                logger.debug("No first or last name found")
                return None, "Invalid name format", "wrong"
            
            # Format the name properly
            formatted = str(name)
            logger.debug(f"Formatted name: {formatted}")
            
            # Additional validation rules
            name_parts = formatted.split()
            logger.debug(f"Name parts: {name_parts}")
            
            # Check if name is too long
            if len(name_parts) > 5:
                logger.debug("Name too long")
                return None, "Name has too many parts", "wrong"
            
            # Validate each part
            for part in name_parts:
                # Skip validation for titles and suffixes
                if part in name.titles or part in name.suffixes:
                    logger.debug(f"Skipping validation for title/suffix: {part}")
                    continue
                
                # Basic validation: must start with a capital letter and contain only letters and hyphens
                if not re.match(r'^[A-Z][a-zA-Z\'-]*$', part):
                    logger.debug(f"Invalid name part: {part}")
                    return None, f"Invalid name part: {part}", "wrong"
                
                # Check for minimum length
                if len(part) < 2:
                    logger.debug(f"Name part too short: {part}")
                    return None, f"Name part too short: {part}", "wrong"
                
                # Check for maximum length
                if len(part) > 20:
                    logger.debug(f"Name part too long: {part}")
                    return None, f"Name part too long: {part}", "wrong"
            
            logger.debug(f"Successfully validated name: {formatted}")
            return formatted, None, "correct"
            
        except Exception as e:
            logger.error(f"Error in name validation: {str(e)}")
            return None, f"Error validating name: {str(e)}", "wrong"

    @staticmethod
    def validate_and_format_date(value):
        """Validate and format date of birth."""
        logger.debug(f"Validating date: {value}")
        
        if not value or not isinstance(value, str):
            logger.debug("Invalid input: empty or not string")
            return None, "Invalid date format", "wrong"

        try:
            # Remove any non-date text that might be present
            value = value.strip()
            logger.debug(f"Cleaned input: {value}")
            
            # Common date formats
            formats = [
                '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
                '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
                '%d %b %Y', '%d %B %Y'
            ]
            
            # Try to parse the date
            parsed_date = None
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(value, fmt)
                    logger.debug(f"Successfully parsed date with format: {fmt}")
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                logger.debug("Could not parse date with any format")
                return None, "Invalid date format", "wrong"
                
            # Validate the date is reasonable for a date of birth
            current_year = datetime.now().year
            year = parsed_date.year
            
            # Check if year is within reasonable range (e.g., 1900 to current year)
            if year < 1900 or year > current_year:
                logger.debug(f"Year {year} out of reasonable range")
                return None, "Year out of reasonable range", "wrong"
                
            # Check if date is in the future
            if parsed_date > datetime.now():
                logger.debug("Date is in the future")
                return None, "Date cannot be in the future", "wrong"
                
            # Standardize to YYYY-MM-DD format
            formatted = parsed_date.strftime('%Y-%m-%d')
            logger.debug(f"Successfully formatted date: {formatted}")
            return formatted, None, "correct"
            
        except Exception as e:
            logger.error(f"Error in date validation: {str(e)}")
            return None, f"Error validating date: {str(e)}", "wrong"

    @staticmethod
    def validate_and_format_phone(value):
        """Validate and format phone number."""
        logger.debug(f"Validating phone: {value}")
        
        if not value or not isinstance(value, str):
            logger.debug("Invalid input: empty or not string")
            return None, "Invalid phone number format", "wrong"

        try:
            # Clean the input - remove any non-digit characters except + and -
            cleaned = re.sub(r'[^\d+\-]', '', value)
            logger.debug(f"Cleaned phone: {cleaned}")
            
            # If the number starts with +, keep it, otherwise add +91 for Indian numbers
            if not cleaned.startswith('+'):
                cleaned = '+91' + cleaned
            logger.debug(f"Phone with country code: {cleaned}")
            
            # Try to parse the phone number
            number = phonenumbers.parse(cleaned)
            logger.debug(f"Parsed phone number: {number}")
            
            # Check if it's a valid number
            if phonenumbers.is_valid_number(number):
                # Format to international format
                formatted = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                logger.debug(f"Successfully formatted phone: {formatted}")
                return formatted, None, "correct"
            
            # If not valid, try without country code
            if not cleaned.startswith('+'):
                number = phonenumbers.parse(cleaned, "IN")
                if phonenumbers.is_valid_number(number):
                    formatted = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                    logger.debug(f"Successfully formatted phone with IN country code: {formatted}")
                    return formatted, None, "correct"
            
            logger.debug("Invalid phone number")
            return None, "Invalid phone number", "wrong"
            
        except Exception as e:
            logger.error(f"Error in phone validation: {str(e)}")
            return None, f"Error validating phone: {str(e)}", "wrong"

    @staticmethod
    def validate_and_format_email(value):
        """Validate and format email address."""
        logger.debug(f"Validating email: {value}")
        
        if not value or not isinstance(value, str):
            logger.debug("Invalid input: empty or not string")
            return None, "Invalid email format", "wrong"

        try:
            # Clean the input
            value = value.strip()
            logger.debug(f"Cleaned email: {value}")
            
            # Validate and normalize email
            validated = validate_email(value)
            formatted = validated.normalized
            logger.debug(f"Successfully validated email: {formatted}")
            return formatted, None, "correct"
            
        except EmailNotValidError as e:
            logger.debug(f"Invalid email: {str(e)}")
            return None, str(e), "wrong"
        except Exception as e:
            logger.error(f"Error in email validation: {str(e)}")
            return None, f"Error validating email: {str(e)}", "wrong"

    @staticmethod
    def validate_and_format_aadhar(value):
        """Validate and format Aadhar number."""
        # Remove spaces and hyphens
        cleaned = re.sub(r'[-\s]', '', value)
        # Check if it's a valid 12-digit number
        if re.match(r'^\d{12}$', cleaned):
            # Format as XXXX-XXXX-XXXX
            formatted = f"{cleaned[:4]}-{cleaned[4:8]}-{cleaned[8:]}"
            return formatted, None, "correct"
        return None, "Invalid Aadhar number", "wrong"

    @staticmethod
    def validate_and_format_pan(value):
        """Validate and format PAN number."""
        # Remove spaces and convert to uppercase
        cleaned = value.upper().replace(' ', '')
        # Check if it matches the PAN format (5 letters, 4 digits, 1 letter)
        if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', cleaned):
            return cleaned, None, "correct"
        return None, "Invalid PAN number", "wrong"

    @staticmethod
    def validate_and_format_passport(value):
        """Validate and format passport number."""
        # Remove spaces and convert to uppercase
        cleaned = value.upper().replace(' ', '')
        # Check if it's a valid passport number (6-9 alphanumeric characters)
        if re.match(r'^[A-Z0-9]{6,9}$', cleaned):
            return cleaned, None, "correct"
        return None, "Invalid passport number", "wrong"

    @staticmethod
    def validate_and_format_voter_id(value):
        """Validate and format Voter ID number."""
        # Remove spaces and convert to uppercase
        cleaned = value.upper().replace(' ', '')
        # Check if it matches the EPIC format (3 letters, 7 digits)
        if re.match(r'^[A-Z]{3}[0-9]{7}$', cleaned):
            return cleaned, None, "correct"
        return None, "Invalid Voter ID number", "wrong"

    @staticmethod
    def validate_and_format_driving_license(value):
        """Validate and format driving license number."""
        # Remove spaces and convert to uppercase
        cleaned = value.upper().replace(' ', '')
        # Basic validation for common formats
        if re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,2}[0-9]{4,7}$', cleaned):
            return cleaned, None, "correct"
        return None, "Invalid driving license number", "wrong"

    @staticmethod
    def validate_and_format_bank_account(value):
        """Validate and format bank account number."""
        # Remove spaces and non-digit characters
        cleaned = re.sub(r'[^\d]', '', value)
        # Check if it's a valid length (8-18 digits)
        if re.match(r'^\d{8,18}$', cleaned):
            return cleaned, None, "correct"
        return None, "Invalid bank account number", "wrong"

    @staticmethod
    def validate_and_format_credit_card(value):
        """Validate and format credit card number."""
        # Remove spaces and non-digit characters
        cleaned = re.sub(r'[^\d]', '', value)
        # Check if it's a valid credit card number
        if re.match(r'^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})$', cleaned):
            # Format as XXXX-XXXX-XXXX-XXXX
            formatted = '-'.join(cleaned[i:i+4] for i in range(0, len(cleaned), 4))
            return formatted, None, "correct"
        return None, "Invalid credit card number", "wrong"

    @staticmethod
    def validate_and_format_ip(value):
        """Validate and format IP address."""
        # Check if it's a valid IPv4 address
        if re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', value):
            return value, None, "correct"
        return None, "Invalid IP address", "wrong"

    @staticmethod
    def get_validator_for_type(data_type):
        """Get the appropriate validator for a given data type."""
        validators = {
            'full_name': DataValidator.validate_and_format_full_name,
            'date_of_birth': DataValidator.validate_and_format_date,
            'mobile_number': DataValidator.validate_and_format_phone,
            'telephone_number': DataValidator.validate_and_format_phone,
            'email_address': DataValidator.validate_and_format_email,
            'aadhar_number': DataValidator.validate_and_format_aadhar,
            'pan_number': DataValidator.validate_and_format_pan,
            'passport_number': DataValidator.validate_and_format_passport,
            'voter_id_number': DataValidator.validate_and_format_voter_id,
            'driving_license_number': DataValidator.validate_and_format_driving_license,
            'bank_account_number': DataValidator.validate_and_format_bank_account,
            'credit_debit_card_number': DataValidator.validate_and_format_credit_card,
            'ip_address': DataValidator.validate_and_format_ip
        }
        return validators.get(data_type) 