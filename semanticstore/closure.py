from semanticstore.utils import *
from semanticstore.cursor import Cursor

class ClosureObject :
    """
    Represents an object for performing similarity-based searches on a key-value store using a query vector.

    This class allows you to search for items in a key-value store based on the similarity of a provided query vector.
    It interfaces with a database and Faiss index for efficient retrieval of matching items.

    Parameters:
    db: A SQLite database connection.
    faiss_index: A Faiss index used for vector similarity searches.
    vector (list): The query vector used for similarity searches.

    Attributes:
    vector (list): The query vector used for similarity searches.

    Methods:
    search(query, top_k): Search for items similar to the provided query vector and retrieve the top-k matches.

    """
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
            D, I = self.__index.search(query_vector, k + len(deleted_ids))

    
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
            return Cursor(res[start:stop])
        return Cursor(self.__search_by_vector(k))
