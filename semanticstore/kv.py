from semanticstore.closure import ClosureObject
from semanticstore.utils import *
from bloom.bloom import Bloom
from threading import Lock
import numpy as np
import sqlite3
import faiss
import json


class KV:
    def _load_bloom(self) :
        if self.__bloom_filter is None:
            try:
                self.__bloom_filter = Bloom.read_mask(self.__bloom_filter_file)
            except Exception as e:
                self.__bloom_filter = Bloom()
                self.__bloom_filter.write_bloom(self.__bloom_filter_file)
        
    def __init__(self, connection, num_dimensions=128):
        self.__db = sqlite3.connect(connection+".db", check_same_thread=False)
        self.__index_file = connection + ".faiss"
        self.__bloom_filter_file = connection + ".bloom"
        self.__num_dimensions = num_dimensions
        self.__index = None
        self.__bloom_filter = None
        self._create_table()
        self._load_index()
        self._load_bloom()
        self._mutex = Lock()
    
    def __fetch_deleted_ids(self):
        cursor = self.__db.cursor()
        cursor.execute('SELECT faiss_id FROM deleted_faiss_ids')
        result = cursor.fetchall()
        deleted_ids = set([row[0] for row in result])
        return deleted_ids
    
    def _create_table(self):
        cursor = self.__db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS kv_store
                          (key TEXT PRIMARY KEY, faiss_id INTEGER, value TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS deleted_faiss_ids (faiss_id INTEGER)''')
        self.__db.commit()

    def _load_index(self):
        if self.__index is None:
            try:
                self.__index = faiss.read_index(self.__index_file)
            except Exception as e:
                self.__index = faiss.IndexFlatL2(self.__num_dimensions) 
                faiss.write_index(self.__index, self.__index_file)

    def close(self, save = True):
        if save :
            self.commit()
        self.__db.close()

    def __get_item_by_faiss_ids(self, faiss_ids, distances) :
        cursor = self.__db.cursor()
        q = f'''SELECT faiss_id, key, value FROM kv_store WHERE faiss_id IN ({', '.join(map(str, faiss_ids))})'''
        result = cursor.execute(q).fetchall()

        return expected_projection(order_by(result, faiss_ids), distances)
    

    def __getitem__(self, key):
        if isinstance(key, slice) and isinstance(key.start, (list, np.ndarray)) and isinstance(key.stop, (int, float)) :
            _, D, I = self.__index.range_search(np.array([key.start]), key.stop ** 2)
            
            filtered_D, filtered_I = filter_deleted_ids(D, I, self.__bloom_filter)
            filtered_D, filtered_I = remove_neg_indexes(filtered_D, filtered_I)

            return self.__get_item_by_faiss_ids(filtered_I, filtered_D)

        elif isinstance(key, slice) and isinstance(key.start, (list, np.ndarray)) and isinstance(key.stop, (list, np.ndarray)) :
            r = np.linalg.norm(np.array(key.start)  - np.array(key.stop), ord=2) ** 2
            _, D, I = self.__index.range_search(np.array([key.start]), r)
            
            filtered_D, filtered_I = filter_deleted_ids(D, I, self.__bloom_filter)
            filtered_D, filtered_I = remove_neg_indexes(filtered_D, filtered_I)

            return self.__get_item_by_faiss_ids(filtered_I, filtered_D)

        elif isinstance(key, (str, int)):
            return self.__get_item_by_key(key)
        elif isinstance(key, (np.ndarray, list)):
            return self.__search_by_vector(key)
        else:
            raise ValueError("Key must be a string, int, or list.")
        
    def __get_item_by_key(self, key):
        cursor = self.__db.cursor()
        cursor.execute('SELECT value FROM kv_store WHERE key = ?', (key,))
        result = cursor.fetchone()
        if result is not None:
            value_json = result[0]
            value_dict = json.loads(value_json) 
            return value_dict
        else:
            raise KeyError(f"Key '{key}' not found")
    
    def __search_by_vector(self, vector):
        intermediate_result = ClosureObject(self.__db, self.__index, vector)
        return intermediate_result

    def __setitem__(self, key, value):
        """
        Set the value associated with the given key in the key-value store, allowing storage of vectors and payloads.

        This method allows you to associate a key with a dictionary containing a 'vector' and 'payload'. The 'vector' should
        be a list or NumPy array containing floating-point values, while 'payload' can be any arbitrary data.

        If a key already exists in the store, its previous entry will be replaced with the new data.

        Parameters:
        key (str): The key under which the data will be stored.
        value (dict): A dictionary containing 'vector' and 'payload' fields.
                    - 'vector': A list or NumPy array of floating-point values representing a vector.
                    - 'payload': Arbitrary data associated with the vector.

        Raises:
        ValueError: If the provided 'value' dictionary does not have the required 'vector' and 'payload' fields,
                    or if the 'vector' field is not a list or NumPy array.

        Example:
        >>> kv_store = YourKeyValueStore()
        >>> data = {
        ...     "vector": [0.1, 0.2, 0.3],
        ...     "payload": "Some payload data"
        ... }
        >>> kv_store["my_key"] = data
        """
        
        cursor = self.__db.cursor()
        
        if isinstance(value, dict) and "vector" in value and "payload" in value:
            vector = np.array(value["vector"]).astype('float32')
            payload = value["payload"]    

            if isinstance(vector, (list, np.ndarray)):
                data = {
                    "vector": list(vector.astype('float64')),
                    "payload": payload
                }
                if self.find(key) :
                    self.remove(key) 
              
                data_json = json.dumps(data)
                
                with self._mutex:
                    faiss_id = self.__index.ntotal
                    cursor.execute('INSERT OR REPLACE INTO kv_store (key, faiss_id, value) VALUES (?, ?, ?)', (key, faiss_id, data_json))
                    self.__index.add(vector.reshape(1, -1))
            else:
                raise ValueError("Value must have a valid 'vector' field that is a list or NumPy array.")
        else:
            raise ValueError("Value must be a dictionary with 'vector' and 'payload' fields.")

    def __contains__(self, key) :
        return self.find(key)
    
    def __delete__(self, key) :
        self.remove(key)

    def remove(self, key):
        cursor = self.__db.cursor()

        q = f'SELECT faiss_id FROM kv_store WHERE key = ?'
        cursor.execute(q, (key,))
        result = cursor.fetchone()

        if result is not None:
            faiss_id = result[0]
            with self._mutex :
                cursor.execute("INSERT INTO deleted_faiss_ids (faiss_id) VALUES (?)", (faiss_id,))
                cursor.execute("DELETE FROM kv_store WHERE key = ?", (key,))
                self.__bloom_filter.add(faiss_id)
        else:
            raise KeyError(f"Key '{key}' not found")

    def put(self, key, value) :
        """
        Set the value associated with the given key in the key-value store, allowing storage of vectors and payloads.

        This method allows you to associate a key with a dictionary containing a 'vector' and 'payload'. The 'vector' should
        be a list or NumPy array containing floating-point values, while 'payload' can be any arbitrary data.

        If a key already exists in the store, its previous entry will be replaced with the new data.

        Parameters:
        key (str): The key under which the data will be stored.
        value (dict): A dictionary containing 'vector' and 'payload' fields.
                    - 'vector': A list or NumPy array of floating-point values representing a vector.
                    - 'payload': Arbitrary data associated with the vector.

        Raises:
        ValueError: If the provided 'value' dictionary does not have the required 'vector' and 'payload' fields,
                    or if the 'vector' field is not a list or NumPy array.

        Example:
        >>> kv_store = YourKeyValueStore()
        >>> data = {
        ...     "vector": [0.1, 0.2, 0.3],
        ...     "payload": "Some payload data"
        ... }
        >>> kv_store["my_key"] = data
        """
        self[key] = value

    def insert(self, keys, vectors, payloads) :
        """
        Only try to insert unique keys, will fail if finds already present keys.
        """
        raise NotImplementedError("Implementation Left")


    def get(self, key) :
        return self[key]
    

    def search(self, query, top_k) :
        """
        Search for items in the key-value store similar to the provided query vector.

        This method performs a search in the key-value store based on the similarity of the provided query vector.
        It returns a cursor to the top-k matching items.

        Parameters:
        query (List[float], np.ndarray): The query vector used to search for similar items.
                                    - If 'query' is a list of floats, it represents the vector for the search query.

        top_k (int): The number of top matching items to retrieve.

        Returns:
        Cursor: A cursor to the top-k matching items.
        """
        return self[query][top_k]

    def find(self, key):
        """
        Check if a key exists in the key-value store.

        This method checks whether a given key exists in the key-value store's database. It performs a database query to
        determine the presence of the key and returns `True` if the key exists, or `False` if it does not.

        Parameters:
        key (str): The key to check for existence in the key-value store.

        Returns:
        bool: `True` if the key exists in the key-value store, `False` otherwise.
        """

        cursor = self.__db.cursor()
        cursor.execute('SELECT 1 FROM kv_store WHERE key = ? LIMIT 1', (key,))
        result = cursor.fetchone()
        return result is not None

    def commit(self) :
        """
        Commit changes to the key-value store.

        This method commits any pending changes, including database modifications, Faiss index updates, and Bloom filter
        updates, to ensure that they are permanently saved.

        Example:
        >>> kv_store = YourKeyValueStore()
        >>> kv_store["key1"] = {"vector": [0.1, 0.2, 0.3], "payload": "Data 1"}
        >>> kv_store.commit()  # Commit the changes to persist them in the store.
        """
        self.__db.commit()
        faiss.write_index(self.__index, self.__index_file)
        self.__bloom_filter.write_bloom(self.__bloom_filter_file)

  