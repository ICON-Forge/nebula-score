from iconservice import *

class IRC31Basic(ABC):
    """ An interface for ICON Token Standard IRC-31 """

    @abstractmethod
    def balanceOf(self, _owner: Address, _id: int) -> int:
        pass

    @abstractmethod
    def balanceOfBatch(self, _owners: List[Address], _ids: List[int]) -> List[int]:
        pass

    @abstractmethod
    def tokenURI(self, _id: int) -> str:
        pass

    @abstractmethod
    def transferFrom(self, _from: Address, _to: Address, _id: int, _value: int, _data: bytes = None):
        pass

    @abstractmethod
    def transferFromBatch(self, _from: Address, _to: Address, _ids: List[int], _values: List[int], _data: bytes = None):
        pass

    @abstractmethod
    def setApprovalForAll(self, _operator: Address, _approved: bool):
        pass

    @abstractmethod
    def isApprovedForAll(self, _owner: Address, _operator: Address) -> bool:
        pass


class IRC31MintBurn(ABC):
    """ Optional Metadata extension for IRC-3 """

    @abstractmethod
    def mint(self, _id: int, _supply: int, _uri: str):
        pass

    @abstractmethod
    def burn(self, _id: int, _amount: int):
        pass

    @abstractmethod
    def setTokenURI(self, _id: int, _uri: str):
        pass
