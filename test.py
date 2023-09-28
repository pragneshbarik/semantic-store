from semanticstore import KV
import threading
from faker import Faker

fake = Faker()

# Define the number of key-value pairs you want
num_pairs = 100



kv = KV('database', num_dimensions=2)



# kv['foo'] = {'vector' : [1, 2], 'payload' : {'some' : 'data'}}


def thread_function(kv, key, value):
    print(key, value)
    kv[key] = value
    kv.commit()
    result = kv[key]
    print(f"Thread ID {threading.current_thread().ident}: Retrieved value for key '{key}': {result}")



data_to_insert = []
for i in range(100):
    key = fake.word()  # Generate a random word as the key
    value = {
        'vector': [i, i],
        'payload': {
            'some': fake.word(),
            'other_data': fake.sentence()
        }
    }
    data_to_insert.append(value)

# print(data_to_insert)

if __name__ == "__main__":
    num_threads = 100  # Number of threads to run concurrently
    # kv = KV('database', num_dimensions=2)

    threads = []


    # Create and start the threads
    for i in range(num_threads):
        thread = threading.Thread(target=thread_function, args=(kv, f'key_{i}', data_to_insert[i % len(data_to_insert)]))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

for res in kv[[1, 1]][5] :
    print(res)