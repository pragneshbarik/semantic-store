import numpy as np
import json

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