import unittest
import datetime

from pyemvue.customer import Customer


class TestCustomer(unittest.TestCase):
    def test_init_defaults(self):
        customer = Customer()
        
        self.assertEqual(customer.customer_gid, 0)
        self.assertEqual(customer.email, "")
        self.assertEqual(customer.first_name, "")
        self.assertEqual(customer.last_name, "")
        self.assertEqual(customer.created_at, datetime.datetime(1970, 1, 1))

    def test_init_with_parameters(self):
        created_date = datetime.datetime(2020, 5, 15, 10, 30, 0)
        customer = Customer(
            gid=123,
            email="test@example.com",
            firstName="John",
            lastName="Doe",
            createdAt=created_date
        )
        
        self.assertEqual(customer.customer_gid, 123)
        self.assertEqual(customer.email, "test@example.com")
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.last_name, "Doe")
        self.assertEqual(customer.created_at, created_date)

    def test_from_json_dictionary_full(self):
        json_data = {
            "customerGid": 456,
            "email": "jane@example.com",
            "firstName": "Jane",
            "lastName": "Smith",
            "createdAt": "2021-03-20T14:22:00Z"
        }
        
        customer = Customer().from_json_dictionary(json_data)
        
        self.assertEqual(customer.customer_gid, 456)
        self.assertEqual(customer.email, "jane@example.com")
        self.assertEqual(customer.first_name, "Jane")
        self.assertEqual(customer.last_name, "Smith")
        self.assertEqual(customer.created_at, "2021-03-20T14:22:00Z")

    def test_from_json_dictionary_partial(self):
        json_data = {
            "customerGid": 789,
            "email": "partial@example.com"
        }
        
        customer = Customer()
        original_first_name = customer.first_name
        original_last_name = customer.last_name
        original_created_at = customer.created_at
        
        result = customer.from_json_dictionary(json_data)
        
        self.assertEqual(customer.customer_gid, 789)
        self.assertEqual(customer.email, "partial@example.com")
        self.assertEqual(customer.first_name, original_first_name)
        self.assertEqual(customer.last_name, original_last_name)
        self.assertEqual(customer.created_at, original_created_at)
        self.assertEqual(result, customer)

    def test_from_json_dictionary_empty(self):
        json_data = {}
        
        customer = Customer(
            gid=999,
            email="existing@example.com",
            firstName="Existing",
            lastName="User",
            createdAt=datetime.datetime(2019, 1, 1)
        )
        
        result = customer.from_json_dictionary(json_data)
        
        # Values should remain unchanged
        self.assertEqual(customer.customer_gid, 999)
        self.assertEqual(customer.email, "existing@example.com")
        self.assertEqual(customer.first_name, "Existing")
        self.assertEqual(customer.last_name, "User")
        self.assertEqual(customer.created_at, datetime.datetime(2019, 1, 1))
        self.assertEqual(result, customer)

    def test_from_json_dictionary_returns_self(self):
        json_data = {"customerGid": 111}
        customer = Customer()
        
        result = customer.from_json_dictionary(json_data)
        
        self.assertIs(result, customer)

    def test_from_json_dictionary_with_none_values(self):
        json_data = {
            "customerGid": None,
            "email": None,
            "firstName": "ValidName",
            "lastName": None,
            "createdAt": None
        }
        
        customer = Customer()
        customer.from_json_dictionary(json_data)
        
        # None values will overwrite existing defaults in the actual implementation
        self.assertIsNone(customer.customer_gid)
        self.assertIsNone(customer.email)
        self.assertEqual(customer.first_name, "ValidName")
        self.assertIsNone(customer.last_name)
        self.assertIsNone(customer.created_at)


if __name__ == '__main__':
    unittest.main()