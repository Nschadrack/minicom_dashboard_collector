PRODUCT_QUANTITIES = (
        ("Volume", "Volume"),
        ("Weight", "Weight"),
        ("Size", "Size"),
        ("Other", "Other"),
    )

PRODUCT_QUANTITY_UNITS = (
        ("mL", "Milliliters"),
        ("g", "Grams"),
        ("m", "meters"),
        ("unk", "Unknown"),
    )

PRODUCT_QUANTITIES_UNITS_MAP = {
        "Volume": "mL",
        "Weight": "g",
        "Size": "m",
        "Other": "unk"
    }

PRODUCT_PACKAGING_MATERIAL = (
    ("Paper", "Paper"),
    ("Cardboard", "Cardboard"),
    ("Glass", "Glass"),
    ("Plastic", "Plastic"),
    ("Cotton", "Cotton"),
    ("Aluminum", "Aluminum"),
    ("Plant based", "Plant based"),
    ("Metal", "Metal"),
    ("Wood", "Wood"),
    ("Other", "Other"),
)

PRODUCT_PRODUCTION_CAPACITY_UNIT = (
    ("Pieces", "Pieces"),
    ("Liters", "Liters"),
    ("Kilograms", "Kilograms"),
)

PRODUCT_PRODUCTION_CAPACITY_PERIOD = (
    ("Day", "Day"),
    ("Month", "Month"),
    ("Year", "Year"),
)

CURRENCIES = (
    ("RWF", "RWF"),
    ("USD", "USD"),
)