# -*- coding: utf-8 -*-

def pageFormat(paper_name, unit='mm'):
    """
    Retrieves the dimensions (height and width) of paper sizes based on their name.

    Args:
        paper_name (str): The name of the paper size, such as 'A4' or 'ANSI A'.
        unit (str): The unit of measurement for the dimensions. Supported values are 'mm' (millimeters), 'cm' (centimeters), and 'in' (inches).

    Returns:
        tuple: A tuple containing the height and width of the paper size in the specified unit.

    Raises:
        ValueError: If an invalid unit is provided.
    """
    paper_sizes = {
        # ANSI sizes
        'ANSI A': (215.9, 279.4),
        'ANSI B': (279.4, 431.8),
        'ANSI C': (431.8, 558.8),
        'ANSI D': (558.8, 863.6),
        'ANSI E': (863.6, 1117.6),

        # Nom commum
        'Lettre': (215.9, 279.4),
        'Tabloide': (279.4, 431.8),

        # International standard sizes
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
        'A7': (74, 105),
        'A8': (52, 74),
        'A9': (37, 52),
        'A10': (26, 37),
        'B0': (1000, 1414),
        'B1': (707, 1000),
        'B2': (500, 707),
        'B3': (353, 500),
        'B4': (250, 353),
        'B5': (176, 250),
        'B6': (125, 176),
        'B7': (88, 125),
        'B8': (62, 88),
        'B9': (44, 62),
        'B10': (31, 44),
        'C0': (917, 1297),
        'C1': (648, 917),
        'C2': (458, 648),
        'C3': (324, 458),
        'C4': (229, 324),
        'C5': (162, 229),
        'C6': (114, 162),
        'C7': (81, 114),
        'C8': (57, 81),
        'C9': (40, 57),
        'C10': (28, 40)
    }
    
    if paper_name in paper_sizes:
        dimensions = paper_sizes[paper_name]
        if unit == 'mm': return dimensions
        elif unit == 'cm': return tuple(dim / 10 for dim in dimensions)
        elif unit == 'in': return tuple(dim * 0.0393701 for dim in dimensions)
        else: raise ValueError("Invalid unit. Supported units are 'mm', 'cm', and 'in'.")
    else: return None