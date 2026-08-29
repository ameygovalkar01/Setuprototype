"""
schema.py - Single Source of Truth for Scheme Data Model & Validation
"""
from typing import Dict, List, Any, Tuple, Optional
import re

DELIMITER = '|'

ALLOWED_CATEGORIES = [
    'SC', 'ST', 'OBC', 'General', 'EWS', 'DNT', 'Minority', 'All'
]

ALLOWED_GENDERS = [
    'All', 'Female', 'Male', 'Transgender'
]

ALLOWED_BENEFIT_TYPES = [
    'Loan', 'Grant', 'Subsidy', 'Credit Guarantee', 'Equity', 'Composite'
]

ALLOWED_SECTORS = [
    'All', 'Manufacturing', 'Services', 'Trade', 'Artisans & Crafts',
    'Agriculture & Allied', 'Startups & Tech', 'Greenfield Enterprises',
    'Food Processing', 'Textiles', 'Micro-Enterprise'
]

ALL_INDIA = 'All India'

STATES_AND_UTS = [
    ALL_INDIA,
    # 28 States
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
    'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
    'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
    'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
    'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    # 8 UTs
    'Andaman and Nicobar Islands', 'Chandigarh',
    'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
    'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
]

STANDARD_DOCUMENTS = [
    'Aadhaar Card',
    'PAN Card',
    'Caste Certificate',
    'Income Certificate',
    'UDID / Disability Certificate',
    'Detailed Project Report (DPR)',
    'Bank Account Statement (6 Months)',
    'Skill Training / Artisan Certificate',
    'Business Registration (Udyam)',
    'Land / Rent Agreement of Workplace'
]

SCHEME_COLUMNS = [
    'scheme_id',
    'scheme_name',
    'sponsoring_body',
    'category',
    'eligible_gender',
    'pwd_only',
    'min_income',
    'max_income',
    'min_age',
    'max_age',
    'states',
    'sector',
    'benefit_type',
    'benefit_amount',
    'subsidy_percentage',
    'description',
    'required_documents',
    'official_url',
    'contact_info'
]

NUMERIC_BOUNDS = {
    'min_income': (0, 100_000_000),
    'max_income': (-1, 100_000_000),  # -1 means uncapped
    'min_age': (14, 100),
    'max_age': (18, 120),
    'subsidy_percentage': (0.0, 100.0)
}

def parse_multi_field(val: Any) -> List[str]:
    """Parses a pipe-delimited string into a list of stripped items."""
    if val is None or (isinstance(val, float) and str(val) == 'nan'):
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    val_str = str(val).strip()
    if not val_str:
        return []
    # If standard pipe delimiter is used
    if '|' in val_str:
        return [x.strip() for x in val_str.split('|') if x.strip()]
    # Fallback if semicolon was used
    if ';' in val_str:
        return [x.strip() for x in val_str.split(';') if x.strip()]
    return [val_str]

def join_multi_field(items: List[str]) -> str:
    """Joins a list of strings using the standard pipe delimiter."""
    if not items:
        return ''
    cleaned = [str(x).strip() for x in items if str(x).strip()]
    return '|'.join(cleaned)

def parse_bool(val: Any) -> bool:
    """Safely parses boolean values from strings/bools."""
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ('true', '1', 'yes', 'y', 't')

def validate_scheme_row(row: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Strict validation of a single scheme dictionary against the schema rules.
    Returns (is_valid, list_of_error_strings).
    """
    errors = []
    
    # Required string fields
    for field in ['scheme_id', 'scheme_name', 'sponsoring_body', 'description', 'official_url']:
        val = str(row.get(field, '')).strip()
        if not val or val == 'nan':
            errors.append(f"Field '{field}' is required and cannot be empty.")
    
    # Validate multi-select categories
    cats = parse_multi_field(row.get('category', ''))
    if not cats:
        errors.append("Field 'category' must contain at least one valid category.")
    else:
        invalid_cats = [c for c in cats if c not in ALLOWED_CATEGORIES]
        if invalid_cats:
            errors.append(f"Invalid categories: {invalid_cats}. Allowed: {ALLOWED_CATEGORIES}")
            
    # Validate eligible_gender
    genders = parse_multi_field(row.get('eligible_gender', ''))
    if not genders:
        errors.append("Field 'eligible_gender' must have at least one selection (e.g. All, Female).")
    else:
        invalid_genders = [g for g in genders if g not in ALLOWED_GENDERS]
        if invalid_genders:
            errors.append(f"Invalid genders: {invalid_genders}. Allowed: {ALLOWED_GENDERS}")
            
    # Validate states
    states = parse_multi_field(row.get('states', ''))
    if not states:
        errors.append("Field 'states' must specify at least one state or 'All India'.")
    else:
        invalid_states = [s for s in states if s not in STATES_AND_UTS]
        if invalid_states:
            errors.append(f"Invalid states: {invalid_states}.")
            
    # Validate numeric fields
    try:
        min_inc = int(row.get('min_income', 0))
        max_inc = int(row.get('max_income', -1))
        if min_inc < 0:
            errors.append("min_income cannot be negative.")
        if max_inc != -1 and max_inc < min_inc:
            errors.append(f"max_income ({max_inc}) cannot be lower than min_income ({min_inc}).")
    except (ValueError, TypeError):
        errors.append("min_income and max_income must be integers.")
        
    try:
        min_age = int(row.get('min_age', 18))
        max_age = int(row.get('max_age', 70))
        if min_age < 14 or min_age > 100:
            errors.append("min_age must be between 14 and 100.")
        if max_age < min_age or max_age > 120:
            errors.append("max_age must be >= min_age and <= 120.")
    except (ValueError, TypeError):
        errors.append("min_age and max_age must be integers.")
        
    try:
        sub = float(row.get('subsidy_percentage', 0.0))
        if sub < 0.0 or sub > 100.0:
            errors.append("subsidy_percentage must be between 0.0 and 100.0.")
    except (ValueError, TypeError):
        errors.append("subsidy_percentage must be a number.")
        
    return (len(errors) == 0, errors)
