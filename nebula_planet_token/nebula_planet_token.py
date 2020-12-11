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
    _IS_RESTRICTED_SALE = 'is_restricted_sale' # Boolean value that indicates if secondary token sales are restricted
    _METADATA_BASE_URL = 'metadata_base_url' # Base URL that is combined with provided token_URI when token gets minted
    _SALE_RECORD_COUNT = 'sale_record_count'  # Number of sale records (includes successful fixed price sales and all auctions)
    _SELLER_FEE = 'seller_fee' # Percentage that the marketplace takes from each token sale. Number is divided by 100000 to get the percentage value. (e.g 2500 equals 2.5%)

    _MAX_ITERATION_LOOP = 100
    _MINIMUM_BID_INCREMENT = 5
    _ICX_TO_LOOPS = 1000000000000000000

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
        self._is_paused = VarDB(self._IS_PAUSED, db, value_type=bool)
        self._is_restricted_sale = VarDB(self._IS_RESTRICTED_SALE, db, value_type=bool)
        self._metadataBaseURL = VarDB(self._METADATA_BASE_URL, db, value_type=str)
        self._sale_record_count = VarDB(self._SALE_RECORD_COUNT, db, value_type=int)
        self._seller_fee = VarDB(self._SELLER_FEE, db, value_type=int)

        self._db = db

    def on_install(self) -> None:
        super().on_install()
        self._director.set(self.msg.sender)
        self._treasurer.set(self.msg.sender)
        self._minter.set(self.msg.sender)
        self._is_paused.set(False)
        self._is_restricted_sale.set(False)
        self._metadataBaseURL.set('')
        self._seller_fee.set(0) # equals 2.5%

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "NebulaPlanetToken"

    @external(readonly=True)
    def symbol(self) -> str:
        return "NPT"

    @payable
    def fallback(self):
        self.DepositReceived(self.msg.sender)

    def _check_that_sender_is_nft_owner(self, _owner: Address):
        if self.msg.sender != _owner:
            revert("You do not own this NFT")

    def _check_that_contract_is_unpaused(self):
        if self._is_paused.get() and not self.msg.sender == self._minter.get():
            revert("Contract is currently paused")

    @external
    def withdraw(self, amount: int):
        """
        Used to withdraw funds from the contract.
        Throws if sender is not the Treasurer.
        """
        treasurer = self._treasurer.get()
        if treasurer != self.msg.sender:
            revert('You are not allowed to withdraw from this contract')
        self.icx.transfer(treasurer, amount)

    @external
    def assign_treasurer(self, _address: Address):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._treasurer.set(_address)
        self.AssignRole("Treasurer", _address)

    @external
    def assign_minter(self, _address: Address):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._minter.set(_address)
        self.AssignRole("Minter", _address)

    @external
    def pause_contract(self):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to pause the contract')
        if self._is_paused.get():
            revert('Contract is already paused')
        self._is_paused.set(True)

    @external
    def unpause_contract(self):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to unpause the contract')
        if not self._is_paused.get():
            revert('Contract is already unpaused')
        self._is_paused.set(False)

    @external
    def restrict_sale(self):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to toggle sale restriction')
        if self._is_restricted_sale.get():
            revert('Token sale is already restricted')
        self._is_restricted_sale.set(True)

    @external
    def unrestrict_sale(self):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to toggle sale restriction')
        if not self._is_restricted_sale.get():
            revert('Token sale is already without restrictions')
        self._is_restricted_sale.set(False)

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
        if self._is_restricted_sale.get():
            revert("Approving tokens is currently disabled")
        owner = self.ownerOf(_tokenId)
        if _to == owner:
            revert("Can't approve to yourself.")
        self._check_that_sender_is_nft_owner(owner)

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
        self._check_that_contract_is_unpaused()
        self._check_that_token_is_not_auctioned(_tokenId)
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
        self._check_that_contract_is_unpaused()

        self._check_that_token_is_not_auctioned(_tokenId)

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

        baseURL = self._metadataBaseURL.get()

        return baseURL + token_URI

    @external
    def set_token_URI(self, _token_id: int, _token_URI: str):
        """
        Set token URI for a given token. Throws if a token does not exist.
        """
        if self._minter.get() != self.msg.sender:
            revert('You do not have permission set token URI')
        self._set_token_URI(_token_id, _token_URI)

    def _set_token_URI(self, _token_id: int, _token_URI: str):
        self._ensure_positive(_token_id)
        self._token_URIs[_token_id] = _token_URI

    def _remove_token_URI(self, _token_id: int):
        del self._token_URIs[_token_id]

    @external
    def set_metadata_base_URL(self, _base_URL: str):
        if self._minter.get() != self.msg.sender:
            revert('You do not have permission set metadata base URL')
        self._metadataBaseURL.set(_base_URL)

    @external
    def set_seller_fee(self, _new_fee: int):
        if self._director.get() != self.msg.sender:
            revert('You do not have permission set seller fee')
        self._seller_fee.set(_new_fee)

    @external(readonly=True)
    def seller_fee(self) -> int:
        return self._seller_fee.get()

    # ================================================
    #  Enumerable extension
    # ================================================

    def _token(self, _token_id: int) -> VarDB:
        return VarDB(f'TOKEN_{str(_token_id)}', self._db, value_type=int)

    def _token_index(self, _index: int) -> VarDB:
        return VarDB(f'INDEX_{str(_index)}', self._db, value_type=int)

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
        result = self._token_index(_index).get()
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
        result = self._token(_token_id).get()
        if result:
            return result
        else:
            return 0

    def _set_token_index(self, _index: int, _token_id: int):
        self._token_index(_index).set(_token_id)
        self._token(_token_id).set(_index)

    def _remove_token_index(self, _index: int):
        token_id = self._token_index(_index).get()
        self._token_index(_index).remove()
        self._token(token_id).remove()

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

    def _check_that_token_is_not_listed(self, _token_id):
        if self._listed_token_prices[str(_token_id)] != 0:
            revert("Token is already listed")

    def _check_that_token_is_not_auctioned(self, _token_id):
        if self._listed_token_prices[str(_token_id)] == -1:
            revert("Token is currently on auction")

    def _check_that_token_is_on_auction(self, _token_id):
        if self._listed_token_prices[str(_token_id)] != -1:
            revert("Token is not on auction")

    def _check_that_price_is_positive(self, _price):
        if _price < 0:
            revert("Price can not be negative")
        if _price == 0:
            revert("Price can not be zero")

    def _check_that_sale_is_not_restricted(self):
        if self._is_restricted_sale.get() and not self.msg.sender == self._minter.get():
            revert("Listing tokens is currently disabled")

    @external
    def list_token(self, _token_id: int, _price: int):
        """
        Lists token for sale. Throws if sender does not own the token.
        Throws if token price is not positive.
        """
        owner = self.ownerOf(_token_id)
        sender = self.msg.sender
        self._check_that_sale_is_not_restricted()
        self._check_that_contract_is_unpaused()
        self._check_that_sender_is_nft_owner(owner)
        self._check_that_price_is_positive(_price)
        self._check_that_token_is_not_auctioned(_token_id)
        self._check_that_token_is_not_listed(_token_id)

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
        if self.msg.sender != owner and self.msg.sender != self._director.get(): # Token can also be delisted by Director, although this should be done rarely and with good reason.
            revert("You do not own this NFT")
        self._check_that_token_is_not_auctioned(_token_id)

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
        self._listed_token_prices.remove(str(_tokenId))

    @external(readonly=True)
    def get_listed_token_by_index(self, _index: int) -> int:
        """ Returns token ID on _index'th position from all tokens listed for sale. Can be used iterate through
        all valid tokens that are for sale. """
        result = self._listed_token_index(_index).get()
        if result:
            return result
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
        self._check_that_contract_is_unpaused()

        if not self.msg.value > 0:
            revert(f'Sent ICX amount needs to be greater than 0')
        token_price = self.get_token_price(_token_id)
        if self.msg.value != token_price:
            revert(f'Sent ICX amount ({self.msg.value}) does not match token price ({token_price})')

        seller = self.ownerOf(_token_id)
        buyer = self.msg.sender
        self._delist_token(seller, _token_id)
        self._transfer(seller, buyer, _token_id)

        fee = self._calculate_seller_fee(token_price)

        self.icx.transfer(seller, int(token_price - fee))
        self.icx.transfer(self.address, int(fee))

        self._create_sale_record(_token_id=_token_id,
                                 _type='sale_success',
                                 _seller=seller,
                                 _buyer=buyer,
                                 _starting_price=token_price,
                                 _final_price=token_price,
                                 _end_time=self.now())

        self.PurchaseToken(seller, buyer, _token_id)

    def _calculate_seller_fee(self, price: int) -> int:
        return price * self._seller_fee.get() / 100000

    def _listed_token(self, _token_id: int) -> VarDB:
        return VarDB(f'LISTED_TOKEN_{str(_token_id)}', self._db, value_type=int)

    def _listed_token_index(self, _index: int) -> VarDB:
        return VarDB(f'LISTED_TOKEN_INDEX_{str(_index)}', self._db, value_type=int)

    def _owner_listed_token_index(self, _address: Address, _index: int) -> VarDB:
        return VarDB(f'LISTED_{str(_address)}_{str(_index)}', self._db, value_type=str)

    @external(readonly=True)
    def get_listed_token_of_owner_by_index(self, _owner: Address, _index: int) -> int:
        """
        Returns token ID from _owner's listed tokens on index number _index. When used together with
        listed_token_count_by_owner(), this method can be used to iterate through tokens owned by _owner on client side.
        """
        result = self._owner_listed_token_index(_owner, _index).get()
        if result:
            return int(result)
        else:
            return 0

    def _set_owner_listed_token_index(self, _address: Address, _index: int, _token_id: int):
        self._owner_listed_token_index(_address, _index).set(str(_token_id))

    def _remove_owner_listed_token_index(self, _address: Address, _index: int):
        self._owner_listed_token_index(_address, _index).remove()

    def _decrement_listed_token_count(self):
        self._total_listed_token_count.set(self._total_listed_token_count.get() - 1)

    def _increment_listed_token_count(self):
        self._total_listed_token_count.set(self._total_listed_token_count.get() + 1)

    def _get_listed_token_index_by_token_id(self, _token_id: int) -> int:
        result = self._listed_token(_token_id).get()
        if result:
            return result
        else:
            return 0

    def _set_listed_token_index(self, _index: int, _token_id: int):
        self._listed_token_index(_index).set(_token_id)
        self._listed_token(_token_id).set(_index)

    def _remove_listed_token_index(self, _index: int):
        token_id = self._listed_token_index(_index).get()
        self._listed_token_index(_index).remove()
        self._listed_token(token_id).remove()

    def _find_listed_token_index_by_token_id(self, _owner: Address, _token_id: int) -> int:
        # Returns listing index of a given _token_id of _owner. Returns 0 when no result.
        number_of_tokens = self.listed_token_count_by_owner(_owner)
        for x in range(1, number_of_tokens + 1):
            if self.get_listed_token_of_owner_by_index(_owner, x) == _token_id:
                return x
        return 0

    # ================================================
    #  Auction
    # ================================================

    def _auction_item_start_time(self, _token_id: int) -> VarDB:
        return VarDB(f'AUCTION_{str(_token_id)}_START_TIME', self._db, value_type=int)

    def _auction_item_end_time(self, _token_id: int) -> VarDB:
        return VarDB(f'AUCTION_{str(_token_id)}_END_TIME', self._db, value_type=int)

    def _auction_item_starting_price(self, _token_id: int) -> VarDB:
        return VarDB(f'AUCTION_{str(_token_id)}_STARTING_PRICE', self._db, value_type=int)

    def _auction_item_current_bid(self, _token_id: int) -> VarDB:
        return VarDB(f'AUCTION_{str(_token_id)}_CURRENT_BID', self._db, value_type=int)

    def _auction_item_highest_bidder(self, _token_id: int) -> VarDB:
        return VarDB(f'AUCTION_{str(_token_id)}_HIGHEST_BIDDER', self._db, value_type=Address)

    @external
    def create_auction(self,  _token_id: int, _starting_price: int, _duration_in_hours: int):
        """
        Creates an English auction for given _token_id. Maximum auction duration is 336 hours (2 weeks).
        Throws if sale is restricted or contract is paused. Throws when token is already listed.
        Throws when sender does not own the token. Throws when starting price is not positive.
        """
        owner = self.ownerOf(_token_id)
        sender = self.msg.sender
        self._check_that_sale_is_not_restricted()
        self._check_that_contract_is_unpaused()
        self._check_that_sender_is_nft_owner(owner)
        self._check_that_token_is_not_auctioned(_token_id)
        self._check_that_token_is_not_listed(_token_id)
        self._check_that_price_is_positive(_starting_price)

        if _duration_in_hours > 336:
            revert("Auction duration can not be longer than two weeks")

        self._increment_listed_token_count()
        self._set_listed_token_index(self._total_listed_token_count.get(), _token_id)
        self._listed_token_prices[str(_token_id)] = -1
        self._owner_listed_token_count[sender] += 1
        self._set_owner_listed_token_index(sender, self._owner_listed_token_count[sender], _token_id)

        start_time = self.now()
        end_time = start_time + _duration_in_hours * 3600 * 1000 * 1000

        self._auction_item_start_time(_token_id).set(start_time)
        self._auction_item_end_time(_token_id).set(end_time)
        self._auction_item_starting_price(_token_id).set(_starting_price)

    def _finish_auction(self, _token_id):
        self._auction_item_start_time(_token_id).remove()
        self._auction_item_end_time(_token_id).remove()
        self._auction_item_starting_price(_token_id).remove()
        self._auction_item_current_bid(_token_id).remove()
        self._auction_item_highest_bidder(_token_id).remove()

        seller = self.ownerOf(_token_id)
        self._delist_token(seller, _token_id)

    @external(readonly=True)
    def get_auction_info(self, _token_id: int) -> dict:
        self._check_that_token_is_on_auction(_token_id)
        end_time = self._auction_item_end_time(_token_id).get()
        starting_price = self._auction_item_starting_price(_token_id).get()
        current_bid = self._auction_item_current_bid(_token_id).get()

        bid_increment: int
        if current_bid:
            bid_increment = current_bid * self._MINIMUM_BID_INCREMENT / 100
        else:
            bid_increment = starting_price * self._MINIMUM_BID_INCREMENT / 100

        auction_item = {
            "status": self._auction_status(_token_id),
            "start_time": self._auction_item_start_time(_token_id).get(),
            "end_time": end_time,
            "starting_price": starting_price,
            "current_bid": current_bid,
            "minimum_bid_increment": bid_increment,
            "highest_bidder": self._auction_item_highest_bidder(_token_id).get(),
        }
        return auction_item

    def _auction_status(self, _token_id) -> str:
        """
        Returns auction status as string value:
        'active' for ongoing auctions.
        'unsold' for finished auctions where no bid was placed. User can return item to them to finish the auction.
        'unclaimed' for finished auctions where a bid was placed, but auctioned item is not yet claimed
        """
        self._check_that_token_is_on_auction(_token_id)

        end_time = self._auction_item_end_time(_token_id).get()
        current_bid = self._auction_item_current_bid(_token_id).get()
        if self.now() < end_time:
            return 'active'
        else:
            if current_bid:
                return 'unclaimed'
            else:
                return 'unsold'

    @external
    @payable
    def place_bid(self, _token_id: int):
        """
        Used for bidding on auction. Bid amount has to exceed previous bid + minimum bid increment.
        Throws if auction has ended.
        Throws if bid amount is less than minimum bid (previous bid + minimum increment).
        """
        self._check_that_contract_is_unpaused()
        self._check_that_token_is_on_auction(_token_id)

        # Check if auction is live
        end_time = self._auction_item_end_time(_token_id).get()
        if self.now() > end_time:
            revert('Can not place a bid. The auction has already ended.')

        # Check if amount is equal to or greater than current_bid + minimum_bid_increment
        starting_price = self._auction_item_starting_price(_token_id).get()
        last_bid = self._auction_item_current_bid(_token_id).get()
        minimum_bid = starting_price
        if last_bid:
            minimum_bid = last_bid + last_bid * self._MINIMUM_BID_INCREMENT / 100
        if self.msg.value < minimum_bid:
            revert(
                f'Your bid {str(self.msg.value / self._ICX_TO_LOOPS)} is lower than minimum bid amount {str(minimum_bid / self._ICX_TO_LOOPS)}')

        last_bidder = self._auction_item_highest_bidder(_token_id).get()

        self._auction_item_highest_bidder(_token_id).set(self.msg.sender)
        self._auction_item_current_bid(_token_id).set(self.msg.value)

        # If bid existed, return last bid to previous high bidder
        if last_bidder:
            self.icx.transfer(last_bidder, last_bid)

        # When a last minute bid is place, the auction end time will be extended by one minute.
        if self.now() > end_time - 1000 * 1000 * 60:
            self._auction_item_end_time(_token_id).set(end_time + 1000 * 1000 * 120)

    @external
    def finalize_auction(self, _token_id: int):
        """
        Method used for sending auctioned item to the winner of the auction and ICX to seller.
        Callable by auction winner or seller.
        Throws if auction does not exist. Throws if auction has not ended.
        Throws if auction item has already been claimed. Throws if auction bid price was not met.
        """
        seller = self.ownerOf(_token_id)
        buyer = self._auction_item_highest_bidder(_token_id).get()
        auction_status = self._auction_status(_token_id)
        self._check_that_token_is_on_auction(_token_id)
        if auction_status != 'unclaimed':
            revert(f'Auction needs to have status: unclaimed. Current status: {auction_status}')
        if not (self.msg.sender == seller or self.msg.sender == buyer):
            revert("Only seller or buyer can finalize the auction")

        last_bid = self._auction_item_current_bid(_token_id).get()

        # Create a record for successful auction
        auction = self.get_auction_info(_token_id)
        self._create_sale_record(_token_id=_token_id,
                                 _type='auction_unsold',
                                 _seller=seller,
                                 _buyer=buyer,
                                 _starting_price=auction['starting_price'],
                                 _final_price=last_bid,
                                 _start_time=auction['start_time'],
                                 _end_time=auction['end_time'])

        self._transfer(seller, buyer, _token_id)
        fee = self._calculate_seller_fee(last_bid)
        self.icx.transfer(seller, int(last_bid - fee))

        self._finish_auction(_token_id)

    @external
    def return_unsold_item(self, _token_id: int):
        """
        Method used for sending unsold auctioned item back to owner.
        Throws if auction does not exist. Throws if auction has not ended.
        Throws if auction item has already been claimed. Throws if auction bid price was not met.
        """
        owner = self.ownerOf(_token_id)
        self._check_that_sender_is_nft_owner(owner)
        self._check_that_token_is_on_auction(_token_id)
        auction_status = self._auction_status(_token_id)
        if auction_status != 'unsold':
            revert(f'Auction needs to have status: unsold. Current status: {auction_status}')


        # Create a record for unsold auction
        auction = self.get_auction_info(_token_id)
        self._create_sale_record(_token_id=_token_id,
                                 _type='auction_unsold',
                                 _seller=owner,
                                 _starting_price=auction['starting_price'],
                                 _start_time=auction['start_time'],
                                 _end_time=auction['end_time'])
        self._finish_auction(_token_id)

    @external
    def cancel_auction(self, _token_id: int):
        """
        Method used for cancelling auctions that don't have a bid yet. Auction item is returned to the owner.
        Throws if auction does not exist. Throws if auction has not ended.
        """
        owner = self.ownerOf(_token_id)
        self._check_that_token_is_on_auction(_token_id)
        if self._auction_status(_token_id) != 'active':
            revert('Auction needs to be active to get cancelled.')
        if self.msg.sender == self._director.get(): # Auction can also be cancelled by Director.
            pass
        else:
            self._check_that_sender_is_nft_owner(owner)
            last_bid = self._auction_item_current_bid(_token_id).get()

            if last_bid and self.msg.sender:
                revert('Bid has already been made. Auction cannot be cancelled.')

        # Create a record for cancelled auction
        auction = self.get_auction_info(_token_id)
        self._create_sale_record(_token_id = _token_id,
                                 _type = 'auction_cancelled',
                                 _seller = owner,
                                 _starting_price = auction['starting_price'],
                                 _start_time = auction['start_time'],
                                 _end_time = self.now())
        self._finish_auction(_token_id)

    # ================================================
    #  Sale records
    # ================================================

    def _record_token_id(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_TOKEN_ID', self._db, value_type=int)

    def _record_type(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_TYPE', self._db, value_type=str)

    def _record_seller(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_SELLER', self._db, value_type=Address)

    def _record_buyer(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_BUYER', self._db, value_type=Address)

    def _record_starting_price(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_STARTING_PRICE', self._db, value_type=int)

    def _record_final_price(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_FINAL_PRICE', self._db, value_type=int)

    def _record_start_time(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_START_TIME', self._db, value_type=int)

    def _record_end_time(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_END_TIME', self._db, value_type=int)

    def _records_count(self) -> int:
        return self._sale_record_count.get()

    def _create_sale_record(self,
                            _token_id: int,
                            _type: str,
                            _seller: Address,
                            _end_time: int,
                            _buyer: Address = None,
                            _starting_price: int = 0,
                            _final_price: int = 0,
                            _start_time: int = 0
                            ):
        record_id = self._records_count() + 1
        self._sale_record_count.set(record_id)

        self._record_token_id(record_id).set(_token_id)
        self._record_type(record_id).set(_type)
        self._record_seller(record_id).set(_seller)
        if _buyer:
            self._record_buyer(record_id).set(_buyer)
        if _starting_price:
            self._record_starting_price(record_id).set(_starting_price)
        if _final_price:
            self._record_final_price(record_id).set(_final_price)
        if _start_time:
            self._record_start_time(record_id).set(_start_time)
        if _end_time:
            self._record_end_time(record_id).set(_end_time)

    @external(readonly=True)
    def get_sale_record(self, _record_id: int) -> dict:
        """
        Method is used for getting historic records of sales and auctions.
        Includes successful fixed price sales and auctions (successful, cancelled, unsold)
        """
        if _record_id > self._sale_record_count.get():
            revert('Sale record does not exist')
        record = {
            "record_id": _record_id,
            "token_id": self._record_token_id(_record_id).get(),
            "type": self._record_type(_record_id).get(),
            "seller": self._record_seller(_record_id).get(),
            "buyer": self._record_buyer(_record_id).get(),
            "starting_price": self._record_starting_price(_record_id).get(),
            "final_price": self._record_final_price(_record_id).get(),
            "start_time": self._record_start_time(_record_id).get(),
            "end_time": self._record_end_time(_record_id).get(),
        }
        return record

    @external(readonly=True)
    def sale_record_count(self) -> int:
        return self._sale_record_count.get()

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

    @eventlog(indexed=1)
    def DepositReceived(self, _sender: Address):
        pass