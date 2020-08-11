from iconservice import *

TAG = 'NebulaPlanetToken'

class IRC3(ABC):
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
    @abstractmethod
    def tokenURI(self, _tokenId: int) -> str:
        pass


class IRC3Enumerable(ABC):
    @abstractmethod
    def totalSupply(self) -> int:
        pass

    @abstractmethod
    def tokenByIndex(self, _index: int) -> int:
        pass

    @abstractmethod
    def tokenOfOwnerByIndex(self, _owner: Address, _index: int) -> int:
        pass


class NebulaPlanetToken(IconScoreBase, IRC3, IRC3Metadata, IRC3Enumerable):
    _OWNED_TOKEN_COUNT = 'owned_token_count'  # Track token count against token owners
    _TOKEN_OWNER = 'token_owner'  # Track token owner against token ID
    _TOKEN_APPROVALS = 'token_approvals'  # Track token approved owner against token ID
    _TOKEN_URIS = 'token_URIs'  # Track token URIs against token ID
    _OWNED_TOKENS = 'owned_tokens'  # Track tokens against token owners
    _TOTAL_SUPPLY = 'total_supply'  # Tracks total number of valid tokens (excluding ones with zero address)

    _ZERO_ADDRESS = Address.from_prefix_and_int(AddressPrefix.EOA, 0)

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._ownedTokenCount = DictDB(self._OWNED_TOKEN_COUNT, db, value_type=int)
        self._tokenOwner = DictDB(self._TOKEN_OWNER, db, value_type=Address)
        self._tokenApprovals = DictDB(self._TOKEN_APPROVALS, db, value_type=Address)
        self._tokenURIs = DictDB(self._TOKEN_URIS, db, value_type=str)
        self._totalSupply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)

        self._db = db

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "NebulaPlanetToken"

    @external(readonly=True)
    def symbol(self) -> str:
        return "NPT"

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        """
        Returns the number of NFTs owned by _owner.
        NFTs assigned to the zero address are considered invalid,
        so this function SHOULD throw for queries about the zero address.
        """
        if _owner is None or self._is_zero_address(_owner):
            revert("Invalid owner")
        return self._ownedTokenCount[_owner]

    @external(readonly=True)
    def ownerOf(self, _tokenId: int) -> Address:
        """
        Returns the owner of an NFT. Throws if _tokenId is not a valid NFT.
        """
        self._ensure_positive(_tokenId)
        owner = self._tokenOwner[_tokenId]
        if owner is None:
            revert("Invalid _tokenId. NFT is not minted")
        if self._is_zero_address(owner):
            revert("Invalid _tokenId. NFT is burned")

        return owner

    @external(readonly=True)
    def getApproved(self, _tokenId: int) -> Address:
        """
        Returns the approved address for a single NFT.
        If there is none, returns the zero address.
        Throws if _tokenId is not a valid NFT.
        """
        self.ownerOf(_tokenId)  # ensure valid token
        addr = self._tokenApprovals[_tokenId]
        if addr is None:
            return self._ZERO_ADDRESS
        return addr

    @external
    def approve(self, _to: Address, _tokenId: int):
        """
        Allows _to to change the ownership of _tokenId from your account.
        The zero address indicates there is no approved address.
        Throws unless self.msg.sender is the current NFT owner.
        """
        owner = self.ownerOf(_tokenId)
        if _to == owner:
            revert("Can't approve to yourself.")
        if self.msg.sender != owner:
            revert("You do not own this NFT")

        self._tokenApprovals[_tokenId] = _to
        self.Approval(owner, _to, _tokenId)

    @external
    def transfer(self, _to: Address, _tokenId: int):
        """
        Transfers the ownership of your NFT to another address,
        and MUST fire the Transfer event. Throws unless self.msg.sender
        is the current owner. Throws if _to is the zero address.
        Throws if _tokenId is not a valid NFT.
        """
        if self.ownerOf(_tokenId) != self.msg.sender:
            revert("You don't have permission to transfer this NFT")
        self._transfer(self.msg.sender, _to, _tokenId)

    @external
    def transferFrom(self, _from: Address, _to: Address, _tokenId: int):
        """
        Transfers the ownership of an NFT from one address to another address,
        and MUST fire the Transfer event. Throws unless self.msg.sender is the
        current owner or the approved address for the NFT. Throws if _from is
        not the current owner. Throws if _to is the zero address. Throws if
        _tokenId is not a valid NFT.
        """
        if self.ownerOf(_tokenId) != self.msg.sender and \
                self._tokenApprovals[_tokenId] != self.msg.sender:
            revert("You don't have permission to transfer this NFT")
        self._transfer(_from, _to, _tokenId)

    def _transfer(self, _from: Address, _to: Address, _tokenId: int):
        if _to is None or self._is_zero_address(_to):
            revert("You can't transfer to a zero address")

        self._clear_approval(_tokenId)
        self._remove_tokens_from(_from, _tokenId)
        self._add_tokens_to(_to, _tokenId)
        self.Transfer(_from, _to, _tokenId)
        Logger.debug(f'Transfer({_from}, {_to}, {_tokenId}, TAG)')

    @external
    def mint(self, _to: Address, _tokenId: int, _tokenUri: str):
        # Mint a new NFT token
        self._ensure_positive(_tokenId)
        if self.msg.sender != self.owner:
            revert("You don't have permission to mint NFT")
        if _tokenId in self._tokenOwner:
            revert("Token already exists")
        self._add_tokens_to(_to, _tokenId)
        self._setTokenUri(_tokenId, _tokenUri)
        self._createNewTokenIndex(_tokenId)
        self.Transfer(self._ZERO_ADDRESS, _to, _tokenId)

    @external
    def burn(self, _tokenId: int):
        # Burn NFT token
        if self.ownerOf(_tokenId) != self.msg.sender:
            revert("You dont have permission to burn this NFT")
        self._burn(self.msg.sender, _tokenId)

    def _burn(self, _owner: Address, _tokenId: int):
        self._clear_approval(_tokenId)
        self._remove_tokens_from(_owner, _tokenId)
        self._removeTokenUri(_tokenId)
        tokenIndex = self._getTokenIndexByTokenId(_tokenId)
        self._adjustTokenIndex(tokenIndex)
        self.Transfer(_owner, self._ZERO_ADDRESS, _tokenId)

    def _is_zero_address(self, _address: Address) -> bool:
        # Check if address is zero address
        if _address == self._ZERO_ADDRESS:
            return True
        return False

    def _ensure_positive(self, _tokenId: int):
        if _tokenId is None or _tokenId < 0:
            revert("tokenId should be positive")

    def _clear_approval(self, _tokenId: int):
        # Delete token's approved operator
        if _tokenId in self._tokenApprovals:
            del self._tokenApprovals[_tokenId]

    @external(readonly=True)
    def tokenURI(self, _tokenId: int) -> str:
        """
        A distinct Uniform Resource Identifier (URI) for a given asset.
        See "IRC3 Metadata JSON Schema" format for details about the format.
        """
        self._ensure_positive(_tokenId)

        tokenURI = self._tokenURIs[_tokenId]
        if tokenURI is None:
            revert("NFT with given _tokenId does not have metadata")
        if self._is_zero_address(tokenURI):
            revert("Invalid _tokenId. NFT is burned")

        return tokenURI

    def _setTokenUri(self, _tokenId: int, _tokenURI: str):
        """
        Set token URI for a given token. Reverts if a token does not exist.
        """
        self._ensure_positive(_tokenId)
        self._tokenURIs[_tokenId] = _tokenURI

    def _removeTokenUri(self, _tokenId: int):
        del self._tokenURIs[_tokenId]

    @external(readonly=True)
    def ownedTokens(self, _owner: Address) -> list:
        """
        Returns an unsorted list of tokens owned by _owner.
        """
        numberOfTokens = self.balanceOf(_owner)
        ownedTokens = []
        for x in range(1, numberOfTokens + 1):
            token = self.tokenOfOwnerByIndex(_owner, x)
            if token != 0:
                ownedTokens.append(self.tokenOfOwnerByIndex(_owner, x))

        return ownedTokens

    @external(readonly=True)
    def totalSupply(self) -> int:
        """
        Returns total number of valid NFTs.
        """
        return self._totalSupply.get()

    def _decrementTotalSupply(self):
        self._totalSupply.set(self._totalSupply.get() - 1)

    def _incrementTotalSupply(self):
        self._totalSupply.set(self._totalSupply.get() + 1)

    def _add_tokens_to(self, _to: Address, _tokenId: int):
        # Add token to new owner and increase token count of owner by 1
        self._tokenOwner[_tokenId] = _to
        self._ownedTokenCount[_to] += 1

        # Add an index to the token for the owner
        index = self._ownedTokenCount[_to]
        self._setOwnerTokenIndex(_to, index, _tokenId)

    def _remove_tokens_from(self, _from: Address, _tokenId: int):
        # Replaces token on last index with the token that will be removed.
        lastIndex = self.balanceOf(_from)
        lastToken = self.tokenOfOwnerByIndex(_from, lastIndex)
        index = self._findTokenIndexByTokenId(_from, _tokenId)
        self._setOwnerTokenIndex(_from, index, lastToken)
        self._removeOwnerTokenIndex(_from, lastIndex)

        # Remove token ownership and subtract owner's token count by 1
        self._ownedTokenCount[_from] -= 1
        self._tokenOwner[_tokenId] = self._ZERO_ADDRESS

    @external(readonly=True)
    def tokenByIndex(self, _index: int) -> int:
        """
        Returns the _tokenId for '_index'th NFT. Returns 0 for invalid result.
        """
        result = VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    def _createNewTokenIndex(self, _tokenId: int):
        """
        Creates an index for _tokenId and increases _totalSupply
        """
        newSupply = self._totalSupply.get() + 1
        self._setTokenIndex(newSupply, _tokenId)
        self._incrementTotalSupply()

    def _adjustTokenIndex(self, _tokenIndex: int):
        """
        Lowers _totalSupply and makes sure all tokens are indexed by moving
        token with last index to the index that is being removed.
        """
        lastIndex = self.totalSupply()
        lastToken = self.tokenByIndex(lastIndex)
        self._removeTokenIndex(_tokenIndex)
        self._removeTokenIndex(lastIndex)
        self._setTokenIndex(_tokenIndex, lastToken)
        self._decrementTotalSupply()

    def _getTokenIndexByTokenId(self, _tokenId: int) -> int:
        result = VarDB(f'TOKEN_{str(_tokenId)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    def _setTokenIndex(self, _index: int, _tokenId: int):
        VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).set(_tokenId)
        VarDB(f'TOKEN_{str(_tokenId)}', self._db, value_type=int).set(_index)

    def _removeTokenIndex(self, _index: int):
        tokenId = VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).get()
        VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).remove()
        VarDB(f'TOKEN_{str(tokenId)}', self._db, value_type=int).remove()

    def _findTokenIndexByTokenId(self, _owner: Address, _tokenId: int) -> int:
        # Returns index of a given _tokenId of _owner. Returns 0 when no result.
        numberOfTokens = self.balanceOf(_owner)
        for x in range(1, numberOfTokens + 1):
            if self.tokenOfOwnerByIndex(_owner, x) == _tokenId:
                return x
        return 0

    @external(readonly=True)
    def tokenOfOwnerByIndex(self, _owner: Address, _index: int) -> int:
        """
        Returns _tokenId assigned to the _owner on a given _index.
        Throws if _owner does not exist or if _index is out of bounds.
        """
        result = VarDB(f'{str(_owner)}_{str(_index)}', self._db, value_type=str).get()
        if result:
            return int(result)
        else:
            return 0

    def _setOwnerTokenIndex(self, _address: Address, _index: int, _tokenId: int):
        VarDB(f'{str(_address)}_{str(_index)}', self._db, value_type=str).set(str(_tokenId))

    def _removeOwnerTokenIndex(self, _address: Address, _index: int):
        VarDB(f'{str(_address)}_{str(_index)}', self._db, value_type=str).remove()

    @eventlog(indexed=3)
    def Approval(self, _owner: Address, _approved: Address, _tokenId: int):
        pass

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _tokenId: int):
        pass
