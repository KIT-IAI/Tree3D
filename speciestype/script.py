# Script to treansform CityGML Vegetation Species Code list
# Input: XMl Document dexcribing vegetation
# Output: How it is used by ArbokaTransformer

from lxml import etree as ET
from unidecode import unidecode

keys = []
keyvalues = []

tree = ET.parse("SpeciesType.xml")
root = tree.getroot()

ns = dict([node for _, node in ET.iterparse("SpeciesType.xml", events=['start-ns'])])

for element in root.findall("./gml:dictionaryEntry/", ns):
    for child in element:
        if child.tag == "{http://www.opengis.net/gml}description":
            key = child.text
        if child.tag == "{http://www.opengis.net/gml}name":
            value = child.text
    key = key.strip().lower()
    if key not in keys:
        keyvalues.append("%s:%s" % (key, value))
        keys.append(key)
    if unidecode(key) not in keys:
        keyvalues.append("%s:%s" % (unidecode(key), value))
        keys.append(unidecode(key))

keyvalues.sort()

with open("citygml_vegetation_species_codes.dict", "w", encoding="utf-8") as file:
    file.write("# This file maps tree species names to its corresponding CityGML Vegetation SolitaryVegetationObject "
               "Species Code-List\n# This is the code list as defined in "
               "https://www.sig3d.org/codelists/standard/vegetation/2.0/SolitaryVegetationObject_species.xml\n# You "
               "may append or alter this file if the program does not recognize the way you the species type in your "
               "dataset\n# When altering this file, ALWAYS use lower-case letters when writing the species type\n\n")
    for element in keyvalues:
        file.write(element)
        file.write("\n")
