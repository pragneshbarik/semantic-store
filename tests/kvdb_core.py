import unittest
from semanticstore import KV

class TestYourKeyValueStore(unittest.TestCase):

    def setUp(self):
        self.kv_store = KV('test_database', num_dimensions=3)

    def tearDown(self):
        self.kv_store.close(False)

    def assertFloatListsAlmostEqual(self, list1, list2, places=7):
        """
        Custom assertion method to compare lists of floating-point values with a specified number of decimal places.
        """
        for a, b in zip(list1, list2):
            self.assertAlmostEqual(a, b, places=places)

    def test_setitem_valid_data(self):
        data = {
            "vector": [0.1, 0.2, 0.3],
            "payload": "Some payload data"
        }
        self.kv_store["my_key"] = data
        retrieved_data = self.kv_store["my_key"]
        
        self.assertFloatListsAlmostEqual(retrieved_data["vector"], data["vector"])
        self.assertEqual(retrieved_data["payload"], data["payload"])


    def test_setitem_existing_key(self):
        data1 = {
            "vector": [0.1, 0.2, 0.3],
            "payload": "Payload 1"
        }
        data2 = {
            "vector": [0.4, 0.5, 0.6],
            "payload": "Payload 2"
        }

        self.kv_store["existing_key"] = data1
        self.kv_store["existing_key"] = data2

        retrieved_data = self.kv_store["existing_key"]

        self.assertFloatListsAlmostEqual(retrieved_data["vector"], data2["vector"])
        self.assertEqual(retrieved_data["payload"], data2["payload"])

    def test_setitem_invalid_data(self):
        invalid_data = {
            "invalid_field": [0.1, 0.2, 0.3],
            "payload": "Some payload data"
        }

        with self.assertRaises(ValueError):
            self.kv_store["invalid_key"] = invalid_data

    def test_setitem_invalid_vector_type(self):
        invalid_data = {
            "vector": "invalid_vector",
            "payload": "Some payload data"
        }

        with self.assertRaises(ValueError):
            self.kv_store["invalid_key"] = invalid_data
    
    def test_remove_existing_key(self):
        key = "existing_key"
        data = {
            "vector": [0.1, 0.2, 0.3],
            "payload": "Some payload data"
        }
        self.kv_store[key] = data

        self.kv_store.remove(key)

        with self.assertRaises(KeyError):
            retrieved_data = self.kv_store[key]
    
    def test_remove_nonexistent_key(self):
        key = "nonexistent_key"

        with self.assertRaises(KeyError):
            self.kv_store.remove(key)

if __name__ == '__main__':
    unittest.main()
