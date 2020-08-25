from .interfaces import *

TAG = 'NebulaPlanetToken'

class NebulaPlanetToken(IconScoreBase, IRC3, IRC3Metadata, IRC3Enumerable):
    _OWNED_TOKEN_COUNT = 'owned_token_count'  # Track token count against token owners
    _TOKEN_OWNER = 'token_owner'  # Track token owner against token ID
    _TOKEN_APPROVALS = 'token_approvals'  # Track token approved owner against token ID
    _TOKEN_URIS = 'token_URIs'  # Track token URIs against token ID
    _OWNED_TOKENS = 'owned_tokens'  # Track tokens against token owners
    _TOTAL_SUPPLY = 'total_supply'  # Tracks total number of valid tokens (excluding ones with zero address)
    _LISTED_TOKEN_PRICES = 'listed_token_prices'  # Tracks listed token prices against token IDs
    _OWNER_LISTED_TOKEN_COUNT = 'owner_listed_token_count'  # Tracks number of listed tokens against token owners
    _TOTAL_LISTED_TOKEN_COUNT = 'total_listed_token_count'  # Tracks total number of listed tokens
    _DIRECTOR = 'director'  # Role responsible for assigning other roles.
    _TREASURER = 'treasurer'  # Role responsible for transferring money to and from the contract
    _MINTER = 'minter'  # Role responsible for minting and burning tokens
    _IS_PAUSED = 'is_paused' # Boolean value that indicates whether a contract is paused
    MAX_ITERATION_LOOP = 100

    _ZERO_ADDRESS = Address.from_prefix_and_int(AddressPrefix.EOA, 0)

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._ownedTokenCount = DictDB(self._OWNED_TOKEN_COUNT, db, value_type=int)
        self._tokenOwner = DictDB(self._TOKEN_OWNER, db, value_type=Address)
        self._tokenApprovals = DictDB(self._TOKEN_APPROVALS, db, value_type=Address)
        self._tokenURIs = DictDB(self._TOKEN_URIS, db, value_type=str)
        self._totalSupply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._ownerListedTokenCount = DictDB(self._OWNER_LISTED_TOKEN_COUNT, db, value_type=int)
        self._totalListedTokenCount = VarDB(self._TOTAL_LISTED_TOKEN_COUNT, db, value_type=int)
        self._listedTokenPrices = DictDB(self._LISTED_TOKEN_PRICES, db, value_type=int)
        self._director = VarDB(self._DIRECTOR, db, value_type=Address)
        self._treasurer = VarDB(self._TREASURER, db, value_type=Address)
        self._minter = VarDB(self._MINTER, db, value_type=Address)
        self._isPaused = VarDB(self._IS_PAUSED, db, value_type=bool)

        self._db = db

    def on_install(self) -> None:
        super().on_install()
        self._director.set(self.msg.sender)
        self._treasurer.set(self.msg.sender)
        self._minter.set(self.msg.sender)
        self._isPaused.set(False)

    def on_update(self) -> None:
        super().on_update()

    @payable
    def fallback(self):
        """
        Called when funds are sent to the contract.
        Throws if sender is not the Treasurer.
        """
        if self._treasurer.get() != self.msg.sender:
            revert('You are not allowed to deposit to this contract')

    # def _isPaused(self):
    #     self._isPaused()

    @external
    def withdraw(self, amount: int):
        """
        Used to withdraw funds from the contract.
        Throws if sender is not the Treasurer.
        """
        treasurer = self._treasurer.get()
        if treasurer != self.msg.sender:
            revert('You are not allowed to withdraw from this contract')
        self.icx.send(treasurer, amount)

    @external
    def assignTreasurer(self, _address: Address):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._treasurer.remove()
        self._treasurer.set(_address)
        self.AssignRole("Treasurer", _address)

    @external
    def assignMinter(self, _address: Address):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._minter.remove()
        self._minter.set(_address)
        self.AssignRole("Minter", _address)

    @external
    def pauseContract(self):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to pause the contract')
        if self._isPaused.get():
            revert('Contract is already paused')
        self._isPaused.set(True)
        self.PauseContract()

    @external
    def unpauseContract(self):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to unpause the contract')
        if not self._isPaused.get():
            revert('Contract is already unpaused')
        self._isPaused.set(False)
        self.UnpauseContract()


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
        if self._isPaused.get() and not self.msg.sender == self._minter.get():
            revert("Contract is currently paused")
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
        if self._isPaused.get() and not self.msg.sender == self._minter.get():
            revert("Contract is currently paused")
        self._transfer(_from, _to, _tokenId)

    def _transfer(self, _from: Address, _to: Address, _tokenId: int):
        if _to is None or self._is_zero_address(_to):
            revert("You can't transfer to a zero address")

        self._clear_approval(_tokenId)
        if self.getTokenPrice(_tokenId):
            self._delistToken(_from, _tokenId)
        self._remove_tokens_from(_from, _tokenId)
        self._add_tokens_to(_to, _tokenId)
        self.Transfer(_from, _to, _tokenId)
        Logger.debug(f'Transfer({_from}, {_to}, {_tokenId}, TAG)')

    @external
    def mint(self, _to: Address, _tokenId: int, _tokenUri: str):
        # Mint a new NFT token
        self._ensure_positive(_tokenId)
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to mint tokens')
        if _tokenId in self._tokenOwner:
            revert("Token already exists")
        self._add_tokens_to(_to, _tokenId)
        self._setTokenUri(_tokenId, _tokenUri)
        self._createNewTokenIndex(_tokenId)
        self.Transfer(self._ZERO_ADDRESS, _to, _tokenId)

    @external
    def burn(self, _tokenId: int):
        # Burn NFT token
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to burn tokens')
        self._burn(self.msg.sender, _tokenId)

    def _burn(self, _owner: Address, _tokenId: int):
        self._clear_approval(_tokenId)
        self._remove_tokens_from(_owner, _tokenId)
        self._removeTokenUri(_tokenId)
        tokenIndex = self._getTokenIndexByTokenId(_tokenId)
        self._adjustTokenIndex(tokenIndex)
        if self.getTokenPrice(_tokenId):
            self._delistToken(_owner, _tokenId)
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

    # ================================================
    #  Metadata extension
    # ================================================

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
        Set token URI for a given token. Throws if a token does not exist.
        """
        self._ensure_positive(_tokenId)
        self._tokenURIs[_tokenId] = _tokenURI

    def _removeTokenUri(self, _tokenId: int):
        del self._tokenURIs[_tokenId]

    # ================================================
    #  Enumerable extension
    # ================================================

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

    # ================================================
    #  Exchange
    # ================================================

    @external
    def listToken(self, _tokenId: int, _price: int):
        """
        Lists token for sale. Throws if sender does not own the token.
        Throws if token price is not positive.
        """
        owner = self.ownerOf(_tokenId)
        sender = self.msg.sender
        if self._isPaused.get() and not self.msg.sender == self._minter.get():
            revert("Contract is currently paused")
        if sender != owner:
            revert("You do not own this NFT")
        if _price < 0:
            revert("Price can not be negative")
        if _price == 0:
            revert("Price can not be zero")

        self._incrementListedTokenCount()
        self._setListedTokenIndex(self._totalListedTokenCount.get(), _tokenId)

        self._listedTokenPrices[str(_tokenId)] = _price

        self._ownerListedTokenCount[sender] += 1
        self._setOwnerListedTokenIndex(sender, self._ownerListedTokenCount[sender], _tokenId)
        self.ListToken(owner, _tokenId, _price)

    @external(readonly=True)
    def totalListedTokenCount(self) -> int:
        """ Returns total number of tokens listed for sale. """
        return self._totalListedTokenCount.get()

    @external(readonly=True)
    def listedTokens(self, _offset: int = 0) -> dict:
        """
        Returns dict of tokens listed for sale, where key is _tokenId and value is current price.
        Only 100 tokens are returned at a time, meaning client is responsible for making multiple
        requests if more is required. Optional parameter _offset can be used to get next batch
        of tokens. For example: listedTokens(100) returns tokens 101-200.
        """
        iterationCount = self.totalListedTokenCount()
        if self.MAX_ITERATION_LOOP < self.totalListedTokenCount():
            iterationCount = self.MAX_ITERATION_LOOP
        tokens = {}
        for x in range(1 + _offset, iterationCount + _offset + 1):
            tokenId = self.getListedTokenByIndex(x)
            price = self.getTokenPrice(tokenId)
            if (tokenId and price):
                tokens[tokenId] = price
        return tokens

    @external(readonly=True)
    def listedTokenCountByOwner(self, _owner: Address) -> int:
        """ Returns total number of tokens listed for sale by _owner. """
        if _owner is None or self._is_zero_address(_owner):
            revert("Invalid owner")
        return self._ownerListedTokenCount[_owner]

    @external(readonly=True)
    def listedTokensByOwner(self, _owner: Address, offset: int = 0) -> dict:
        """
        Returns dict of tokens listed for sale by given _owner, where key is _tokenId and value is current price.
        Only 100 tokens are returned at a time, meaning client is responsible for making multiple requests if more is
        required. Optional parameter _offset can be used to get next batch of tokens.
        For example: listedTokens(100) returns tokens 101-200.
        """
        iterationCount = self.listedTokenCountByOwner(_owner)
        if self.MAX_ITERATION_LOOP < self.totalListedTokenCount():
            iterationCount = self.MAX_ITERATION_LOOP
        tokens = {}
        for x in range(1 + offset, iterationCount + offset + 1):
            tokenId = self.getListedTokenOfOwnerByIndex(_owner, x)
            price = self.getTokenPrice(tokenId)
            if (tokenId and price):
                tokens[tokenId] = price
        return tokens

    @external
    def delistToken(self, _tokenId: int):
        """ Removes token from sale. Throws if token is not listed. Throws if sender does not own the token. """
        owner = self.ownerOf(_tokenId)
        if self.msg.sender != owner:
            revert("You do not own this NFT")
        if not self.getTokenPrice(_tokenId):
            revert("Token is not listed")

        self._delistToken(owner, _tokenId)

    def _delistToken(self, _owner: Address, _tokenId: int):
        self._removeTokenListing(_tokenId)
        self._removeOwnerTokenListing(_owner, _tokenId)
        self.clearTokenPrice(_tokenId)

        self.DelistToken(_owner, _tokenId)

    def _removeTokenListing(self, _tokenId: int):
        """ Adjusts token indexes by deleting token that is about to be removed and moving last token in its place. """
        activeIndex = self._getListedTokenIndexByTokenId(_tokenId)
        lastIndex = self.totalListedTokenCount()
        lastToken = self.getListedTokenByIndex(lastIndex)
        self._removeListedTokenIndex(activeIndex)
        self._removeListedTokenIndex(lastIndex)
        self._setListedTokenIndex(activeIndex, lastToken)
        self._decrementListedTokenCount()

    def _removeOwnerTokenListing(self, _owner: Address, _tokenId: int):
        """
        Adjusts token indexes by deleting token that is about to be removed,
        and moving the last token in its place.
        """
        activeIndex = self._getListedTokenOfOwnerByTokenId(_owner, _tokenId)
        lastIndex = self.listedTokenCountByOwner(_owner)
        lastToken = self.getListedTokenOfOwnerByIndex(_owner, lastIndex)
        self._removeOwnerListedTokenIndex(_owner, activeIndex)
        self._removeOwnerListedTokenIndex(_owner, lastIndex)
        self._setOwnerListedTokenIndex(_owner, activeIndex, lastToken)
        self._ownerListedTokenCount[_owner] -= 1

    def _getListedTokenOfOwnerByTokenId(self, _owner: Address, _tokenId: int) -> int:
        """ Returns list index of a given _tokenId of _owner. Returns 0 when no result. """
        numberOfTokens = self.listedTokenCountByOwner(_owner)
        for x in range(1, numberOfTokens + 1):
            if self.getListedTokenOfOwnerByIndex(_owner, x) == _tokenId:
                return x
        return 0

    @external(readonly=True)
    def getTokenPrice(self, _tokenId: int) -> int:
        """ Returns price the token is being sold for. """
        return self._listedTokenPrices[str(_tokenId)]

    def clearTokenPrice(self, _tokenId: int):
        """ Returns price the token is being sold for. """
        DictDB(self._LISTED_TOKEN_PRICES, self.db, value_type=int).remove(str(_tokenId))

    @external(readonly=True)
    def getListedTokenByIndex(self, _index: int) -> int:
        """ Returns token ID on _index'th position from all tokens listed for sale. Can be used iterate through
        all valid tokens that are for sale. """
        result = VarDB(f'LISTED_TOKEN_INDEX_{str(_index)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    @external(readonly=True)
    def getListedTokenOfOwnerByIndex(self, _owner: Address, _index: int) -> int:
        """
        Returns token ID from _owner's listed tokens on index number _index. When used together with
        listedTokenCountByOwner(), this method can be used to iterate through tokens owned by _owner on client side.
        """
        result = VarDB(f'LISTED_{str(_owner)}_{str(_index)}', self._db, value_type=str).get()
        if result:
            return int(result)
        else:
            return 0

    @external
    @payable
    def purchaseToken(self, _tokenId: int):
        """
        Purchases a token listed for sale with given _tokenId. The amount of ICX sent must match the token sale price,
        otherwise throws an error. When a correct amount is sent, the NFT will be sent from seller to buyer, and SCORE
        will send token's price worth of ICX to seller (minus fee, if applicable).
        """
        tokenPrice = self.getTokenPrice(_tokenId)
        if self.msg.value != tokenPrice:
            revert(f'Sent ICX amount ({self.msg.value}) does not match token price ({tokenPrice})')

        seller = self.ownerOf(_tokenId)
        buyer = self.msg.sender
        self._delistToken(seller, _tokenId)
        self._transfer(seller, buyer, _tokenId)
        self.icx.transfer(seller, tokenPrice)

        # self._removeTokenListing(_tokenId)
        self.PurchaseToken(seller, buyer, _tokenId)

    def _getOwnerListedTokenIndex(self, _address: Address, _index: int) -> int:
        return int(VarDB(f'LISTED_{str(_address)}_{str(_index)}', self._db, value_type=str).get())

    def _setOwnerListedTokenIndex(self, _address: Address, _index: int, _tokenId: int):
        VarDB(f'LISTED_{str(_address)}_{str(_index)}', self._db, value_type=str).set(str(_tokenId))

    def _removeOwnerListedTokenIndex(self, _address: Address, _index: int):
        VarDB(f'LISTED_{str(_address)}_{str(_index)}', self._db, value_type=str).remove()

    def _decrementListedTokenCount(self):
        self._totalListedTokenCount.set(self._totalListedTokenCount.get() - 1)

    def _incrementListedTokenCount(self):
        self._totalListedTokenCount.set(self._totalListedTokenCount.get() + 1)

    def _getListedTokenIndexByTokenId(self, _tokenId: int) -> int:
        result = VarDB(f'LISTED_TOKEN_{str(_tokenId)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    def _setListedTokenIndex(self, _index: int, _tokenId: int):
        VarDB(f'LISTED_TOKEN_INDEX_{str(_index)}', self._db, value_type=int).set(_tokenId)
        VarDB(f'LISTED_TOKEN_{str(_tokenId)}', self._db, value_type=int).set(_index)

    def _removeListedTokenIndex(self, _index: int):
        tokenId = VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).get()
        VarDB(f'LISTED_TOKEN_INDEX_{str(_index)}', self._db, value_type=int).remove()
        VarDB(f'LISTED_TOKEN_{str(tokenId)}', self._db, value_type=int).remove()

    def _findListedTokenIndexByTokenId(self, _owner: Address, _tokenId: int) -> int:
        # Returns listing index of a given _tokenId of _owner. Returns 0 when no result.
        numberOfTokens = self.listedTokenCountByOwner(_owner)
        for x in range(1, numberOfTokens + 1):
            if self.getListedTokenOfOwnerByIndex(_owner, x) == _tokenId:
                return x
        return 0


    @eventlog(indexed=3)
    def Approval(self, _owner: Address, _approved: Address, _tokenId: int):
        pass

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _tokenId: int):
        pass

    @eventlog(indexed=3)
    def PurchaseToken(self, _seller: Address, _buyer: Address, _tokenId: int):
        pass

    @eventlog(indexed=3)
    def ListToken(self, _owner: Address, _tokenId: int, price: int):
        pass

    @eventlog(indexed=2)
    def DelistToken(self, _owner: Address, _tokenId: int):
        pass

    @eventlog(indexed=2)
    def AssignRole(self, _role: str, _owner: Address):
        pass

    @eventlog
    def PauseContract(self):
        pass

    @eventlog
    def UnpauseContract(self):
        pass
