from abc import ABC, abstractmethod

class Pipeline(ABC):

    @abstractmethod
    def insert_file(self) -> int:
        pass

    @abstractmethod
    def commit(self) -> int :
        pass
    
    
    def delete(self, uuid:str) :
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



    


