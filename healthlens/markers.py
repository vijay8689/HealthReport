"""Conservative display grouping; original result names and units stay intact."""
import re


ALIASES = {
    "haemoglobin": "Hemoglobin", "hemoglobin": "Hemoglobin",
    "totalwbccount": "White blood cell count", "wbccount": "White blood cell count",
    "wbc": "White blood cell count", "totalleucocytecount": "White blood cell count",
    "totalrbccount": "Red blood cell count", "rbccount": "Red blood cell count",
    "rbc": "Red blood cell count",
    "plateletcount": "Platelet count",
    "serumcreatinine": "Creatinine", "creatinine": "Creatinine",
    "fastingbloodglucose": "Fasting glucose", "glucosefasting": "Fasting glucose",
    "glucosefastingfbs": "Fasting glucose", "glucosefastingbloodsugar": "Fasting glucose",
    "25ohvitaminvitd3": "25-OH Vitamin D", "25hydroxyvitamind": "25-OH Vitamin D",
    "vitamind25hydroxy": "25-OH Vitamin D",
    "bloodureanitrogen": "Blood urea nitrogen",
    "thyroidstimulatinghormonetsh": "Thyroid stimulating hormone (TSH)",
}


def marker_key(observation):
    token = re.sub(r"[^a-z0-9]", "", observation.name.casefold())
    name = ALIASES.get(token, re.sub(r"\s+", " ", observation.name.strip().rstrip(".,")).casefold())
    unit = re.sub(r"\s+", "", observation.unit).casefold()
    # Legacy hemoglobin mass-per-100-mL labels have the same numeric scale.
    if name == "Hemoglobin" and unit in {"gm%", "g%", "gm/dl", "g/dl", "g/100ml", "gm/100ml"}:
        unit = "g/dL"
    specimen = observation.specimen.strip().casefold()
    return name, unit, specimen
