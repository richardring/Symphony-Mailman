from abc import ABC, abstractmethod


class Cache(ABC):
    @abstractmethod
    def __init__(self, cache_config):
        pass

    @abstractmethod
    def Get_Connection(self):
        pass

    @abstractmethod
    def Get_Id(self, email_address: str) -> str:
        pass

    @abstractmethod
    def Delete_Id(self, id: str):
        pass

    @abstractmethod
    def Insert_Id(self, email_address: str, symphony_id: str, pod_id: str, pretty_name: str=''):
        pass

    @abstractmethod
    def Clear_All(self):
        pass
