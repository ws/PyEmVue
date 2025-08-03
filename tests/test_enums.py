import unittest

from pyemvue.enums import Scale, Unit


class TestScale(unittest.TestCase):
    def test_scale_values(self):
        self.assertEqual(Scale.SECOND.value, "1S")
        self.assertEqual(Scale.MINUTE.value, "1MIN")
        self.assertEqual(Scale.MINUTES_15.value, "15MIN")
        self.assertEqual(Scale.HOUR.value, "1H")
        self.assertEqual(Scale.DAY.value, "1D")
        self.assertEqual(Scale.WEEK.value, "1W")
        self.assertEqual(Scale.MONTH.value, "1MON")
        self.assertEqual(Scale.YEAR.value, "1Y")

    def test_scale_enum_membership(self):
        self.assertIn(Scale.SECOND, Scale)
        self.assertIn(Scale.MINUTE, Scale)
        self.assertIn(Scale.MINUTES_15, Scale)
        self.assertIn(Scale.HOUR, Scale)
        self.assertIn(Scale.DAY, Scale)
        self.assertIn(Scale.WEEK, Scale)
        self.assertIn(Scale.MONTH, Scale)
        self.assertIn(Scale.YEAR, Scale)

    def test_scale_equality(self):
        self.assertEqual(Scale.SECOND, Scale.SECOND)
        self.assertNotEqual(Scale.SECOND, Scale.MINUTE)

    def test_scale_from_value(self):
        self.assertEqual(Scale("1S"), Scale.SECOND)
        self.assertEqual(Scale("1MIN"), Scale.MINUTE)
        self.assertEqual(Scale("15MIN"), Scale.MINUTES_15)
        self.assertEqual(Scale("1H"), Scale.HOUR)
        self.assertEqual(Scale("1D"), Scale.DAY)
        self.assertEqual(Scale("1W"), Scale.WEEK)
        self.assertEqual(Scale("1MON"), Scale.MONTH)
        self.assertEqual(Scale("1Y"), Scale.YEAR)

    def test_scale_invalid_value(self):
        with self.assertRaises(ValueError):
            Scale("INVALID")

    def test_scale_str_representation(self):
        self.assertEqual(str(Scale.SECOND), "Scale.SECOND")
        self.assertEqual(str(Scale.MINUTE), "Scale.MINUTE")

    def test_scale_all_members(self):
        expected_members = {
            'SECOND', 'MINUTE', 'MINUTES_15', 'HOUR', 
            'DAY', 'WEEK', 'MONTH', 'YEAR'
        }
        actual_members = {member.name for member in Scale}
        self.assertEqual(actual_members, expected_members)


class TestUnit(unittest.TestCase):
    def test_unit_values(self):
        self.assertEqual(Unit.VOLTS.value, "Voltage")
        self.assertEqual(Unit.KWH.value, "KilowattHours")
        self.assertEqual(Unit.USD.value, "Dollars")
        self.assertEqual(Unit.AMPHOURS.value, "AmpHours")
        self.assertEqual(Unit.TREES.value, "Trees")
        self.assertEqual(Unit.GAS.value, "GallonsOfGas")
        self.assertEqual(Unit.DRIVEN.value, "MilesDriven")
        self.assertEqual(Unit.CARBON.value, "Carbon")

    def test_unit_enum_membership(self):
        self.assertIn(Unit.VOLTS, Unit)
        self.assertIn(Unit.KWH, Unit)
        self.assertIn(Unit.USD, Unit)
        self.assertIn(Unit.AMPHOURS, Unit)
        self.assertIn(Unit.TREES, Unit)
        self.assertIn(Unit.GAS, Unit)
        self.assertIn(Unit.DRIVEN, Unit)
        self.assertIn(Unit.CARBON, Unit)

    def test_unit_equality(self):
        self.assertEqual(Unit.KWH, Unit.KWH)
        self.assertNotEqual(Unit.KWH, Unit.USD)

    def test_unit_from_value(self):
        self.assertEqual(Unit("Voltage"), Unit.VOLTS)
        self.assertEqual(Unit("KilowattHours"), Unit.KWH)
        self.assertEqual(Unit("Dollars"), Unit.USD)
        self.assertEqual(Unit("AmpHours"), Unit.AMPHOURS)
        self.assertEqual(Unit("Trees"), Unit.TREES)
        self.assertEqual(Unit("GallonsOfGas"), Unit.GAS)
        self.assertEqual(Unit("MilesDriven"), Unit.DRIVEN)
        self.assertEqual(Unit("Carbon"), Unit.CARBON)

    def test_unit_invalid_value(self):
        with self.assertRaises(ValueError):
            Unit("INVALID")

    def test_unit_str_representation(self):
        self.assertEqual(str(Unit.KWH), "Unit.KWH")
        self.assertEqual(str(Unit.USD), "Unit.USD")

    def test_unit_all_members(self):
        expected_members = {
            'VOLTS', 'KWH', 'USD', 'AMPHOURS', 
            'TREES', 'GAS', 'DRIVEN', 'CARBON'
        }
        actual_members = {member.name for member in Unit}
        self.assertEqual(actual_members, expected_members)

    def test_unit_case_sensitivity(self):
        with self.assertRaises(ValueError):
            Unit("kilowatthours")  # lowercase should fail
        
        with self.assertRaises(ValueError):
            Unit("KILOWATTHOURS")  # uppercase should fail


class TestEnumIntegration(unittest.TestCase):
    def test_enums_are_different_types(self):
        self.assertNotEqual(type(Scale.SECOND), type(Unit.KWH))

    def test_enums_cannot_be_compared(self):
        # Enums of different types can be compared, they just return False
        result = Scale.SECOND == Unit.KWH
        self.assertFalse(result)

    def test_enum_values_can_be_used_in_sets(self):
        scale_set = {Scale.SECOND, Scale.MINUTE, Scale.HOUR}
        self.assertEqual(len(scale_set), 3)
        self.assertIn(Scale.SECOND, scale_set)

        unit_set = {Unit.KWH, Unit.USD, Unit.VOLTS}
        self.assertEqual(len(unit_set), 3)
        self.assertIn(Unit.KWH, unit_set)

    def test_enum_values_can_be_used_in_dicts(self):
        scale_dict = {Scale.SECOND: "second", Scale.MINUTE: "minute"}
        self.assertEqual(scale_dict[Scale.SECOND], "second")

        unit_dict = {Unit.KWH: "energy", Unit.USD: "cost"}
        self.assertEqual(unit_dict[Unit.KWH], "energy")


if __name__ == '__main__':
    unittest.main()