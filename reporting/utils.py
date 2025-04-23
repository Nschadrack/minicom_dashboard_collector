from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def generate_periods(period_months: int, start_date_str: str = None) -> list:
    """
    Generate equal periods within a calendar year starting from a specified date.
    
    Args:
        period_months: Duration of each period in months
        start_date_str: Optional start date in 'YYYY-MM-DD' format
    
    Returns:
        List of tuples with (period_start, period_end) dates
    """
    # Set initial date
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = date(date.today().year, 1, 1)
    
    base_year = start_date.year
    end_of_year = date(base_year, 12, 31)
    
    periods = []
    current_start = start_date
    
    while True:
        # Calculate period end by adding months and subtracting 1 day
        next_end = current_start + relativedelta(months=+period_months) - relativedelta(days=1)
        
        # Ensure we don't go beyond the base year
        if next_end > end_of_year:
            next_end = end_of_year
        
        periods.append((current_start, next_end))
        
        # Prepare for next iteration
        current_start = next_end + relativedelta(days=1)
        
        # Stop if we've reached the end of the year
        if current_start > end_of_year:
            break
            
    return periods
