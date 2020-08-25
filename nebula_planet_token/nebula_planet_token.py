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
    _MAX_ITERATION_LOOP = 100

    _ZERO_ADDRESS = Address.from_prefix_and_int(AddressPrefix.EOA, 0)

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._owned_token_count = DictDB(self._OWNED_TOKEN_COUNT, db, value_type=int)
        self._token_owner = DictDB(self._TOKEN_OWNER, db, value_type=Address)
        self._token_approvals = DictDB(self._TOKEN_APPROVALS, db, value_type=Address)
        self._token_URIs = DictDB(self._TOKEN_URIS, db, value_type=str)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._total_listed_token_count = VarDB(self._TOTAL_LISTED_TOKEN_COUNT, db, value_type=int)
        self._owner_listed_token_count = DictDB(self._OWNER_LISTED_TOKEN_COUNT, db, value_type=int)
        self._listed_token_prices = DictDB(self._LISTED_TOKEN_PRICES, db, value_type=int)
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
    def assign_treasurer(self, _address: Address):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._treasurer.remove()
        self._treasurer.set(_address)
        self.AssignRole("Treasurer", _address)

    @external
    def assign_minter(self, _address: Address):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._minter.remove()
        self._minter.set(_address)
        self.AssignRole("Minter", _address)

    @external
    def pause_contract(self):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to pause the contract')
        if self._isPaused.get():
            revert('Contract is already paused')
        self._isPaused.set(True)
        self.PauseContract()

    @external
    def unpause_contract(self):
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
        return self._owned_token_count[_owner]

    @external(readonly=True)
    def ownerOf(self, _tokenId: int) -> Address:
        """
        Returns the owner of an NFT. Throws if _tokenId is not a valid NFT.
        """
        self._ensure_positive(_tokenId)
        owner = self._token_owner[_tokenId]
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
        address = self._token_approvals[_tokenId]
        if address is None:
            return self._ZERO_ADDRESS
        return address

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

        self._token_approvals[_tokenId] = _to
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
                self._token_approvals[_tokenId] != self.msg.sender:
            revert("You don't have permission to transfer this NFT")
        if self._isPaused.get() and not self.msg.sender == self._minter.get():
            revert("Contract is currently paused")
        self._transfer(_from, _to, _tokenId)

    def _transfer(self, _from: Address, _to: Address, _token_id: int):
        if _to is None or self._is_zero_address(_to):
            revert("You can't transfer to a zero address")

        self._clear_approval(_token_id)
        if self.get_token_price(_token_id):
            self._delist_token(_from, _token_id)
        self._remove_tokens_from(_from, _token_id)
        self._add_tokens_to(_to, _token_id)
        self.Transfer(_from, _to, _token_id)
        Logger.debug(f'Transfer({_from}, {_to}, {_token_id}, TAG)')

    @external
    def mint(self, _to: Address, _token_id: int, _token_URI: str):
        # Mint a new NFT token
        self._ensure_positive(_token_id)
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to mint tokens')
        if _token_id in self._token_owner:
            revert("Token already exists")
        self._add_tokens_to(_to, _token_id)
        self._set_token_URI(_token_id, _token_URI)
        self._create_new_token_index(_token_id)
        self.Transfer(self._ZERO_ADDRESS, _to, _token_id)

    @external
    def burn(self, _token_id: int):
        # Burn NFT token
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to burn tokens')
        self._burn(_token_id)

    def _burn(self, _token_id: int):
        self._clear_approval(_token_id)
        token_owner = self.ownerOf(_token_id)
        if self.get_token_price(_token_id):
            self._delist_token(token_owner, _token_id)
        self._remove_tokens_from(token_owner, _token_id)
        self._remove_token_URI(_token_id)
        tokenIndex = self._get_token_index_by_token_id(_token_id)
        self._adjust_token_index(tokenIndex)

        self.Transfer(token_owner, self._ZERO_ADDRESS, _token_id)

    def _is_zero_address(self, _address: Address) -> bool:
        # Check if address is zero address
        if _address == self._ZERO_ADDRESS:
            return True
        return False

    def _ensure_positive(self, _token_id: int):
        if _token_id is None or _token_id < 0:
            revert("tokenId should be positive")

    def _clear_approval(self, _tokenId: int):
        # Delete token's approved operator
        if _tokenId in self._token_approvals:
            del self._token_approvals[_tokenId]

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

        token_URI = self._token_URIs[_tokenId]
        if token_URI is None:
            revert("NFT with given _tokenId does not have metadata")
        if self._is_zero_address(token_URI):
            revert("Invalid _tokenId. NFT is burned")

        return token_URI

    def _set_token_URI(self, _tokenId: int, _token_URI: str):
        """
        Set token URI for a given token. Throws if a token does not exist.
        """
        self._ensure_positive(_tokenId)
        self._token_URIs[_tokenId] = _token_URI

    def _remove_token_URI(self, _token_id: int):
        del self._token_URIs[_token_id]

    # ================================================
    #  Enumerable extension
    # ================================================

    @external(readonly=True)
    def owned_tokens(self, _owner: Address) -> list:
        """
        Returns an unsorted list of tokens owned by _owner.
        """
        number_of_tokens = self.balanceOf(_owner)
        owned_tokens = []
        for x in range(1, number_of_tokens + 1):
            token = self.tokenOfOwnerByIndex(_owner, x)
            if token != 0:
                owned_tokens.append(self.tokenOfOwnerByIndex(_owner, x))

        return owned_tokens

    @external(readonly=True)
    def totalSupply(self) -> int:
        """
        Returns total number of valid NFTs.
        """
        return self._total_supply.get()

    def _decrement_total_supply(self):
        self._total_supply.set(self._total_supply.get() - 1)

    def _increment_total_supply(self):
        self._total_supply.set(self._total_supply.get() + 1)

    def _add_tokens_to(self, _to: Address, _token_id: int):
        # Add token to new owner and increase token count of owner by 1
        self._token_owner[_token_id] = _to
        self._owned_token_count[_to] += 1

        # Add an index to the token for the owner
        index = self._owned_token_count[_to]
        self._set_owner_token_index(_to, index, _token_id)

    def _remove_tokens_from(self, _from: Address, _token_id: int):
        # Replaces token on last index with the token that will be removed.
        last_index = self.balanceOf(_from)
        last_token = self.tokenOfOwnerByIndex(_from, last_index)
        index = self._find_token_index_by_token_id(_from, _token_id)
        if last_index > 1:
            self._set_owner_token_index(_from, index, last_token)
        self._remove_owner_token_index(_from, last_index)

        # Remove token ownership and subtract owner's token count by 1
        self._owned_token_count[_from] -= 1
        self._token_owner[_token_id] = self._ZERO_ADDRESS

    @external(readonly=True)
    def tokenByIndex(self, _index: int) -> int:
        """
        Returns the _token_id for '_index'th NFT. Returns 0 for invalid result.
        """
        result = VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    def _create_new_token_index(self, _token_id: int):
        """
        Creates an index for _token_id and increases _totalSupply
        """
        new_supply = self._total_supply.get() + 1
        self._set_token_index(new_supply, _token_id)
        self._increment_total_supply()

    def _adjust_token_index(self, _token_id: int):
        """
        Lowers _totalSupply and makes sure all tokens are indexed by moving
        token with last index to the index that is being removed.
        """
        lastIndex = self.totalSupply()
        lastToken = self.tokenByIndex(lastIndex)
        self._remove_token_index(_token_id)
        self._remove_token_index(lastIndex)
        if lastIndex > 1:
            self._set_token_index(_token_id, lastToken)
        self._decrement_total_supply()

    def _get_token_index_by_token_id(self, _token_id: int) -> int:
        result = VarDB(f'TOKEN_{str(_token_id)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    def _set_token_index(self, _index: int, _token_id: int):
        VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).set(_token_id)
        VarDB(f'TOKEN_{str(_token_id)}', self._db, value_type=int).set(_index)

    def _remove_token_index(self, _index: int):
        token_id = VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).get()
        VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).remove()
        VarDB(f'TOKEN_{str(token_id)}', self._db, value_type=int).remove()

    def _find_token_index_by_token_id(self, _owner: Address, _token_id: int) -> int:
        # Returns index of a given _token_id of _owner. Returns 0 when no result.
        number_of_tokens = self.balanceOf(_owner)
        for x in range(1, number_of_tokens + 1):
            if self.tokenOfOwnerByIndex(_owner, x) == _token_id:
                return x
        return 0

    @external(readonly=True)
    def tokenOfOwnerByIndex(self, _owner: Address, _index: int) -> int:
        """
        Returns _token_id assigned to the _owner on a given _index.
        Throws if _owner does not exist or if _index is out of bounds.
        """
        result = VarDB(f'{str(_owner)}_{str(_index)}', self._db, value_type=str).get()
        if result:
            return int(result)
        else:
            return 0

    def _set_owner_token_index(self, _address: Address, _index: int, _token_id: int):
        VarDB(f'{str(_address)}_{str(_index)}', self._db, value_type=str).set(str(_token_id))

    def _remove_owner_token_index(self, _address: Address, _index: int):
        VarDB(f'{str(_address)}_{str(_index)}', self._db, value_type=str).remove()

    # ================================================
    #  Exchange
    # ================================================

    @external
    def list_token(self, _token_id: int, _price: int):
        """
        Lists token for sale. Throws if sender does not own the token.
        Throws if token price is not positive.
        """
        owner = self.ownerOf(_token_id)
        sender = self.msg.sender
        if self._isPaused.get() and not self.msg.sender == self._minter.get():
            revert("Contract is currently paused")
        if sender != owner:
            revert("You do not own this NFT")
        if _price < 0:
            revert("Price can not be negative")
        if _price == 0:
            revert("Price can not be zero")

        self._increment_listed_token_count()
        self._set_listed_token_index(self._total_listed_token_count.get(), _token_id)

        self._listed_token_prices[str(_token_id)] = _price

        self._owner_listed_token_count[sender] += 1
        self._set_owner_listed_token_index(sender, self._owner_listed_token_count[sender], _token_id)
        self.ListToken(owner, _token_id, _price)

    @external(readonly=True)
    def total_listed_token_count(self) -> int:
        """ Returns total number of tokens listed for sale. """
        return self._total_listed_token_count.get()

    @external(readonly=True)
    def listed_tokens(self, _offset: int = 0) -> dict:
        """
        Returns dict of tokens listed for sale, where key is _tokenId and value is current price.
        Only 100 tokens are returned at a time, meaning client is responsible for making multiple
        requests if more is required. Optional parameter _offset can be used to get next batch
        of tokens. For example: listedTokens(100) returns tokens 101-200.
        """
        iteration_count = self.total_listed_token_count()
        if self._MAX_ITERATION_LOOP < self.total_listed_token_count():
            iteration_count = self._MAX_ITERATION_LOOP
        tokens = {}
        for x in range(1 + _offset, iteration_count + _offset + 1):
            token_id = self.get_listed_token_by_index(x)
            price = self.get_token_price(token_id)
            if token_id and price:
                tokens[token_id] = price
        return tokens

    @external(readonly=True)
    def listed_token_count_by_owner(self, _owner: Address) -> int:
        """ Returns total number of tokens listed for sale by _owner. """
        if _owner is None or self._is_zero_address(_owner):
            revert("Invalid owner")
        return self._owner_listed_token_count[_owner]

    @external(readonly=True)
    def listed_tokens_by_owner(self, _owner: Address, offset: int = 0) -> dict:
        """
        Returns dict of tokens listed for sale by given _owner, where key is _tokenId and value is current price.
        Only 100 tokens are returned at a time, meaning client is responsible for making multiple requests if more is
        required. Optional parameter _offset can be used to get next batch of tokens.
        For example: listedTokens(100) returns tokens 101-200.
        """
        iteration_count = self.listed_token_count_by_owner(_owner)
        if self._MAX_ITERATION_LOOP < self.total_listed_token_count():
            iteration_count = self._MAX_ITERATION_LOOP
        tokens = {}
        for x in range(1 + offset, iteration_count + offset + 1):
            token_id = self.get_listed_token_of_owner_by_index(_owner, x)
            price = self.get_token_price(token_id)
            if token_id and price:
                tokens[token_id] = price
        return tokens

    @external
    def delist_token(self, _token_id: int):
        """ Removes token from sale. Throws if token is not listed. Throws if sender does not own the token. """
        owner = self.ownerOf(_token_id)
        if self.msg.sender != owner:
            revert("You do not own this NFT")
        if not self.get_token_price(_token_id):
            revert("Token is not listed")

        self._delist_token(owner, _token_id)

    def _delist_token(self, _owner: Address, _token_id: int):
        self._remove_token_listing(_token_id)
        self._remove_owner_token_listing(_owner, _token_id)
        self.clear_token_price(_token_id)

        self.DelistToken(_owner, _token_id)

    def _remove_token_listing(self, _tokenId: int):
        """ Adjusts token indexes by deleting token that is about to be removed and moving last token in its place. """
        active_index = self._get_listed_token_index_by_token_id(_tokenId)
        last_index = self.total_listed_token_count()
        last_token = self.get_listed_token_by_index(last_index)
        self._remove_listed_token_index(active_index)
        self._remove_listed_token_index(last_index)
        if last_index > 1:
            self._set_listed_token_index(active_index, last_token)
        self._decrement_listed_token_count()

    def _remove_owner_token_listing(self, _owner: Address, _token_id: int):
        """
        Adjusts token indexes by deleting token that is about to be removed,
        and moving the last token in its place.
        """
        active_index = self._get_listed_token_of_owner_by_token_id(_owner, _token_id)
        last_index = self.listed_token_count_by_owner(_owner)
        last_token = self.get_listed_token_of_owner_by_index(_owner, last_index)
        self._remove_owner_listed_token_index(_owner, active_index)
        self._remove_owner_listed_token_index(_owner, last_index)
        if last_index > 1:
            self._set_owner_listed_token_index(_owner, active_index, last_token)
        self._owner_listed_token_count[_owner] -= 1

    def _get_listed_token_of_owner_by_token_id(self, _owner: Address, _token_id: int) -> int:
        """ Returns list index of a given _token_id of _owner. Returns 0 when no result. """
        number_of_tokens = self.listed_token_count_by_owner(_owner)
        for x in range(1, number_of_tokens + 1):
            if self.get_listed_token_of_owner_by_index(_owner, x) == _token_id:
                return x
        return 0

    @external(readonly=True)
    def get_token_price(self, _tokenId: int) -> int:
        """ Returns price the token is being sold for. """
        return self._listed_token_prices[str(_tokenId)]

    def clear_token_price(self, _tokenId: int):
        """ Returns price the token is being sold for. """
        DictDB(self._LISTED_TOKEN_PRICES, self.db, value_type=int).remove(str(_tokenId))

    @external(readonly=True)
    def get_listed_token_by_index(self, _index: int) -> int:
        """ Returns token ID on _index'th position from all tokens listed for sale. Can be used iterate through
        all valid tokens that are for sale. """
        result = VarDB(f'LISTED_TOKEN_INDEX_{str(_index)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    @external(readonly=True)
    def get_listed_token_of_owner_by_index(self, _owner: Address, _index: int) -> int:
        """
        Returns token ID from _owner's listed tokens on index number _index. When used together with
        listed_token_count_by_owner(), this method can be used to iterate through tokens owned by _owner on client side.
        """
        result = VarDB(f'LISTED_{str(_owner)}_{str(_index)}', self._db, value_type=str).get()
        if result:
            return int(result)
        else:
            return 0

    @external
    @payable
    def purchase_token(self, _token_id: int):
        """
        Purchases a token listed for sale with given _token_id. The amount of ICX sent must match the token sale price,
        otherwise throws an error. When a correct amount is sent, the NFT will be sent from seller to buyer, and SCORE
        will send token's price worth of ICX to seller (minus fee, if applicable).
        """
        token_price = self.get_token_price(_token_id)
        if self.msg.value != token_price:
            revert(f'Sent ICX amount ({self.msg.value}) does not match token price ({token_price})')

        seller = self.ownerOf(_token_id)
        buyer = self.msg.sender
        self._delist_token(seller, _token_id)
        self._transfer(seller, buyer, _token_id)
        self.icx.transfer(seller, token_price)

        self.PurchaseToken(seller, buyer, _token_id)

    def _get_owner_listed_token_index(self, _address: Address, _index: int) -> int:
        return int(VarDB(f'LISTED_{str(_address)}_{str(_index)}', self._db, value_type=str).get())

    def _set_owner_listed_token_index(self, _address: Address, _index: int, _token_id: int):
        VarDB(f'LISTED_{str(_address)}_{str(_index)}', self._db, value_type=str).set(str(_token_id))

    def _remove_owner_listed_token_index(self, _address: Address, _index: int):
        VarDB(f'LISTED_{str(_address)}_{str(_index)}', self._db, value_type=str).remove()

    def _decrement_listed_token_count(self):
        self._total_listed_token_count.set(self._total_listed_token_count.get() - 1)

    def _increment_listed_token_count(self):
        self._total_listed_token_count.set(self._total_listed_token_count.get() + 1)

    def _get_listed_token_index_by_token_id(self, _token_id: int) -> int:
        result = VarDB(f'LISTED_TOKEN_{str(_token_id)}', self._db, value_type=int).get()
        if result:
            return result
        else:
            return 0

    def _set_listed_token_index(self, _index: int, _token_id: int):
        VarDB(f'LISTED_TOKEN_INDEX_{str(_index)}', self._db, value_type=int).set(_token_id)
        VarDB(f'LISTED_TOKEN_{str(_token_id)}', self._db, value_type=int).set(_index)

    def _remove_listed_token_index(self, _index: int):
        token_id = VarDB(f'INDEX_{str(_index)}', self._db, value_type=int).get()
        VarDB(f'LISTED_TOKEN_INDEX_{str(_index)}', self._db, value_type=int).remove()
        VarDB(f'LISTED_TOKEN_{str(token_id)}', self._db, value_type=int).remove()

    def _find_listed_token_index_by_token_id(self, _owner: Address, _token_id: int) -> int:
        # Returns listing index of a given _token_id of _owner. Returns 0 when no result.
        number_of_tokens = self.listed_token_count_by_owner(_owner)
        for x in range(1, number_of_tokens + 1):
            if self.get_listed_token_of_owner_by_index(_owner, x) == _token_id:
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
