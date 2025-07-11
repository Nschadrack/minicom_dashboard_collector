
def format_number(value, decimals=2):
    try:
        # Handle both integer and string decimal specifications
        decimals = int(decimals)
        num = float(value)
    except (ValueError, TypeError):
        return 0
    
    # Round to specified decimal places
    rounded = round(num, decimals)
    integer_part = int(rounded)
    decimal_part = rounded - integer_part

    formatted_integer = "{:,}".format(integer_part)
    
    if decimal_part == 0:
        return formatted_integer
    
    # Format with dynamic decimal places
    format_string = f"{{:.{decimals}f}}"
    parts = format_string.format(rounded).split('.')
    decimal_str = parts[1].rstrip('0')
    
    if not decimal_str:  # If all decimals were zeros
        return formatted_integer
    
    return f"{formatted_integer}.{decimal_str}"


def format_number_two(value, decimals=6):
    try:
        # Handle both integer and string decimal specifications
        decimals = int(decimals)
        num = float(value)
    except (ValueError, TypeError):
        return 0
    
    # Round to specified decimal places
    rounded = round(num, decimals)
    integer_part = int(rounded)
    decimal_part = rounded - integer_part
    
    if decimal_part == 0:
        return integer_part
    
    # Format with dynamic decimal places
    format_string = f"{{:.{decimals}f}}"
    parts = format_string.format(rounded).split('.')
    decimal_str = parts[1].rstrip('0')
    
    if not decimal_str:  # If all decimals were zeros
        return integer_part
    
    return float(f"{integer_part}.{decimal_str}")

