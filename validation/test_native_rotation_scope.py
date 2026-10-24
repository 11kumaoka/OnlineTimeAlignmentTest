"""Safety boundaries for the experimentally validated native one-axis XML charts."""
import math
import unittest
import xml.etree.ElementTree as ET
from validation.telescope_closure.rotation import rotate_component


class NativeRotationScope(unittest.TestCase):
    def component(self):
        return ET.fromstring('<module_component><rotation x="-pi/2" y="-pi/2" z="0"/></module_component>')

    def test_signed_increment_and_current_orientation(self):
        for axis,attribute in [('x','y'),('y','x')]:
            component=self.component()
            rotate_component(component,.004,axis)
            rotate_component(component,-.005,axis)
            self.assertAlmostEqual(float(component.find('rotation').get(attribute)),-math.pi/2+.001,places=14)
            self.assertEqual(component.find('rotation').get('z'),'0')

    def test_coupled_rotation_is_rejected(self):
        for first,second in [('x','y'),('y','x')]:
            component=self.component();rotate_component(component,.002,first)
            before=ET.tostring(component)
            with self.assertRaises(ValueError):rotate_component(component,.003,second)
            self.assertEqual(ET.tostring(component),before)

    def test_unsupported_or_nonfinite_update_is_rejected(self):
        for angle,axis in [(.001,'z'),(.02,'x'),(math.inf,'y'),(math.nan,'x')]:
            component=self.component();before=ET.tostring(component)
            with self.assertRaises(ValueError):rotate_component(component,angle,axis)
            self.assertEqual(ET.tostring(component),before)
