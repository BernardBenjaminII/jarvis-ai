from abc import ABC
from abc import abstractmethod


class BaseExtractor(ABC):

    @abstractmethod
    def supports(self, path):

        pass

    @abstractmethod
    def extract(self, path):

        pass
