

from lxml import etree as ET
from unidecode import unidecode

tree = ET.parse("SpeciesType.xml")
root = tree.getroot()

ns = dict([node for _, node in ET.iterparse("SpeciesType.xml", events=['start-ns'])])

for index, element in enumerate(root.findall("./gml:dictionaryEntry/", ns)):
    print(element.tag)

print(index)

