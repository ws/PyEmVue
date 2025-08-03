import unittest
import datetime
from dateutil.parser import parse

from pyemvue.device import (
    VueDevice, VueDeviceChannel, VueUsageDevice, VueDeviceChannelUsage,
    OutletDevice, ChargerDevice, ChannelType, Vehicle, VehicleStatus
)


class TestVueDevice(unittest.TestCase):
    def test_init(self):
        device = VueDevice(gid=123, manId="EMP123", modelNum="Vue2", firmwareVersion="1.0.0")
        
        self.assertEqual(device.device_gid, 123)
        self.assertEqual(device.manufacturer_id, "EMP123")
        self.assertEqual(device.model, "Vue2")
        self.assertEqual(device.firmware, "1.0.0")
        self.assertEqual(device.parent_device_gid, 0)
        self.assertEqual(device.parent_channel_num, "")
        self.assertEqual(device.channels, [])
        self.assertIsNone(device.outlet)
        self.assertIsNone(device.ev_charger)
        self.assertFalse(device.connected)
        self.assertEqual(device.offline_since, datetime.datetime.min)

    def test_from_json_dictionary_basic(self):
        json_data = {
            "deviceGid": 456,
            "manufacturerDeviceId": "EMP456",
            "model": "Vue3",
            "firmware": "2.0.0",
            "parentDeviceGid": 123,
            "parentChannelNum": "1"
        }
        
        device = VueDevice().from_json_dictionary(json_data)
        
        self.assertEqual(device.device_gid, 456)
        self.assertEqual(device.manufacturer_id, "EMP456")
        self.assertEqual(device.model, "Vue3")
        self.assertEqual(device.firmware, "2.0.0")
        self.assertEqual(device.parent_device_gid, 123)
        self.assertEqual(device.parent_channel_num, "1")

    def test_from_json_dictionary_with_channels(self):
        json_data = {
            "deviceGid": 789,
            "channels": [
                {"deviceGid": 789, "name": "Main", "channelNum": "1,2,3"},
                {"deviceGid": 789, "name": "Circuit 1", "channelNum": "4"}
            ]
        }
        
        device = VueDevice().from_json_dictionary(json_data)
        
        self.assertEqual(len(device.channels), 2)
        self.assertEqual(device.channels[0].name, "Main")
        self.assertEqual(device.channels[1].name, "Circuit 1")

    def test_from_json_dictionary_with_outlet(self):
        json_data = {
            "deviceGid": 999,
            "outlet": {
                "deviceGid": 999,
                "outletOn": True,
                "loadGid": 1001
            }
        }
        
        device = VueDevice().from_json_dictionary(json_data)
        
        self.assertIsNotNone(device.outlet)
        self.assertEqual(device.outlet.device_gid, 999)
        self.assertTrue(device.outlet.outlet_on)
        self.assertEqual(device.outlet.load_gid, 1001)

    def test_from_json_dictionary_with_charger(self):
        json_data = {
            "deviceGid": 888,
            "evCharger": {
                "deviceGid": 888,
                "chargerOn": False,
                "chargingRate": 0,
                "maxChargingRate": 32
            }
        }
        
        device = VueDevice().from_json_dictionary(json_data)
        
        self.assertIsNotNone(device.ev_charger)
        self.assertEqual(device.ev_charger.device_gid, 888)
        self.assertFalse(device.ev_charger.charger_on)
        self.assertEqual(device.ev_charger.max_charging_rate, 32)

    def test_from_json_dictionary_with_connection_status(self):
        json_data = {
            "deviceGid": 777,
            "deviceConnected": {
                "connected": True,
                "offlineSince": "2023-01-01T12:00:00Z"
            }
        }
        
        device = VueDevice().from_json_dictionary(json_data)
        
        self.assertTrue(device.connected)
        self.assertEqual(device.offline_since, parse("2023-01-01T12:00:00Z"))

    def test_populate_location_properties_from_json_basic(self):
        json_data = {
            "deviceName": "Main Panel",
            "displayName": "Home Energy Monitor",
            "zipCode": "12345",
            "timeZone": "America/New_York",
            "usageCentPerKwHour": 12.5,
            "peakDemandDollarPerKw": 15.0,
            "billingCycleStartDay": 1,
            "solar": True
        }
        
        device = VueDevice()
        device.populate_location_properties_from_json(json_data)
        
        self.assertEqual(device.device_name, "Main Panel")
        self.assertEqual(device.display_name, "Home Energy Monitor")
        self.assertEqual(device.zip_code, "12345")
        self.assertEqual(device.time_zone, "America/New_York")
        self.assertEqual(device.usage_cent_per_kw_hour, 12.5)
        self.assertEqual(device.peak_demand_dollar_per_kw, 15.0)
        self.assertEqual(device.billing_cycle_start_day, 1)
        self.assertTrue(device.solar)

    def test_populate_location_properties_with_location_info(self):
        json_data = {
            "locationInformation": {
                "airConditioning": "central",
                "heatSource": "heat_pump",
                "locationSqFt": "2000",
                "numElectricCars": "1",
                "locationType": "house",
                "numPeople": "4",
                "swimmingPool": "true",
                "hotTub": "false"
            },
            "latitudeLongitude": {
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        }
        
        device = VueDevice()
        device.populate_location_properties_from_json(json_data)
        
        self.assertEqual(device.air_conditioning, "central")
        self.assertEqual(device.heat_source, "heat_pump")
        self.assertEqual(device.location_sqft, "2000")
        self.assertEqual(device.num_electric_cars, "1")
        self.assertEqual(device.location_type, "house")
        self.assertEqual(device.num_people, "4")
        self.assertEqual(device.swimming_pool, "true")
        self.assertEqual(device.hot_tub, "false")
        self.assertEqual(device.latitude, 40.7128)
        self.assertEqual(device.longitude, -74.0060)


class TestVueDeviceChannel(unittest.TestCase):
    def test_init(self):
        channel = VueDeviceChannel(
            gid=123,
            name="Main",
            channelNum="1,2,3",
            channelMultiplier=1.5,
            channelTypeGid=1
        )
        
        self.assertEqual(channel.device_gid, 123)
        self.assertEqual(channel.name, "Main")
        self.assertEqual(channel.channel_num, "1,2,3")
        self.assertEqual(channel.channel_multiplier, 1.5)
        self.assertEqual(channel.channel_type_gid, 1)
        self.assertEqual(channel.nested_devices, {})
        self.assertEqual(channel.type, "")
        self.assertIsNone(channel.parent_channel_num)

    def test_from_json_dictionary(self):
        json_data = {
            "deviceGid": 456,
            "name": "Circuit 1",
            "channelNum": "4",
            "channelMultiplier": 2.0,
            "channelTypeGid": 2,
            "type": "FiftyAmp",
            "parentChannelNum": "1,2,3"
        }
        
        channel = VueDeviceChannel().from_json_dictionary(json_data)
        
        self.assertEqual(channel.device_gid, 456)
        self.assertEqual(channel.name, "Circuit 1")
        self.assertEqual(channel.channel_num, "4")
        self.assertEqual(channel.channel_multiplier, 2.0)
        self.assertEqual(channel.channel_type_gid, 2)
        self.assertEqual(channel.type, "FiftyAmp")
        self.assertEqual(channel.parent_channel_num, "1,2,3")

    def test_as_dictionary(self):
        channel = VueDeviceChannel(
            gid=789,
            name="Test Channel",
            channelNum="5",
            channelMultiplier=1.0,
            channelTypeGid=3
        )
        channel.type = "Main"
        channel.parent_channel_num = "1"
        
        result = channel.as_dictionary()
        
        expected = {
            "deviceGid": 789,
            "name": "Test Channel",
            "channelNum": "5",
            "channelMultiplier": 1.0,
            "channelTypeGid": 3,
            "type": "Main",
            "parentChannelNum": "1"
        }
        self.assertEqual(result, expected)


class TestVueUsageDevice(unittest.TestCase):
    def test_init(self):
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        device = VueUsageDevice(gid=123, timestamp=timestamp)
        
        self.assertEqual(device.device_gid, 123)
        self.assertEqual(device.timestamp, timestamp)
        self.assertEqual(device.channels, {})

    def test_from_json_dictionary(self):
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        json_data = {
            "deviceGid": 456,
            "channelUsages": [
                {"channelNum": "1", "usage": 1.5, "name": "Main"},
                {"channelNum": "2", "usage": 0.5, "name": "Circuit 1"}
            ]
        }
        
        device = VueUsageDevice(timestamp=timestamp).from_json_dictionary(json_data)
        
        self.assertEqual(device.device_gid, 456)
        self.assertEqual(len(device.channels), 2)
        self.assertIn("1", device.channels)
        self.assertIn("2", device.channels)
        self.assertEqual(device.channels["1"].usage, 1.5)
        self.assertEqual(device.channels["2"].usage, 0.5)

    def test_from_json_dictionary_empty(self):
        device = VueUsageDevice().from_json_dictionary({})
        self.assertEqual(device.channels, {})

    def test_from_json_dictionary_none(self):
        device = VueUsageDevice().from_json_dictionary(None)
        self.assertEqual(device.channels, {})


class TestVueDeviceChannelUsage(unittest.TestCase):
    def test_init(self):
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        channel = VueDeviceChannelUsage(
            gid=123,
            usage=2.5,
            channelNum="1",
            name="Main",
            timestamp=timestamp
        )
        
        self.assertEqual(channel.device_gid, 123)
        self.assertEqual(channel.usage, 2.5)
        self.assertEqual(channel.channel_num, "1")
        self.assertEqual(channel.name, "Main")
        self.assertEqual(channel.timestamp, timestamp)
        self.assertEqual(channel.percentage, 0.0)
        self.assertEqual(channel.nested_devices, {})

    def test_from_json_dictionary(self):
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        json_data = {
            "name": "Circuit 1",
            "deviceGid": 456,
            "channelNum": "2",
            "usage": 1.8,
            "percentage": 25.5
        }
        
        channel = VueDeviceChannelUsage(timestamp=timestamp).from_json_dictionary(json_data)
        
        self.assertEqual(channel.name, "Circuit 1")
        self.assertEqual(channel.device_gid, 456)
        self.assertEqual(channel.channel_num, "2")
        self.assertEqual(channel.usage, 1.8)
        self.assertEqual(channel.percentage, 25.5)

    def test_from_json_dictionary_with_nested_devices(self):
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        json_data = {
            "channelNum": "1",
            "usage": 3.0,
            "nestedDevices": [
                {
                    "deviceGid": 789,
                    "channelUsages": [
                        {"channelNum": "1", "usage": 1.0}
                    ]
                },
                {
                    "deviceGid": 790,
                    "channelUsages": [
                        {"channelNum": "1", "usage": 2.0}
                    ]
                }
            ]
        }
        
        channel = VueDeviceChannelUsage(timestamp=timestamp).from_json_dictionary(json_data)
        
        self.assertEqual(len(channel.nested_devices), 2)
        self.assertIn(789, channel.nested_devices)
        self.assertIn(790, channel.nested_devices)
        self.assertEqual(channel.nested_devices[789].device_gid, 789)
        self.assertEqual(channel.nested_devices[790].device_gid, 790)

    def test_from_json_dictionary_channel_usages_wrapper(self):
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        json_data = {
            "channelUsages": {
                "name": "Wrapped Channel",
                "channelNum": "3",
                "usage": 0.8
            }
        }
        
        channel = VueDeviceChannelUsage(timestamp=timestamp).from_json_dictionary(json_data)
        
        self.assertEqual(channel.name, "Wrapped Channel")
        self.assertEqual(channel.channel_num, "3")
        self.assertEqual(channel.usage, 0.8)


class TestOutletDevice(unittest.TestCase):
    def test_init(self):
        outlet = OutletDevice(gid=123, on=True)
        
        self.assertEqual(outlet.device_gid, 123)
        self.assertTrue(outlet.outlet_on)
        self.assertEqual(outlet.load_gid, 0)
        self.assertEqual(outlet.schedules, [])

    def test_from_json_dictionary(self):
        json_data = {
            "deviceGid": 456,
            "outletOn": False,
            "loadGid": 789
        }
        
        outlet = OutletDevice().from_json_dictionary(json_data)
        
        self.assertEqual(outlet.device_gid, 456)
        self.assertFalse(outlet.outlet_on)
        self.assertEqual(outlet.load_gid, 789)

    def test_as_dictionary(self):
        outlet = OutletDevice(gid=999, on=True)
        outlet.load_gid = 1001
        
        result = outlet.as_dictionary()
        
        expected = {
            "deviceGid": 999,
            "outletOn": True,
            "loadGid": 1001
        }
        self.assertEqual(result, expected)


class TestChargerDevice(unittest.TestCase):
    def test_init(self):
        charger = ChargerDevice(gid=123, on=True)
        
        self.assertEqual(charger.device_gid, 123)
        self.assertTrue(charger.charger_on)
        self.assertEqual(charger.message, "")
        self.assertEqual(charger.status, "")
        self.assertEqual(charger.icon, "")
        self.assertEqual(charger.icon_label, "")
        self.assertEqual(charger.icon_detail_text, "")
        self.assertEqual(charger.fault_text, "")
        self.assertEqual(charger.charging_rate, 0)
        self.assertEqual(charger.max_charging_rate, 0)
        self.assertFalse(charger.off_peak_schedules_enabled)
        self.assertEqual(charger.custom_schedules, [])
        self.assertEqual(charger.load_gid, 0)

    def test_from_json_dictionary(self):
        json_data = {
            "deviceGid": 456,
            "loadGid": 789,
            "chargerOn": False,
            "message": "Ready to charge",
            "status": "available",
            "icon": "plug",
            "iconLabel": "Available",
            "iconDetailText": "Ready for charging",
            "faultText": "",
            "chargingRate": 16,
            "maxChargingRate": 32,
            "offPeakSchedulesEnabled": True,
            "debugCode": "DEBUG123",
            "proControlCode": "PRO456",
            "breakerPIN": "1234"
        }
        
        charger = ChargerDevice().from_json_dictionary(json_data)
        
        self.assertEqual(charger.device_gid, 456)
        self.assertEqual(charger.load_gid, 789)
        self.assertFalse(charger.charger_on)
        self.assertEqual(charger.message, "Ready to charge")
        self.assertEqual(charger.status, "available")
        self.assertEqual(charger.icon, "plug")
        self.assertEqual(charger.icon_label, "Available")
        self.assertEqual(charger.icon_detail_text, "Ready for charging")
        self.assertEqual(charger.fault_text, "")
        self.assertEqual(charger.charging_rate, 16)
        self.assertEqual(charger.max_charging_rate, 32)
        self.assertTrue(charger.off_peak_schedules_enabled)
        self.assertEqual(charger.debug_code, "DEBUG123")
        self.assertEqual(charger.pro_control_code, "PRO456")
        self.assertEqual(charger.breaker_pin, "1234")

    def test_as_dictionary(self):
        charger = ChargerDevice(gid=999, on=True)
        charger.load_gid = 1001
        charger.charging_rate = 24
        charger.max_charging_rate = 48
        
        result = charger.as_dictionary()
        
        expected = {
            "deviceGid": 999,
            "loadGid": 1001,
            "chargerOn": True,
            "chargingRate": 24,
            "maxChargingRate": 48
        }
        self.assertEqual(result, expected)

    def test_as_dictionary_with_breaker_pin(self):
        charger = ChargerDevice(gid=999, on=True)
        charger.breaker_pin = "5678"
        
        result = charger.as_dictionary()
        
        self.assertIn("breakerPIN", result)
        self.assertEqual(result["breakerPIN"], "5678")


class TestChannelType(unittest.TestCase):
    def test_init(self):
        channel_type = ChannelType(gid=1, description="Main", selectable=True)
        
        self.assertEqual(channel_type.channel_type_gid, 1)
        self.assertEqual(channel_type.description, "Main")
        self.assertTrue(channel_type.selectable)

    def test_from_json_dictionary(self):
        json_data = {
            "channelTypeGid": 2,
            "description": "FiftyAmp",
            "selectable": False
        }
        
        channel_type = ChannelType().from_json_dictionary(json_data)
        
        self.assertEqual(channel_type.channel_type_gid, 2)
        self.assertEqual(channel_type.description, "FiftyAmp")
        self.assertFalse(channel_type.selectable)


class TestVehicle(unittest.TestCase):
    def test_init(self):
        vehicle = Vehicle(
            vehicleGid=123,
            vendor="Tesla",
            apiId="API123",
            displayName="My Tesla",
            loadGid="456",
            make="Tesla",
            model="Model 3",
            year=2023
        )
        
        self.assertEqual(vehicle.vehicle_gid, 123)
        self.assertEqual(vehicle.vendor, "Tesla")
        self.assertEqual(vehicle.api_id, "API123")
        self.assertEqual(vehicle.display_name, "My Tesla")
        self.assertEqual(vehicle.load_gid, "456")
        self.assertEqual(vehicle.make, "Tesla")
        self.assertEqual(vehicle.model, "Model 3")
        self.assertEqual(vehicle.year, 2023)

    def test_from_json_dictionary(self):
        json_data = {
            "vehicleGid": 789,
            "vendor": "Ford",
            "apiId": "API789",
            "displayName": "My F-150",
            "loadGid": "101112",
            "make": "Ford",
            "model": "F-150 Lightning",
            "year": 2022
        }
        
        vehicle = Vehicle().from_json_dictionary(json_data)
        
        self.assertEqual(vehicle.vehicle_gid, 789)
        self.assertEqual(vehicle.vendor, "Ford")
        self.assertEqual(vehicle.api_id, "API789")
        self.assertEqual(vehicle.display_name, "My F-150")
        self.assertEqual(vehicle.load_gid, "101112")
        self.assertEqual(vehicle.make, "Ford")
        self.assertEqual(vehicle.model, "F-150 Lightning")
        self.assertEqual(vehicle.year, 2022)

    def test_as_dictionary(self):
        vehicle = Vehicle(
            vehicleGid=555,
            vendor="Chevy",
            apiId="API555",
            displayName="My Bolt",
            loadGid="666",
            make="Chevrolet",
            model="Bolt EV",
            year=2021
        )
        
        result = vehicle.as_dictionary()
        
        expected = {
            "vehicleGid": 555,
            "vendor": "Chevy",
            "apiId": "API555",
            "displayName": "My Bolt",
            "loadGid": "666",
            "make": "Chevrolet",
            "model": "Bolt EV",
            "year": 2021
        }
        self.assertEqual(result, expected)


class TestVehicleStatus(unittest.TestCase):
    def test_init(self):
        status = VehicleStatus(
            vehicleGid=123,
            vehicleState="parked",
            batteryLevel=80,
            batteryRange=250,
            chargingState="charging",
            chargeLimitPercent=90,
            minutesToFullCharge=45,
            chargeCurrentRequest=16,
            chargeCurrentRequestMax=32
        )
        
        self.assertEqual(status.vehicle_gid, 123)
        self.assertEqual(status.vehicle_state, "parked")
        self.assertEqual(status.battery_level, 80)
        self.assertEqual(status.battery_range, 250)
        self.assertEqual(status.charging_state, "charging")
        self.assertEqual(status.charge_limit_percent, 90)
        self.assertEqual(status.minutes_to_full_charge, 45)
        self.assertEqual(status.charge_current_request, 16)
        self.assertEqual(status.charge_current_request_max, 32)

    def test_from_json_dictionary(self):
        json_data = {
            "settings": {
                "vehicleGid": 456,
                "vehicleState": "driving",
                "batteryLevel": 65,
                "batteryRange": 180,
                "chargingState": "not_charging",
                "chargeLimitPercent": 85,
                "minutesToFullCharge": 0,
                "chargeCurrentRequest": 0,
                "chargeCurrentRequestMax": 24
            }
        }
        
        status = VehicleStatus().from_json_dictionary(json_data)
        
        self.assertEqual(status.vehicle_gid, 456)
        self.assertEqual(status.vehicle_state, "driving")
        self.assertEqual(status.battery_level, 65)
        self.assertEqual(status.battery_range, 180)
        self.assertEqual(status.charging_state, "not_charging")
        self.assertEqual(status.charge_limit_percent, 85)
        self.assertEqual(status.minutes_to_full_charge, 0)
        self.assertEqual(status.charge_current_request, 0)
        self.assertEqual(status.charge_current_request_max, 24)

    def test_as_dictionary(self):
        status = VehicleStatus(
            vehicleGid=789,
            vehicleState="parked",
            batteryLevel=95,
            batteryRange=300,
            chargingState="complete",
            chargeLimitPercent=100,
            minutesToFullCharge=0,
            chargeCurrentRequest=0,
            chargeCurrentRequestMax=48
        )
        
        result = status.as_dictionary()
        
        expected = {
            "vehicleGid": 789,
            "vehicleState": "parked",
            "batteryLevel": 95,
            "batteryRange": 300,
            "chargingState": "complete",
            "chargeLimitPercent": 100,
            "minutesToFullCharge": 0,
            "chargeCurrentRequest": 0,
            "chargeCurrentRequestMax": 48
        }
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()