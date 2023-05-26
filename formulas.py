# https://www.garrtool.com/resources/machining-formulas/


def feed(RPM, CPT, flutes):
    """
    Calculate the feed rate based on the RPM (Revolutions Per Minute), CPT (Chip Load Per Tooth),
    and the number of flutes.

    Args:
        RPM (float): The rotational speed of the cutting tool in revolutions per minute.
        CPT (float): The amount of material removed per tooth during each revolution of the tool,
            expressed in millimeters per tooth (mm/tooth).
        flutes (int): The number of flutes (cutting edges) on the tool.

    Returns:
        float: The feed rate in millimeters per minute, which is the product of RPM, CPT, and the number of flutes.

    """
    return RPM * CPT * flutes


def thou_to_mm(thou):
    """
    Convert a length value from thousandths of an inch (thou) to millimeters (mm).

    Args:
        thou (float): The length value in thousandths of an inch (thou) to be converted to millimeters.

    Returns:
        float: The equivalent length value converted to millimeters.

    """
    return thou / 39.370078740157


def SFM_to_SMM(SFM):
    """
    Convert a speed value from Surface Feet per Minute (SFM) to Surface Millimeters per Minute (SMM).

    Args:
        SFM (float): The speed value in Surface Feet per Minute (SFM) to be converted.

    Returns:
        float: The equivalent speed value converted to Surface Millimeters per Minute (SMM).

    """
    return SFM * 0.3048


print(thou_to_mm(1))


class FeedsAndSpeeds:
    def __init__(self):
        # Material
        self.hb_min = None
        self.hb_max = None
        self.k_factor = None

        # Tool
        self.diameter = None
        self.flute_num = None
        self.flute_len = None
        self.lead_angle = None

        # Cutting
        self.doc = None
        self.woc = None
        self.smm = None
        self.mmpt = None

    def print_values(self):
        print("\nHB Min:", self.hb_min)
        print("HB Max:", self.hb_max)
        print("K-Factor:", self.k_factor)
        print("Cutting Diameter:", self.diameter)
        print("Flute Num:", self.flute_num)
        print("Flute Length:", self.flute_len)
        print("Lead Angle:", self.lead_angle)
        print("Depth of Cut:", self.doc)
        print("Width of Cut:", self.woc)
        print("Surface Meters per Minute:", self.smm)
        print("Millimeters per tooth:", self.mmpt)

    def calculate(self):
        pass


# SFM = (Pi * RPM * Diameter) / 12

# RPM = (12 * SFM) / (Pi * Diameter)
# MRR = WOC * DOC * IPM
# HP = MRR / K
