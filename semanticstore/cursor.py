from semanticstore.utils import *
from jmespath import search
from collections.abc import Iterable

class Cursor :
    """
    Represents a cursor for navigating and filtering results from various data structures.

    The `Cursor` class is designed to work with a wide range of data structures, including dictionaries,
    lists, and other iterable objects. It provides methods for navigation, filtering, and retrieval of data.

    Parameters:
    res (object): The initial result or data structure to be used with the cursor.

    Attributes:
    res (object): The result or data structure currently associated with the cursor.
    is_scriptable (bool): Indicates whether the result is scriptable (supports indexing).
    is_iterable (bool): Indicates whether the result is iterable.

    Methods:
    __getitem__(key): Retrieve an item or slice from the result.
    __next__(): Iterate over the elements of the result.
    filter(jmespath_query): Filter the result using a JMESPath query.
    __repr__(): Return a string representation of the result.
    fetch(): Retrieve the current result.

    Example:
    >>> data = {
    ...     "name": "John",
    ...     "age": 30,
    ...     "friends": ["Alice", "Bob"]
    ... }
    >>> cursor = Cursor(data)
    >>> # Access a specific field using indexing
    >>> name = cursor["name"].fetch()  # Retrieves "John"
    >>> # Iterate over the elements in a list
    >>> friends = cursor["friends"]
    >>> for friend in friends:
    ...     print(friend.fetch())
    ...
    "Alice"
    "Bob"
    >>> # Filter data using a JMESPath query
    >>> filtered_data = cursor.filter("friends[0]")  # Retrieves "Alice"
    >>> print(filtered_data.fetch())
    """
    def __init__(self, res) :
        self.__result = res
        self.__is_scriptable = hasattr(res, '__getitem__')
        self.__is_iterable = isinstance(res, Iterable)
        self.__index = 0
    
    def __getitem__(self, key) :
        if self.__is_scriptable :
            return Cursor(self.__result[key])
        else:
            raise TypeError(f"'{type(self.__result).__name__}' object is not subscriptable")

    def __next__(self) :
        if self.__is_iterable and self.__index < len(self.__result):
            item = self.__result[self.__index]
            self.__index += 1
            return Cursor(item)
        else:
            raise StopIteration

    def filter(self, jmespath_query: str) :
        """
        Filter the result using a JMESPath query.

        This method filters the result using a JMESPath query and returns a new cursor to the filtered data.

        Parameters:
        jmespath_query (str): The JMESPath query used for filtering.

        Returns:
        Cursor: A cursor to the filtered data.
        """

        filtered_res = search(jmespath_query, self.__result)
        return Cursor(filtered_res)
    
    def __repr__(self) -> str:
        return str(self.__result)

    def fetch(self) :
        """
        Retrieve the current result.

        Returns:
        object: The current result.
        """
        return self.__result
     
