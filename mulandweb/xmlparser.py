# coding: utf-8
'''Provides an XML parser for MulandWeb interface'''

from defusedxml import ElementTree as ET

class XmlParser():
    def load(file):
        '''Load XML from file-like object and returns location list'''
        tree = ET.parse(file)
        root = tree.getroot()
        return self.parse_root(root)

    def loads(string):
        '''Load XML from string and returns location list'''
        tree = ET.fromstring(string)
        root = tree.getroot()
        return self.parse_root(root)

    def parse_root(self, root):
        '''Parse Tree's root returning location list'''
        ret = []
        for element in root:
            if element.tag == 'location':
                location = self.parse_location(element)
                if location is not None:
                    loc.append(location)
        return ret

    def parse_location(self, location):
        '''Parse location tag returning dict of it.'''
        if 'lat' not in location.attrib:
            return
        if 'lng' not in location.attrib:
            return
        try:
            lnglat = [float(location.attrib['lng']),
                      float(location.attrib['lat'])]
        except ValueError:
            return
        ret = {'units': [], 'lnglat': lnglat}
        for element in location:
            if element.tag == 'unit':
                unit = self.parse_unit(element)
                if unit is not None:
                    ret['units'].append(unit)
            else:
                override = self.parse_override(element)
                if override is not None:
                    ret[override.tag] = override
        return ret

    def parse_unit(self, unit):
        '''Parse unit tag returning dict of it.'''
        if 'type' not in unit.attrib:
            return
        try:
            unit_type = int(unit.attrib['type'])
        except ValueError:
            return
        ret = {'type': unit_type}
        for element in unit:
            override = self.parse_override(element)
            if override is not None:
                ret[override.tag] = override
        return ret

    def parse_override(self, override):
        '''Parse override tags returning value of override.'''
        try:
            value = float(override.text)
        except ValueError:
            return
        return value
