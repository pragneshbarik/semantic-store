from abc import ABC, abstractmethod

class Pipeline(ABC):

    @abstractmethod
    def insert_file(self) -> int:
        pass

    @abstractmethod
    def commit(self) -> int :
        pass
    
    


    # @abstractmethod
    # def similarity_search(self, query: str, k: int) -> list[int] :
    #     pass

    # @abstractmethod
    # def search_via_text(self) :
    #     pass
    
    # @abstractmethod
    # def search_via_image(self) :
    #     pass

    # @abstractmethod 
    # def search_via_audio(self) :
    #     pass

    # @abstractmethod
    # def search_via_video(self) :
    #     pass


    @staticmethod
    def order_by(records, order):
        print(len(records), len(order))
        # if not all(0 <= i < len(records) for i in order) or len(set(order)) != len(order):
        #     raise ValueError("Invalid order list")

        record_dict = {record[0]: record for record in records}

        ordered_records = [record_dict[i] for i in order]

        return ordered_records


