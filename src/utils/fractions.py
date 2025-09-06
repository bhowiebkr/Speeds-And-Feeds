"""
Fractional input parsing utilities for CNC ToolHub.

Provides functions for parsing fractional imperial measurements (e.g., "1/4", "3/8")
and converting them to high-precision Decimal values.
"""

import re
from decimal import Decimal
from fractions import Fraction
from typing import Union, Optional, Tuple


class FractionalInputError(ValueError):
    """Exception raised when fractional input cannot be parsed."""
    pass


def parse_fractional_input(input_str: str) -> Decimal:
    """
    Parse fractional or decimal input and return a high-precision Decimal.
    
    Supports formats:
    - Simple fractions: "1/4", "3/8", "1/2"
    - Mixed fractions: "1 1/4", "2 3/8"
    - Decimals: "0.25", "1.5"
    - Integers: "1", "2"
    
    Args:
        input_str: String input to parse
        
    Returns:
        Decimal: High-precision decimal representation
        
    Raises:
        FractionalInputError: If input cannot be parsed
        
    Examples:
        >>> parse_fractional_input("1/4")
        Decimal('0.25')
        >>> parse_fractional_input("1 1/2")
        Decimal('1.5')
        >>> parse_fractional_input("0.375")
        Decimal('0.375')
    """
    if not input_str or not input_str.strip():
        raise FractionalInputError("Empty input")
    
    input_str = input_str.strip()
    
    # Try to parse as mixed fraction (e.g., "1 1/4", "2 3/8")
    mixed_match = re.match(r'^(\d+)\s+(\d+)/(\d+)$', input_str)
    if mixed_match:
        whole, numerator, denominator = map(int, mixed_match.groups())
        if denominator == 0:
            raise FractionalInputError("Division by zero in fraction")
        
        # Convert to Fraction for exact arithmetic, then to Decimal
        fraction = Fraction(whole) + Fraction(numerator, denominator)
        return Decimal(fraction.numerator) / Decimal(fraction.denominator)
    
    # Try to parse as simple fraction (e.g., "1/4", "3/8")
    simple_fraction_match = re.match(r'^(\d+)/(\d+)$', input_str)
    if simple_fraction_match:
        numerator, denominator = map(int, simple_fraction_match.groups())
        if denominator == 0:
            raise FractionalInputError("Division by zero in fraction")
        
        # Use Fraction for exact arithmetic, then convert to Decimal
        fraction = Fraction(numerator, denominator)
        return Decimal(fraction.numerator) / Decimal(fraction.denominator)
    
    # Try to parse as decimal or integer
    try:
        return Decimal(input_str)
    except (ValueError, TypeError) as e:
        raise FractionalInputError(f"Cannot parse '{input_str}' as fraction or decimal") from e


def decimal_to_fraction_string(decimal_value: Union[Decimal, float, str], max_denominator: int = 64) -> Optional[str]:
    """
    Convert a decimal value to its fractional representation if it's a simple fraction.
    
    Args:
        decimal_value: Decimal value to convert
        max_denominator: Maximum allowed denominator (default 64 for common imperial fractions)
        
    Returns:
        String representation of fraction if simple, None otherwise
        
    Examples:
        >>> decimal_to_fraction_string(Decimal("0.25"))
        "1/4"
        >>> decimal_to_fraction_string(Decimal("1.5"))
        "1 1/2"
        >>> decimal_to_fraction_string(Decimal("0.123"))
        None  # Not a simple fraction
    """
    try:
        # Convert to Fraction
        if isinstance(decimal_value, str):
            decimal_value = Decimal(decimal_value)
        
        fraction = Fraction(decimal_value).limit_denominator(max_denominator)
        
        # Check if the limited fraction is close enough to the original
        if abs(float(fraction) - float(decimal_value)) > 1e-10:
            return None  # Not a simple fraction
        
        # Format as mixed fraction if >= 1, simple fraction otherwise
        if fraction >= 1:
            whole_part = fraction.numerator // fraction.denominator
            remainder = fraction.numerator % fraction.denominator
            
            if remainder == 0:
                return str(whole_part)  # Whole number
            else:
                return f"{whole_part} {remainder}/{fraction.denominator}"
        else:
            if fraction.denominator == 1:
                return str(fraction.numerator)  # Whole number
            return f"{fraction.numerator}/{fraction.denominator}"
    
    except (ValueError, TypeError):
        return None


def get_common_imperial_fractions() -> list[Tuple[str, Decimal]]:
    """
    Get a list of common imperial fractional sizes used in machining.
    
    Returns:
        List of tuples (display_string, decimal_value)
    """
    common_fractions = [
        "1/64", "1/32", "3/64", "1/16", "5/64", "3/32", "7/64", "1/8",
        "9/64", "5/32", "11/64", "3/16", "13/64", "7/32", "15/64", "1/4",
        "17/64", "9/32", "19/64", "5/16", "21/64", "11/32", "23/64", "3/8",
        "25/64", "13/32", "27/64", "7/16", "29/64", "15/32", "31/64", "1/2",
        "33/64", "17/32", "35/64", "9/16", "37/64", "19/32", "39/64", "5/8",
        "41/64", "21/32", "43/64", "11/16", "45/64", "23/32", "47/64", "3/4",
        "49/64", "25/32", "51/64", "13/16", "53/64", "27/32", "55/64", "7/8",
        "57/64", "29/32", "59/64", "15/16", "61/64", "31/32", "63/64", "1"
    ]
    
    # Convert to (display_string, Decimal) pairs
    result = []
    for fraction_str in common_fractions:
        try:
            decimal_val = parse_fractional_input(fraction_str)
            result.append((fraction_str, decimal_val))
        except FractionalInputError:
            continue  # Skip invalid fractions
    
    return result


def format_diameter_display(diameter: Union[Decimal, float], original_unit: str, show_both: bool = True) -> str:
    """
    Format a diameter for display, showing fractional form when appropriate.
    
    Args:
        diameter: Diameter value
        original_unit: Original unit ("mm" or "inch")
        show_both: Whether to show both fractional and decimal forms
        
    Returns:
        Formatted string for display
        
    Examples:
        >>> format_diameter_display(Decimal("0.25"), "inch")
        '1/4" (0.2500")'
        >>> format_diameter_display(Decimal("6.35"), "mm")
        '6.35mm'
    """
    if original_unit == "inch":
        # Try to display as fraction for imperial
        fraction_str = decimal_to_fraction_string(diameter)
        if fraction_str and show_both:
            return f'{fraction_str}" ({float(diameter):.4f}")'
        elif fraction_str:
            return f'{fraction_str}"'
        else:
            return f'{float(diameter):.4f}"'
    else:
        # Metric - just show decimal
        return f'{float(diameter):.3f}mm'