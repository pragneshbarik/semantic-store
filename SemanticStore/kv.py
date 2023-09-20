import sqlite3
import faiss
import json
import numpy as np

def remove_neg_indexes(D: np.ndarray, I: np.ndarray):
    D = np.array(D)
    I = np.array(I)
    D = D[I >= 0]
    I = I[I >= 0]
    return list(D), list(I)


def order_by(records, order):
    record_dict = {record[0]: record for record in records}
    ordered_records = [record_dict[i] for i in order]
    return ordered_records


def filter_deleted_ids(D, I, deleted_ids) :
    filtered_D = []
    filtered_I = []

    for i, faiss_id in enumerate(I):
        if faiss_id not in deleted_ids :
            filtered_I.append(faiss_id)
            filtered_D.append(D[i])

    return filtered_D, filtered_I


def expected_projection(records, distances) :
    result_list = []
    for record, distance in zip(records, distances):
        _, key, value_json = record
        value_dict = json.loads(value_json)
        result_dict = {"key": key, "value": value_dict, "distance": distance}
        result_list.append(result_dict)
    
    return result_list

def fetch_deleted_ids(db):
        cursor = db.cursor()
        cursor.execute('SELECT faiss_id FROM deleted_faiss_ids')
        result = cursor.fetchall()
        deleted_ids = set([row[0] for row in result])
        return deleted_ids

class ClosureObject :
    def __init__(self, db, faiss_index, vector) :
        self.__db = db
        self.__index = faiss_index
        self.vector = vector
        self.__deleted_ids = self.__fetch_deleted_ids()

    def __fetch_deleted_ids(self):
        cursor = self.__db.cursor()
        cursor.execute('SELECT faiss_id FROM deleted_faiss_ids')
        result = cursor.fetchall()
        deleted_ids = set([row[0] for row in result])
        return deleted_ids

    def __search_by_vector(self, k):
        vector = [self.vector]
        deleted_ids = self.__fetch_deleted_ids()
        if self.__index is not None:
            query_vector = np.array(vector)
            D, I = self.__index.search(query_vector, k= k + len(deleted_ids))

    
            filtered_D, filtered_I = filter_deleted_ids(D[0], I[0], self.__fetch_deleted_ids())
            filtered_D, filtered_I = remove_neg_indexes(filtered_D, filtered_I)

            return self.__get_item_by_faiss_ids(filtered_I, filtered_D)
            

    def __get_item_by_faiss_ids(self, faiss_ids, distances) :
        cursor = self.__db.cursor()
        q = f'''SELECT faiss_id, key, value FROM kv_store WHERE faiss_id IN ({', '.join(map(str, faiss_ids))})'''
        result = cursor.execute(q).fetchall()

        return expected_projection(order_by(result, faiss_ids), distances)

    def __getitem__(self, k) :
        if isinstance(k, slice) :
            start, stop, _ = k.start, k.stop, k.step
            res = self.__search_by_vector(stop)
            return res[start:stop]
        return self.__search_by_vector(k)

class KV:
    def __init__(self, connection, num_dimensions=128):
        self.__db = sqlite3.connect(connection+".db")
        self.__index_file = connection + ".faiss"
        self.__num_dimensions = num_dimensions
        self.__index = None
        self.__create_table()
        self.__load_index()

    def __fetch_deleted_ids(self):
        cursor = self.__db.cursor()
        cursor.execute('SELECT faiss_id FROM deleted_faiss_ids')
        result = cursor.fetchall()
        deleted_ids = set([row[0] for row in result])
        return deleted_ids
    
    def __create_table(self):
        cursor = self.__db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS kv_store
                          (key TEXT PRIMARY KEY, faiss_id INTEGER, value TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS deleted_faiss_ids (faiss_id INTEGER)''')
        self.__db.commit()

    def __load_index(self):
        if self.__index is None:
            try:
                self.__index = faiss.read_index(self.__index_file)
            except Exception as e:
                self.__index = faiss.IndexFlatL2(self.__num_dimensions) 
                faiss.write_index(self.__index, self.__index_file)

    def close(self):
        self.__save_index()
        self.__db.close()

    def __get_item_by_faiss_ids(self, faiss_ids, distances) :
        cursor = self.__db.cursor()
        q = f'''SELECT faiss_id, key, value FROM kv_store WHERE faiss_id IN ({', '.join(map(str, faiss_ids))})'''
        result = cursor.execute(q).fetchall()

        return expected_projection(order_by(result, faiss_ids), distances)
    

    def __getitem__(self, key):
        if isinstance(key, slice) and isinstance(key.start, (list, np.ndarray)) and isinstance(key.stop, (int, float)) :
            _, D, I = self.__index.range_search(np.array([key.start]), key.stop ** 2)
            
            filtered_D, filtered_I = filter_deleted_ids(D, I, self.__fetch_deleted_ids())
            filtered_D, filtered_I = remove_neg_indexes(filtered_D, filtered_I)

            return self.__get_item_by_faiss_ids(filtered_I, filtered_D)

        elif isinstance(key, slice) and isinstance(key.start, (list, np.ndarray)) and isinstance(key.stop, (list, np.ndarray)) :
            r = np.linalg.norm(np.array(key.start)  - np.array(key.stop), ord=2) ** 2
            _, D, I = self.__index.range_search(np.array([key.start]), r)
            filtered_D, filtered_I = filter_deleted_ids(D, I, self.__fetch_deleted_ids())
            filtered_D, filtered_I = remove_neg_indexes(filtered_D, filtered_I)

            return self.__get_item_by_faiss_ids(filtered_I, filtered_D)

        elif isinstance(key, (str, int)):
            return self.__get_item_by_key(key)
        elif isinstance(key, list):
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
    
        cursor = self.__db.cursor()
        
        if isinstance(value, dict) and "vector" in value and "metadata" in value:
            vector = value["vector"]
            metadata = value["metadata"]
            

            if isinstance(vector, (list, np.ndarray)):
                data = {
                    "vector": vector,
                    "metadata": metadata
                }
                
                if self.find(key) :
                    self.remove(key) 
              
                data_json = json.dumps(data)
                faiss_id = self.__index.ntotal
                
                cursor.execute('INSERT OR REPLACE INTO kv_store (key, faiss_id, value) VALUES (?, ?, ?)', (key, faiss_id, data_json))
                
                # Update the Faiss index
                if self.__index is not None:
                    self.__index.add(np.array([vector]))
            else:
                raise ValueError("Value must have a valid 'vector' field that is a list or NumPy array.")
        else:
            raise ValueError("Value must be a dictionary with 'vector' and 'metadata' fields.")


    def remove(self, key):
        cursor = self.__db.cursor()

        q = f'SELECT faiss_id FROM kv_store WHERE key = ?'
        cursor.execute(q, (key,))
        result = cursor.fetchone()

        if result is not None:
            faiss_id = result[0]

            q = f'INSERT INTO deleted_faiss_ids (faiss_id) VALUES (?)'
            cursor.execute(q, (faiss_id,))
        else:
            raise KeyError(f"Key '{key}' not found")

    def put(self, key, value) :
        self[key] = value

    def get(self, key) :
        return self[key]

    def find(self, key):
        cursor = self.__db.cursor()
        cursor.execute('SELECT 1 FROM kv_store WHERE key = ? LIMIT 1', (key,))
        result = cursor.fetchone()
        return result is not None

    def commit(self) :
        self.__db.commit()
        faiss.write_index(self.__index, self.__index_file)

    def close(self):
        self.__db.close()
        faiss.write_index(self.__index, self.__index_file)
