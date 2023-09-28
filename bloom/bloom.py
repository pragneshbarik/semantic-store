import mmh3
import math
import pickle
from bitarray import bitarray
class Bloom:
  
    '''
    Class for Bloom filter, using murmur3 hash function
    '''

    def __init__(self):
        '''
        items_count : int
            Number of items expected to be stored in bloom filter
        fp_prob : float
            False Positive probability in decimal
        '''
        self.fp_prob = 0.01
        self.items_count = 1_000_000
  
        self.size = self.get_size(self.items_count, self.fp_prob)
  
        self.hash_count = self.get_hash_count(self.size, self.items_count)
  
        self.bit_array = bitarray(self.size)
  
        self.bit_array.setall(0)
  
    def add(self, item):
        '''
        Add an item in the filter
        '''
        digests = []
        for i in range(self.hash_count):
            digest = mmh3.hash(str(item), i) % self.size
            digests.append(digest)
  
            self.bit_array[digest] = True
  
    def check(self, item):
        '''
        Check for existence of an item in filter
        '''
        for i in range(self.hash_count):
            digest = mmh3.hash(str(item), i) % self.size
            if self.bit_array[digest] == False:
  
                return False
        return True
    
    def __contains__(self, item) :
        return self.check(item)
  
    @classmethod
    def get_size(self, n, p):
        '''
        Return the size of bit array(m) to used using
        following formula
        m = -(n * lg(p)) / (lg(2)^2)
        n : int
            number of items expected to be stored in filter
        p : float
            False Positive probability in decimal
        '''
        m = -(n * math.log(p))/(math.log(2)**2)
        return int(m)
  
    @classmethod
    def get_hash_count(self, m, n):
        '''
        Return the hash function(k) to be used using
        following formula
        k = (m/n) * lg(2)
  
        m : int
            size of bit array
        n : int
            number of items expected to be stored in filter
        '''
        k = (m/n) * math.log(2)
        return int(k)
    
    def complement(self, array: list) :
        """
        Mask elements in the input list that are not present in the Bloom filter.

        This method takes a list of elements and checks each element's presence
        in the Bloom filter. Elements that are not found in the Bloom filter
        are included in the result list.

        Parameters:
        array (list): The list of elements to be filtered.

        Returns:
        list: A list containing elements from the input list that are not present
            in the Bloom filter.
        """
        res = []
        for x in array :
            if x not in self :
                res.append(x)
        return res

    
    def write_bloom(self, filename):
        """
        Serialize and write the Bloom filter to a file on disk.
        
        Parameters:
        filename (str): The name of the file to write to.
        """
        data = {
            "fp_prob": self.fp_prob,
            "size": self.size,
            "hash_count": self.hash_count,
            "bit_array": self.bit_array
        }
        with open(filename, 'wb') as file:
            pickle.dump(data, file)


    @classmethod
    def read_bloom(cls, filename):
        """
        Read and deserialize a Bloom filter from a file on disk.

        Parameters:
        filename (str): The name of the file to read from.

        Returns:
        BloomMask: An instance of BloomMask initialized with the data from the file.
        """
        with open(filename, 'rb') as file:
            data = pickle.load(file)

        bloom_filter = cls.__new__(cls)  # Create an instance without calling __init__
        bloom_filter.fp_prob = data["fp_prob"]
        bloom_filter.size = data["size"]
        bloom_filter.hash_count = data["hash_count"]
        bloom_filter.bit_array = data["bit_array"]

        return bloom_filter
