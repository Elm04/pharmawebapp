def format_currency(value):
    """Formatte un nombre avec séparateurs de milliers et 2 décimales"""
    try:
        return "{:,.2f}".format(float(value)).replace(",", " ").replace(".", ",").replace(" ", ".")
    except (ValueError, TypeError):
        return value