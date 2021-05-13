from iconservice import *

class IRC3(ABC):
    """ An interface for ICON Token Standard IRC-3 """
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def symbol(self) -> str:
        pass

    @abstractmethod
    def balanceOf(self, _owner: Address) -> int:
        pass

    @abstractmethod
    def ownerOf(self, _tokenId: int) -> Address:
        pass

    @abstractmethod
    def getApproved(self, _tokenId: int) -> Address:
        pass

    @abstractmethod
    def approve(self, _to: Address, _tokenId: int):
        pass

    @abstractmethod
    def transfer(self, _to: Address, _tokenId: int):
        pass

    @abstractmethod
    def transferFrom(self, _from: Address, _to: Address, _tokenId: int):
        pass


class IRC3Metadata(ABC):
    """ Optional Metadata extension for IRC-3 """
    @abstractmethod
    def tokenURI(self, _tokenId: int) -> str:
        pass


class IRC3Enumerable(ABC):
    """ Optional Enumerable extension for IRC-3 """
    @abstractmethod
    def totalSupply(self) -> int:
        pass

    @abstractmethod
    def tokenByIndex(self, _index: int) -> int:
        pass

    @abstractmethod
    def tokenOfOwnerByIndex(self, _owner: Address, _index: int) -> int:
        pass
