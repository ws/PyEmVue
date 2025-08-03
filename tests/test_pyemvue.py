import unittest
from unittest.mock import Mock, patch, mock_open
import datetime
import json
from dateutil.parser import parse

from pyemvue.pyemvue import PyEmVue, _format_time
from pyemvue.auth import Auth, SimulatedAuth
from pyemvue.device import (
    VueDevice, VueDeviceChannel, VueUsageDevice, VueDeviceChannelUsage,
    OutletDevice, ChargerDevice, ChannelType, Vehicle, VehicleStatus,
    EvChargingReport
)
from pyemvue.customer import Customer
from pyemvue.enums import Scale, Unit


class TestPyEmVue(unittest.TestCase):
    def setUp(self):
        self.vue = PyEmVue()
        self.mock_auth = Mock(spec=Auth)
        self.vue.auth = self.mock_auth

    def test_init(self):
        vue = PyEmVue(connect_timeout=5.0, read_timeout=15.0)
        self.assertEqual(vue.connect_timeout, 5.0)
        self.assertEqual(vue.read_timeout, 15.0)
        self.assertIsNone(vue.username)
        self.assertIsNone(vue.token_storage_file)
        self.assertIsNone(vue.customer)

    def test_down_for_maintenance_no_maintenance(self):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = self.vue.down_for_maintenance()
            self.assertIsNone(result)

    def test_down_for_maintenance_with_message(self):
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"msg": "System maintenance in progress"}'
            mock_response.json.return_value = {"msg": "System maintenance in progress"}
            mock_get.return_value = mock_response
            
            result = self.vue.down_for_maintenance()
            self.assertEqual(result, "System maintenance in progress")

    def test_get_devices_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"devices": [{"deviceGid": 123, "model": "Vue2"}]}'
        mock_response.json.return_value = {
            "devices": [{"deviceGid": 123, "model": "Vue2"}]
        }
        self.mock_auth.request.return_value = mock_response
        
        devices = self.vue.get_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].device_gid, 123)
        self.assertEqual(devices[0].model, "Vue2")

    def test_get_devices_empty_response(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        self.mock_auth.request.return_value = mock_response
        
        devices = self.vue.get_devices()
        self.assertEqual(len(devices), 0)

    def test_populate_device_properties(self):
        device = VueDevice(gid=123)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"deviceName": "Main Panel"}'
        mock_response.json.return_value = {"deviceName": "Main Panel"}
        self.mock_auth.request.return_value = mock_response
        
        result = self.vue.populate_device_properties(device)
        self.assertEqual(result.device_name, "Main Panel")

    def test_update_channel(self):
        channel = VueDeviceChannel(gid=123, channelNum="1")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"name": "Updated Channel"}'
        mock_response.json.return_value = {"name": "Updated Channel"}
        self.mock_auth.request.return_value = mock_response
        
        result = self.vue.update_channel(channel)
        self.assertEqual(result.name, "Updated Channel")

    def test_get_customer_details_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"customerGid": 456, "email": "test@example.com"}'
        mock_response.json.return_value = {"customerGid": 456, "email": "test@example.com"}
        self.mock_auth.request.return_value = mock_response
        
        customer = self.vue.get_customer_details()
        self.assertIsNotNone(customer)
        self.assertEqual(customer.customer_gid, 456)
        self.assertEqual(customer.email, "test@example.com")

    def test_get_customer_details_empty_response(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        self.mock_auth.request.return_value = mock_response
        
        customer = self.vue.get_customer_details()
        self.assertIsNone(customer)

    def test_get_device_list_usage_single_device(self):
        instant = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"deviceListUsages": {"instant": "2023-01-01T12:00:00Z", "devices": [{"deviceGid": 123, "channelUsages": [{"channelNum": "1", "usage": 1.5}]}]}}'
        mock_response.json.return_value = {
            "deviceListUsages": {
                "instant": "2023-01-01T12:00:00Z",
                "devices": [
                    {
                        "deviceGid": 123,
                        "channelUsages": [{"channelNum": "1", "usage": 1.5}]
                    }
                ]
            }
        }
        self.mock_auth.request.return_value = mock_response
        
        devices = self.vue.get_device_list_usage("123", instant)
        self.assertEqual(len(devices), 1)
        self.assertIn(123, devices)
        self.assertEqual(devices[123].device_gid, 123)

    def test_get_device_list_usage_multiple_devices(self):
        instant = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"deviceListUsages": {"instant": "2023-01-01T12:00:00Z", "devices": [{"deviceGid": 123}, {"deviceGid": 456}]}}'
        mock_response.json.return_value = {
            "deviceListUsages": {
                "instant": "2023-01-01T12:00:00Z",
                "devices": [{"deviceGid": 123}, {"deviceGid": 456}]
            }
        }
        self.mock_auth.request.return_value = mock_response
        
        devices = self.vue.get_device_list_usage(["123", "456"], instant)
        self.assertEqual(len(devices), 2)
        self.assertIn(123, devices)
        self.assertIn(456, devices)

    def test_get_chart_usage_success(self):
        channel = VueDeviceChannel(gid=123, channelNum="1")
        start = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2023, 1, 1, 23, 59, 59, tzinfo=datetime.timezone.utc)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"firstUsageInstant": "2023-01-01T00:00:00Z", "usageList": [1.0, 1.5, 2.0]}'
        mock_response.json.return_value = {
            "firstUsageInstant": "2023-01-01T00:00:00Z",
            "usageList": [1.0, 1.5, 2.0]
        }
        self.mock_auth.request.return_value = mock_response
        
        usage, instant = self.vue.get_chart_usage(channel, start, end)
        self.assertEqual(usage, [1.0, 1.5, 2.0])
        self.assertEqual(instant, parse("2023-01-01T00:00:00Z"))

    def test_get_chart_usage_mains_channel(self):
        channel = VueDeviceChannel(gid=123, channelNum="MainsFromGrid")
        start = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        
        usage, instant = self.vue.get_chart_usage(channel, start)
        self.assertEqual(usage, [])
        self.assertEqual(instant, start)

    def test_get_outlets_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"outlets": [{"deviceGid": 789, "outletOn": true}]}'
        mock_response.json.return_value = {
            "outlets": [{"deviceGid": 789, "outletOn": True}]
        }
        self.mock_auth.request.return_value = mock_response
        
        outlets = self.vue.get_outlets()
        self.assertEqual(len(outlets), 1)
        self.assertEqual(outlets[0].device_gid, 789)
        self.assertTrue(outlets[0].outlet_on)

    def test_update_outlet(self):
        outlet = OutletDevice(gid=789, on=False)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deviceGid": 789, "outletOn": True}
        self.mock_auth.request.return_value = mock_response
        
        result = self.vue.update_outlet(outlet, on=True)
        self.assertTrue(result.outlet_on)

    def test_get_chargers_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"evChargers": [{"deviceGid": 999, "chargerOn": false}]}'
        mock_response.json.return_value = {
            "evChargers": [{"deviceGid": 999, "chargerOn": False}]
        }
        self.mock_auth.request.return_value = mock_response
        
        chargers = self.vue.get_chargers()
        self.assertEqual(len(chargers), 1)
        self.assertEqual(chargers[0].device_gid, 999)
        self.assertFalse(chargers[0].charger_on)

    def test_update_charger(self):
        charger = ChargerDevice(gid=999, on=False)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deviceGid": 999, "chargerOn": True, "chargingRate": 16}
        self.mock_auth.request.return_value = mock_response
        
        result = self.vue.update_charger(charger, on=True, charge_rate=16)
        self.assertTrue(result.charger_on)
        self.assertEqual(result.charging_rate, 16)

    def test_get_devices_status(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"outlets": [{"deviceGid": 789}], "evChargers": [{"deviceGid": 999}]}'
        mock_response.json.return_value = {
            "outlets": [{"deviceGid": 789}],
            "evChargers": [{"deviceGid": 999}]
        }
        self.mock_auth.request.return_value = mock_response
        
        outlets, chargers = self.vue.get_devices_status()
        self.assertEqual(len(outlets), 1)
        self.assertEqual(len(chargers), 1)
        self.assertEqual(outlets[0].device_gid, 789)
        self.assertEqual(chargers[0].device_gid, 999)

    def test_get_channel_types(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '[{"channelTypeGid": 1, "description": "Main", "selectable": true}]'
        mock_response.json.return_value = [
            {"channelTypeGid": 1, "description": "Main", "selectable": True}
        ]
        self.mock_auth.request.return_value = mock_response
        
        channel_types = self.vue.get_channel_types()
        self.assertEqual(len(channel_types), 1)
        self.assertEqual(channel_types[0].channel_type_gid, 1)
        self.assertEqual(channel_types[0].description, "Main")
        self.assertTrue(channel_types[0].selectable)

    def test_get_vehicles(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '[{"vehicleGid": 111, "make": "Tesla", "model": "Model 3"}]'
        mock_response.json.return_value = [
            {"vehicleGid": 111, "make": "Tesla", "model": "Model 3"}
        ]
        self.mock_auth.request.return_value = mock_response
        
        vehicles = self.vue.get_vehicles()
        self.assertEqual(len(vehicles), 1)
        self.assertEqual(vehicles[0].vehicle_gid, 111)
        self.assertEqual(vehicles[0].make, "Tesla")
        self.assertEqual(vehicles[0].model, "Model 3")

    def test_get_vehicle_status(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"settings": {"vehicleGid": 111, "batteryLevel": 80}}'
        mock_response.json.return_value = {
            "settings": {"vehicleGid": 111, "batteryLevel": 80}
        }
        self.mock_auth.request.return_value = mock_response
        
        status = self.vue.get_vehicle_status(111)
        self.assertIsNotNone(status)
        self.assertEqual(status.vehicle_gid, 111)
        self.assertEqual(status.battery_level, 80)

    @patch('builtins.open', mock_open(read_data='{"id_token": "test_token"}'))
    @patch('json.load')
    @patch('pyemvue.auth.Cognito')  # Mock Cognito to avoid AWS config issues
    def test_login_with_token_file(self, mock_cognito, mock_json_load):
        mock_json_load.return_value = {
            "id_token": "test_token",
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "username": "test@example.com"
        }
        
        # Mock the Cognito instance
        mock_cognito_instance = Mock()
        mock_cognito.return_value = mock_cognito_instance
        
        with patch.object(self.vue, '_store_tokens'), \
             patch.object(self.vue, 'get_customer_details') as mock_get_customer:
            mock_get_customer.return_value = Customer(gid=456, email="test@example.com")
            
            # Mock the Auth class methods directly
            with patch('pyemvue.pyemvue.Auth') as mock_auth_class:
                mock_auth_instance = Mock()
                mock_auth_instance.refresh_tokens.return_value = None
                mock_auth_instance.tokens = {"access_token": "token"}
                mock_auth_instance.get_username.return_value = "test@example.com"
                mock_auth_class.return_value = mock_auth_instance
                
                result = self.vue.login(username="test@example.com", token_storage_file="tokens.json")
                self.assertTrue(result)
                self.assertEqual(self.vue.username, "test@example.com")

    def test_login_simulator(self):
        with patch.object(self.vue, 'get_customer_details') as mock_get_customer:
            mock_get_customer.return_value = Customer(gid=456, email="test@example.com")
            
            result = self.vue.login_simulator("http://localhost:8080", "test@example.com", "password")
            self.assertTrue(result)
            self.assertEqual(self.vue.username, "test@example.com")

    @patch('builtins.open', mock_open())
    @patch('json.dump')
    def test_store_tokens(self, mock_json_dump):
        self.vue.token_storage_file = "tokens.json"
        self.vue.username = "test@example.com"
        tokens = {"access_token": "token", "id_token": "id_token"}
        
        self.vue._store_tokens(tokens)
        mock_json_dump.assert_called_once()


class TestFormatTime(unittest.TestCase):
    def test_format_time_aware_utc(self):
        time = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        result = _format_time(time)
        self.assertEqual(result, "2023-01-01T12:00:00Z")

    def test_format_time_aware_non_utc(self):
        est = datetime.timezone(datetime.timedelta(hours=-5))
        time = datetime.datetime(2023, 1, 1, 7, 0, 0, tzinfo=est)
        result = _format_time(time)
        self.assertEqual(result, "2023-01-01T12:00:00Z")

    def test_format_time_unaware(self):
        time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        result = _format_time(time)
        self.assertEqual(result, "2023-01-01T12:00:00Z")

    def test_get_ev_charging_report_success(self):
        mock_response = Mock()
        mock_response.text = json.dumps({
            "device_id": "C93A7B12DCF947F58E3B76",
            "interval": {
                "start": "2025-08-01T00:00:00Z",
                "end": "2025-09-01T00:00:00Z"
            },
            "report_description": "Test report description",
            "call_to_action_type": None,
            "energy_kwhs": 75.65,
            "charging_cost": 5.39,
            "daily_charging_totals": [
                {
                    "date": "2025-08-01",
                    "energy_kwhs": 34.07,
                    "charging_cost": 2.44,
                    "savings": 2.99,
                    "potential_savings": None
                }
            ],
            "plug_in_sessions": [
                {
                    "interval": {
                        "start": "2025-07-31T21:10:19.493Z",
                        "end": "2025-08-01T13:54:25.457Z"
                    },
                    "charging_sessions": [
                        {
                            "interval": {
                                "start": "2025-08-01T01:00:58.575Z",
                                "end": "2025-08-01T01:28:07.479Z"
                            },
                            "energy_kwhs": 4.27,
                            "charging_cost": 0.31,
                            "savings": 0.85,
                            "potential_savings": None
                        }
                    ]
                }
            ]
        })
        mock_response.raise_for_status.return_value = None
        self.mock_auth.request.return_value = mock_response

        start = datetime.datetime(2025, 8, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2025, 9, 1, tzinfo=datetime.timezone.utc)
        result = self.vue.get_ev_charging_report("C93A7B12DCF947F58E3B76", start, end)

        self.assertIsInstance(result, EvChargingReport)
        self.assertEqual(result.device_id, "C93A7B12DCF947F58E3B76")
        self.assertEqual(result.energy_kwhs, 75.65)
        self.assertEqual(result.charging_cost, 5.39)
        self.assertEqual(len(result.daily_charging_totals), 1)
        self.assertEqual(len(result.plug_in_sessions), 1)
        self.assertEqual(len(result.plug_in_sessions[0].charging_sessions), 1)

    def test_get_ev_charging_report_empty_response(self):
        mock_response = Mock()
        mock_response.text = ""
        mock_response.raise_for_status.return_value = None
        self.mock_auth.request.return_value = mock_response

        start = datetime.datetime(2025, 8, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2025, 9, 1, tzinfo=datetime.timezone.utc)
        result = self.vue.get_ev_charging_report("C93A7B12DCF947F58E3B76", start, end)

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()