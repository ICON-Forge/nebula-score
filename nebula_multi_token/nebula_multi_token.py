from iconservice import *
from .interfaces import *
ZERO_ADDRESS = Address.from_prefix_and_int(AddressPrefix.EOA, 0)

def require(condition: bool, message: str):
    if not condition:
        revert(message)

class IRC31ReceiverInterface(InterfaceScore):
    @interface
    def setOriginator(self, _origin: Address, _approved: bool):
        pass

    @interface
    def onIRC31Received(self, _operator: Address, _from: Address, _id: int, _value: int, _data: bytes):
        pass

    @interface
    def onIRC31BatchReceived(self, _operator: Address, _from: Address, _ids: List[int], _values: List[int], _data: bytes):
        pass


class NebulaMultiToken(IconScoreBase, IRC31Basic, IRC31MintBurn):
    _OWNED_TOKEN_COUNT = 'owned_token_count'  # Track token count per address
    _OWNED_TOKEN_COUNT_BY_ID = 'owned tokens'  # Track the owned tokens per address, per tokenID

    _TOTAL_SUPPLY = 'total_supply'  # Tracks total number of valid tokens (excluding ones with zero address)
    _TOTAL_SUPPLY_TOKEN = 'total_supply_token'  # Tracks total supply for each token (excluding ones with zero address)
    #_LISTED_TOKEN_PRICES = 'listed_token_prices'  # Tracks listed token prices against token IDs
    #_OWNER_LISTED_TOKEN_COUNT = 'owner_listed_count'  # Tracks number of listed tokens against token owners
    #_OWNER_LISTED_TOKEN_BALANCE = 'owner_listed_balance'  # Tracks the balance of listed tokens by token owners
    #_TOTAL_LISTED_TOKEN_COUNT = 'total_listed_count'  # Tracks total number of listed tokens
    #_OWNER_LISTED_TOKENS_COUNT = 'owner_listed_count'  # Tracks number of listed token index against token owners
    _DIRECTOR = 'director'  # Role responsible for assigning other roles.
    _TREASURER = 'treasurer'  # Role responsible for transferring money to and from the contract
    _MINTER = 'minter'  # Role responsible for minting and burning tokens
    _IS_PAUSED = 'is_paused' # Boolean value that indicates whether a contract is paused
    _IS_RESTRICTED_SALE = 'is_restricted_sale' # Boolean value that indicates if secondary token sales are restricted
    _METADATA_BASE_URL = 'metadata_base_url' # Base URL that is combined with provided token_URI when token gets minted
    _SELLER_FEE = 'seller_fee' # Percentage that the marketplace takes from each token sale. Number is divided by 100000 to get the percentage value. (e.g 2500 equals 2.5%)
    _SALE_RECORD_COUNT = 'sale_record_count'  # Number of sale records (includes successful fixed price sales and all auctions)
    
    # Marketplace - Sell Order
    _LISTED_TOKEN_BALANCE_BY_OWNER = "listed_token_balance_by_owner" #How many tokens of the same id are locked for each tokenid/address 
    _LISTED_SALES_PER_TOKENID_BY_OWNER = "listed_sales_per_tokenid_by_owner" #How many sales per tokenid does an owner have 
    _NUMBER_SALE_ORDERS_PER_TOKENID = "number_sale_orders_per_tokenid" #Keeps the number of active sale orders per token id
    _MP_PRICE_LIST = "market_place_price_list" # Keeps the price for all active offers
    _MP_QUANTITY_LIST = "market_place_quantity_list" # Keeps the quantity of tokens on sale for all active offers
    _INDEX_MAPPING = "index_mapping" # Maps the global tokenID index with the user specifc index
    #_LISTED_TOKEN_TYPES_BY_OWNER = "listed_token_types_by_owner" # Number of different token types listed by address
    _NUMBER_SELL_ORDERS_BY_OWNER = "number_sell_orders_by_owner" # number of sell order listed by an address
    _ADDRESS_INDEX_TO_TOKENID_INDEX = "address_index_to_tokenid_index" # Map the user sell order index to the tokenid sell order index

    # Marketplace - Buy Order
    _MP_BUY_PRICE_LIST = "market_place_buy_price_list" # Keeps the price for all active buy offers
    _MP_BUY_QUANTITY_LIST = "market_place_buy_quantity_list" # Keeps the quantity of tokens on sale for all active offers
    _NUMBER_BUY_ORDERS_PER_TOKENID = "number_buy_orders_per_tokenid" #Keeps the number of active buy orders per token id
    _NUMBER_BUY_ORDERS_BY_OWNER = "number_buy_orders_by_owner" # number of buy orders listed by an address 
    _LISTED_PURCHASES_PER_TOKENID_BY_OWNER = "listed_purchases_per_tokenid_by_owner" #How many purchase offers per tokenid does an owner have
    _INDEX_MAPPING_PURCHASE = "index_mapping_purchase" # Maps the global tokenID index with the user specifc index for buy orders
    _ADDRESS_INDEX_TO_TOKENID_INDEX_PURCHASE = "address_index_to_tokenid_index_purchase" # Map the user sell order index to the tokenid sell order index for buy orders

    def __init__(self, db: 'IconScoreDatabase') -> None:
        super().__init__(db)
        # id => (owner => balance)
        self._owned_token_count = DictDB(self._OWNED_TOKEN_COUNT, db, value_type=int) #[address]->count
        self._owned_token_count_by_id = DictDB(self._OWNED_TOKEN_COUNT_BY_ID, db, value_type=int, depth=2) #[address][tokenID]->count ( _balances )

        # owner => (operator => approved)
        self._operatorApproval = DictDB('approval', db, value_type=bool, depth=2)
        # id => token URI
        self._token_URIs = DictDB('token_uri', db, value_type=str)
        self._total_number_tokens = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._total_supply_per_token = DictDB(self._TOTAL_SUPPLY_TOKEN, db, value_type=int)
        self._tokenNames = DictDB('token_name', db, value_type=str)
        self._tokenSymbol = DictDB('token_symbol', db, value_type=str)
        #self._total_listed_token_count = VarDB(self._TOTAL_LISTED_TOKEN_COUNT, db, value_type=int)
        #self._owner_listed_token_count = DictDB(self._OWNER_LISTED_TOKEN_COUNT, db, value_type=int)
        #self._owner_listed_token_balance = DictDB(self._OWNER_LISTED_TOKEN_BALANCE, db, value_type=int, depth=2) # [address][tokenID]
        #self._owner_listed_tokens_count = DictDB(self._OWNER_LISTED_TOKENS_COUNT, db, value_type=int, depth=2) # [address][tokenID]
        self._is_paused = VarDB(self._IS_PAUSED, db, value_type=bool)

        self._is_restricted_sale = VarDB(self._IS_RESTRICTED_SALE, db, value_type=bool)
        #self._listed_token_prices = DictDB(self._LISTED_TOKEN_PRICES, db, value_type=int, depth=2) # [address][tokenID]
        self._director = VarDB(self._DIRECTOR, db, value_type=Address)
        self._treasurer = VarDB(self._TREASURER, db, value_type=Address)
        self._minter = VarDB(self._MINTER, db, value_type=Address)
        self._minters = DictDB(self._MINTER, db, value_type=Address)

        self._metadataBaseURL = VarDB(self._METADATA_BASE_URL, db, value_type=str)
        self._sale_record_count = VarDB(self._SALE_RECORD_COUNT, db, value_type=int)
        self._seller_fee = VarDB(self._SELLER_FEE, db, value_type=int)

        # Marketplace - Sell Order
        self._listed_token_balance_by_owner = DictDB(self._LISTED_TOKEN_BALANCE_BY_OWNER, db, value_type=int, depth=2)# [address][tokenID]
        self._listed_sales_per_tokenid_by_owner = DictDB(self._LISTED_SALES_PER_TOKENID_BY_OWNER, db, value_type=int, depth=2)# [address][tokenID]
        self._number_sale_orders_per_tokenid = DictDB(self._NUMBER_SALE_ORDERS_PER_TOKENID, db, value_type=int)# [tokenID]
        self._mp_price_list = DictDB(self._MP_PRICE_LIST, db, value_type=int, depth=2) # [tokenID][index]
        self._mp_quantity_list = DictDB(self._MP_QUANTITY_LIST, db, value_type=int, depth=2) # [tokenID][index]
        self._index_mapping = DictDB(self._INDEX_MAPPING, db, value_type=str) # [tokenID_index] = [address_tokenID_index]
        #self._listed_token_types_by_owner = DictDB(self._LISTED_TOKEN_TYPES_BY_OWNER, db, value_type=int) #[address]
        self._number_sell_orders_per_owner = DictDB(self._NUMBER_SELL_ORDERS_BY_OWNER, db, value_type=int) #[address]
        self._address_index_to_tokenid_index = DictDB(self._ADDRESS_INDEX_TO_TOKENID_INDEX, db, value_type=str) #[address_index]->[tokenID_index]

        # Marketplace - Buy Order
        self._mp_buy_price_list = DictDB(self._MP_BUY_PRICE_LIST, db, value_type=int, depth=2) # [tokenID][index]
        self._mp_buy_quantity_list = DictDB(self._MP_BUY_QUANTITY_LIST, db, value_type=int, depth=2) # [tokenID][index]
        self._number_buy_orders_per_tokenid = DictDB(self._NUMBER_BUY_ORDERS_PER_TOKENID, db, value_type=int)# [tokenID]
        self._number_buy_orders_per_owner = DictDB(self._NUMBER_BUY_ORDERS_BY_OWNER, db, value_type=int) #[address]
        self._listed_purchases_per_tokenid_by_owner = DictDB(self._LISTED_PURCHASES_PER_TOKENID_BY_OWNER, db, value_type=int, depth=2)# [address][tokenID]
        self._index_mapping_purchase = DictDB(self._INDEX_MAPPING_PURCHASE, db, value_type=str) # [tokenID_index] = [address_tokenID_index]
        self._address_index_to_tokenid_index_purchase = DictDB(self._ADDRESS_INDEX_TO_TOKENID_INDEX_PURCHASE, db, value_type=str) #[address_index]->[tokenID_index]
        
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
    def tokenName(self, _id: int) -> str:
        """
        Returns a Name for a given token ID.
        :param _id: ID of the token
        :return: the Name string
        """
        return self._tokenNames[_id]
    
    @external(readonly=True)
    def tokenSymbol(self, _id: int) -> str:
        """
        Returns a Symbol  for a given token ID.
        :param _id: ID of the token
        :return: the Symbol string
        """
        return self._tokenSymbol[_id]

    @payable
    def fallback(self):
        self.DepositReceived(self.msg.sender)

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
    def balanceOf(self, _owner: Address, _id: int) -> int:
        """
        Returns the balance of the owner's tokens.
        :param _owner: the address of the token holder
        :param _id: ID of the token
        :return: the _owner's balance of the token type requested
        """
        if _owner is None or self._is_zero_address(_owner):
            revert("Invalid owner")
        return self._owned_token_count_by_id[_owner][_id]

    @external(readonly=True)
    def balanceOfTokenClasses(self, _owner: Address) -> int:
        """
        Returns the balance of the owner's token classes.
        :param _owner: the address of the token holder
        :return: the _owner's balance of token classes
        """
        if _owner is None or self._is_zero_address(_owner):
            revert("Invalid owner")
        return self._owned_token_count[_owner]

    @external(readonly=True)
    def balanceOfBatch(self, _owners: List[Address], _ids: List[int]) -> List[int]:
        """
        Returns the balance of multiple owner/id pairs.
        :param _owners: the addresses of the token holders
        :param _ids: IDs of the tokens
        :return: the list of balance (i.e. balance for each owner/id pair)
        """
        require(len(_owners) == len(_ids), "owner/id pairs mismatch")

        balances = []
        for i in range(len(_owners)):
            balances.append(self._owned_token_count_by_id[_ids[i]][_owners[i]])
        return balances

    @external
    def transfer(self, _to: Address, _tokenId: int, _value: int):
        """
        Transfers the ownership of your NFT to another address,
        and MUST fire the Transfer event. Throws unless self.msg.sender
        is the current owner. Throws if _to is the zero address.
        Throws if _tokenId is not a valid NFT.
        """
        _from =  self.msg.sender

        require(0 <= _value <= self._owned_token_count_by_id[_from][_tokenId], "Insufficient funds")

        self._check_that_contract_is_unpaused()

        # Check that tokens are not locked in a sell order
        balance = self.balanceOf(_from, _tokenId)
        require(balance - self._get_listed_token_balance_by_owner(_from, _tokenId) >= _value, "Number of tokens is less than available tokens.")
       
        self._transfer(self.msg.sender, _to, _tokenId, _value)

    def _transfer(self, _from: Address, _to: Address, _token_id: int, _value: int):
        require(_to != ZERO_ADDRESS, "You can't transfer to a zero address")

        #self._clear_approval(_token_id)
        #if self.get_token_price(_token_id):
        #    self._delist_token(_from, _token_id)
        self._remove_tokens_from(_from, _token_id, _value)
        self._add_tokens_to(_to, _token_id, _value)
        self.TransferSingle(_from, _from, _to, _token_id, _value)
        Logger.debug(f'TransferSingle({_from}, {_from}, {_to}, {_token_id}, {_value}, TAG)')

    @external
    def transferFrom(self, _from: Address, _to: Address, _id: int, _value: int, _data: bytes = None):
        """
        Transfers `_value` amount of an token `_id` from one address to another address,
        and must emit `TransferSingle` event to reflect the balance change.
        When the transfer is complete, this method must invoke `onIRC31Received(Address,Address,int,int,bytes)` in `_to`,
        if `_to` is a contract. If the `onIRC31Received` method is not implemented in `_to` (receiver contract),
        then the transaction must fail and the transfer of tokens should not occur.
        If `_to` is an externally owned address, then the transaction must be sent without trying to execute
        `onIRC31Received` in `_to`.
        Additional `_data` can be attached to this token transaction, and it should be sent unaltered in call
        to `onIRC31Received` in `_to`. `_data` can be empty.
        Throws unless the caller is the current token holder or the approved address for the token ID.
        Throws if `_from` does not have enough amount to transfer for the token ID.
        Throws if `_to` is the zero address.

        :param _from: source address
        :param _to: target address
        :param _id: ID of the token
        :param _value: the amount of transfer
        :param _data: additional data that should be sent unaltered in call to `_to`
        """
        self._check_that_contract_is_unpaused()
        require(_to != ZERO_ADDRESS, "_to must be non-zero")
        require(_from == self.msg.sender or self.isApprovedForAll(_from, self.msg.sender),
                "You don't have permission to transfer this NFT")
        require(0 <= _value <= self._owned_token_count_by_id[_from][_id], "Insufficient funds")

        # Balance and token checks
        require(self._is_owner_of_token(_from, _id) == True, "Sender does not own the token.")
        balance = self.balanceOf(_from, _id)
        require(balance - self._get_listed_token_balance_by_owner(_from, _id) >= _value, "Number of tokens is less than available tokens.")      

        self._transfer(_from, _to, _id, _value)

        if _to.is_contract:
            # call `onIRC31Received` if the recipient is a contract
            recipient_score = self.create_interface_score(_to, IRC31ReceiverInterface)
            recipient_score.onIRC31Received(self.msg.sender, _from, _id, _value,
                                            b'' if _data is None else _data)
    
    @eventlog(indexed=3)
    def TransferSingle(self, _operator: Address, _from: Address, _to: Address, _id: int, _value: int):
        """
        Must trigger on any successful token transfers, including zero value transfers as well as minting or burning.
        When minting/creating tokens, the `_from` must be set to zero address.
        When burning/destroying tokens, the `_to` must be set to zero address.

        :param _operator: the address of an account/contract that is approved to make the transfer
        :param _from: the address of the token holder whose balance is decreased
        :param _to: the address of the recipient whose balance is increased
        :param _id: ID of the token
        :param _value: the amount of transfer
        """
        pass

    @external
    def transferFromBatch(self, _from: Address, _to: Address, _ids: List[int], _values: List[int], _data: bytes = None):
        # TODO!
        pass


    @external
    def mint(self, _id: int, _supply: int, _uri: str):
        """
        Creates a new token type and assigns _initialSupply to creator
        """
        #self._ensure_positive(_id)
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to mint tokens')
        require(self._minters[_id] is None, "Token is already minted")
        require(_supply > 0, "Supply should be positive")
        require(len(_uri) > 0, "Uri should be set")

        self._minters[_id] = self.msg.sender
        self._mint(self.msg.sender, _id, _supply, _uri)

    @external
    def mint_to(self, _to: Address, _id: int, _supply: int, _uri: str):
        """
        Creates a new token type and assigns _initialSupply to _to
        """
        self._ensure_positive(_id)
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to mint tokens')
        require(self._minters[_id] is None, "Token is already minted")
        require(_supply > 0, "Supply should be positive")
        require(len(_uri) > 0, "Uri should be set")

        self._minters[_id] = _to
        self._mint(_to, _id, _supply, _uri)

    # TODO: Is this necessary method?
    # @external(readonly=True)
    # def getApproved(self, _tokenId: int) -> Address:
    #     """
    #     Returns the approved address for a single NFT.
    #     If there is none, returns the zero address.
    #     Throws if _tokenId is not a valid NFT.
    #     """
    #     self.ownerOf(_tokenId)  # ensure valid token
    #     address = self._token_approvals[_tokenId]
    #     if address is None:
    #         return self._ZERO_ADDRESS
    #     return address

    @external
    def setApprovalForAll(self, _operator: Address, _approved: bool):
        """
        Enables or disables approval for a third party ("operator") to manage all of the caller's tokens,
        and must emit `ApprovalForAll` event on success.

        :param _operator: address to add to the set of authorized operators
        :param _approved: true if the operator is approved, false to revoke approval
        """
        self._operatorApproval[self.msg.sender][_operator] = _approved
        self.ApprovalForAll(self.msg.sender, _operator, _approved)

    @external(readonly=True)
    def isApprovedForAll(self, _owner: Address, _operator: Address) -> bool:
        """
        Returns the approval status of an operator for a given owner.

        :param _owner: the owner of the tokens
        :param _operator: the address of authorized operator
        :return: true if the operator is approved, false otherwise
        """
        return self._operatorApproval[_owner][_operator]

    @external
    def burn(self, _token_id: int, _value: int):
        # Burn NFT supply (not the token itself)
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to burn tokens')
        self._burn(_token_id, _value)

    def _burn(self, _token_id: int, _value: int):
        #TODO Skipped approvals for the moment
        # self._clear_approval(_token_id)

        # TODO What is the price needed for?
        # if self.get_token_price(_token_id):
        #    self._delist_token(token_owner, _token_id)
        self._remove_tokens_from(self.msg.sender, _token_id, _value)
        self._total_supply_per_token[_token_id] -= _value
        # TOOD Not needed?
        # self._remove_token_URI(_token_id)
        # TODO skipped the index for now
        # tokenIndex = self._get_token_index_by_token_id(_token_id)
        # self._adjust_token_index(tokenIndex)

        

        self.TransferSingle(self.msg.sender, ZERO_ADDRESS, _token_id, _value)

    # @external(readonly=True)
    # def get_token_price(self, _tokenId: int) -> int:
    #     """ Returns price the token is being sold for. """
    #     return self._listed_token_prices[str(_tokenId)]


    # ===============================================================================================
    # Internal methods
    # ===============================================================================================

    @eventlog(indexed=2)
    def AssignRole(self, _role: str, _owner: Address):
        pass

    @eventlog(indexed=3)
    def TransferSingle(self, _operator: Address, _from: Address, _to: Address, _id: int, _value: int):
        """
        Must trigger on any successful token transfers, including zero value transfers as well as minting or burning.
        When minting/creating tokens, the `_from` must be set to zero address.
        When burning/destroying tokens, the `_to` must be set to zero address.

        :param _operator: the address of an account/contract that is approved to make the transfer
        :param _from: the address of the token holder whose balance is decreased
        :param _to: the address of the recipient whose balance is increased
        :param _id: ID of the token
        :param _value: the amount of transfer
        """
        pass
    
    @eventlog(indexed=1)
    def URI(self, _id: int, _value: str):
        """
        Must trigger on any successful URI updates for a token ID.
        URIs are defined in RFC 3986.
        The URI must point to a JSON file that conforms to the "ERC-1155 Metadata URI JSON Schema".

        :param _id: ID of the token
        :param _value: the updated URI string
        """
        pass

    def _ensure_positive(self, _token_id: int):
        if _token_id is None or _token_id < 0:
            revert("tokenId should be positive")

    def _mint(self, _owner: Address, _id: int, _supply: int, _uri: str):
        self._add_tokens_to(_owner, _id, _supply)
        self._total_supply_per_token[_id] = _supply

        self._setTokenURI(_id, _uri)
        
        self._create_new_token_index(_id)
        # emit transfer event for Mint semantic
        self.TransferSingle(_owner, ZERO_ADDRESS, _owner, _id, _supply)

    def setTokenURI(self, _id: int, _uri: str):
        if self._minter.get() != self.msg.sender:
            revert('You are not allowed to set token URI')
        self._setTokenURI(_id, _uri)
    
    def _setTokenURI(self, _id: int, _uri: str):
        self._token_URIs[_id] = _uri
        self.URI(_id, _uri)

    def _set_token_index(self, _index: int, _token_id: int):
        self._token_index(_index).set(_token_id)
        self._token(_token_id).set(_index)

    def _increment_total_supply(self):
        self._total_number_tokens.set(self._total_number_tokens.get() + 1)

    def _is_zero_address(self, _address: Address) -> bool:
        # Check if address is zero address
        if _address == ZERO_ADDRESS:
            return True
        return False
    
    def _check_that_contract_is_unpaused(self):
        if self._is_paused.get() and not self.msg.sender == self._minter.get():
            revert("Contract is currently paused")
    
    def _is_owner_of_token(self, _from, _tokenId) -> bool:
        if self._owned_token_count_by_id[_from][_tokenId] > 0:
            return True
        else:
            return False
    
    def _get_number_of_token_classes_owned(self, _address: Address) -> int:
        return self._owned_token_count[_address]

    def _add_number_of_token_classes_owned(self, _address: Address, _value: int):
        self._owned_token_count[_address] += _value
    
    def _remove_number_of_token_classes_owned(self, _address: Address, _value: int):
        self._owned_token_count[_address] -= _value

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
        number_of_tokens = self._get_number_of_token_classes_owned(_owner)
        owned_tokens = []
        for x in range(1, number_of_tokens + 1):
            token = self.tokenOfOwnerByIndex(_owner, x)
            if token != 0:
                owned_tokens.append(self.tokenOfOwnerByIndex(_owner, x))

        return owned_tokens

    @external(readonly=True)
    def totalSupply(self) -> int:
        """
        Returns total number of different tokens.
        """
        return self._total_number_tokens.get()
    
    @external(readonly=True)
    def totalSupplyPerToken(self, _token_id) -> int:
        """
        Returns total number of different tokens.
        """
        return self._total_supply_per_token[_token_id]

    def _add_tokens_to(self, _to: Address, _token_id: int, _value: int):
        # Add token to new owner and increase token count of owner by 1
        #self._token_owner[_token_id] = _to
        self._add_number_of_token_classes_owned(_to, 1)
        self._owned_token_count_by_id[_to][_token_id] += _value

        # Add an index to the token for the owner
        index = self._owned_token_count[_to]
        self._set_owner_token_index(_to, index, _token_id)

    def _remove_tokens_from(self, _from: Address, _token_id: int, _value: int):
        # Replaces token on last index with the token that will be removed.
        token_balance = self.balanceOf(_from, _token_id)
        last_index = self.balanceOfTokenClasses(_from)

        require(token_balance > 0, "The token balance is not correct.")

        self._owned_token_count_by_id[_from][_token_id] = token_balance - _value
        
        if (token_balance - _value) == 0:
            # TODO Shouldn't this work -> self._owned_token_count_by_id[_from][_token_id].remove()
            self._owned_token_count_by_id[_from][_token_id] = token_balance - _value
            last_token = self.tokenOfOwnerByIndex(_from, last_index)
            index = self._find_token_index_by_token_id(_from, _token_id)
            if last_index > 1:
                self._set_owner_token_index(_from, index, last_token)
            self._remove_owner_token_index(_from, last_index)

            # Remove token ownership and subtract owner's token count by 1
            self._remove_number_of_token_classes_owned(_from, 1)
            #TODO self._token_owner[_token_id] = self._ZERO_ADDRESS
    
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
        new_supply = self._total_number_tokens.get() + 1
        self._set_token_index(new_supply, _token_id)
        self._increment_total_supply()

    def _get_token_index_by_token_id(self, _token_id: int) -> int:
        result = self._token(_token_id).get()
        if result:
            return result
        else:
            return 0

    def _remove_token_index(self, _index: int):
        token_id = self._token_index(_index).get()
        self._token_index(_index).remove()
        self._token(token_id).remove()

    @external
    def set_seller_fee(self, _new_fee: int):
        if self._director.get() != self.msg.sender:
            revert('You do not have permission set seller fee')
        self._seller_fee.set(_new_fee)

    @external(readonly=True)
    def seller_fee(self) -> int:
        return self._seller_fee.get()

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

    def _find_token_index_by_token_id(self, _owner: Address, _token_id: int) -> int:
        # Returns index of a given _token_id of _owner. Returns 0 when no result.
        number_of_tokens = self.balanceOfTokenClasses(_owner)
        for x in range(1, number_of_tokens + 1):
            if self.tokenOfOwnerByIndex(_owner, x) == _token_id:
                return x
        return 0

    def _set_owner_token_index(self, _address: Address, _index: int, _token_id: int):
        VarDB(f'{str(_address)}_{str(_index)}', self._db, value_type=str).set(str(_token_id))

    def _remove_owner_token_index(self, _address: Address, _index: int):
        VarDB(f'{str(_address)}_{str(_index)}', self._db, value_type=str).remove()

    # ================================================
    #  Marketplace - Sell Order
    # ================================================

    @external
    def create_sell_order(self,  _token_id: int, _price: int, _quantity: int):
        """
        Creates an sell order on the market place order.
        Throws if sale is restricted or contract is paused.
        Throws when starting price is not positive.
        Throws when sender does not own the token.
        Throws when has too few unlisted tokens
        """
        sender = self.msg.sender

        # General Checks
        self._check_that_sale_is_not_restricted()
        self._check_that_contract_is_unpaused()
        self._check_that_price_is_positive(_price)

        # Balance and token checks
        require(self._is_owner_of_token(sender, _token_id) == True, "Sender does not own the token.")
        balance = self.balanceOf(sender, _token_id)
        require(balance - self._get_listed_token_balance_by_owner(sender, _token_id) >= _quantity, "Number of tokens is less than available tokens.")

        # Get new indices
        _token_index = self._get_number_sell_orders_per_tokenid(_token_id)
        _user_token_index = self._get_number_sell_orders_per_owner(sender)

        # Set Index Mapping
        self._set_tokenid_index_to_address_index(sender, _token_id, _token_index, _user_token_index)
        self._set_address_index_to_tokenid_index(sender, _token_id, _token_index, _user_token_index)

        # Lock token balance for owner
        self._set_listed_token_balance_by_owner(sender, _token_id, _quantity)

        # Set offer information
        self._set_mp_offer_price(_token_id, _token_index, _price)
        self._set_mp_offer_quantity(_token_id, _token_index, _quantity)

        # Increase sell order count for tokenid and address
        self._increase_number_sell_orders_per_tokenid(_token_id)
        self._increase_number_sell_orders_per_owner(sender)
        self._increase_listed_sales_per_tokenID_by_owner(sender, _token_id)
    
    @external
    def list_sell_orders(self,  _token_id: int, offset: int=0) -> dict:
        """
        List all sell orders for a specific token id.
        Throws when offset is higher than the available sell orders.
        """
        num_sell_orders = self._get_number_sell_orders_per_tokenid(_token_id)
        require(offset < num_sell_orders, "Offset is higher than available sell orders.")

        result_dict = {}
        for i in range(0 + offset, min(offset + 100, num_sell_orders)):
            price = self._get_mp_offer_price(_token_id, i)
            quantity = self._get_mp_offer_quantity(_token_id, i)
            address = self._get_tokenid_index_to_address_indexing(_token_id, i).split("_")[0]
            result_dict[i] = [price, quantity, address]

        return result_dict
    
    @external
    def list_own_sell_orders(self, offset: int=0) -> dict:
        """
        List all sell active sell orders for the sender.
        Throws when offset is higher than the available sell orders.
        """
        result_dict = {}
        sender = self.msg.sender
        num_sell_orders = self._get_number_sell_orders_per_owner(sender)

        if num_sell_orders == 0:
            return result_dict

        require(offset < num_sell_orders, "Offset is higher than available sell orders.")

        for i in range(0 + offset, min(offset + 100, num_sell_orders)):
            mapping = self._get_address_index_to_tokenid_index(sender, i).split("_") #tokenid_index
            price = self._get_mp_offer_price(int(mapping[0]), int(mapping[1]))
            quantity = self._get_mp_offer_quantity(int(mapping[0]), int(mapping[1]))
        
            result_dict[i] = [int(mapping[0]), price, quantity]

        return result_dict
    
    @external
    def cancel_own_sell_order(self, _tokenID: int, _user_index: int):
        """
        Remove sell order.
        Throws if sale is restricted or contract is paused.
        """
        sender = self.msg.sender

        # General Checks
        self._check_that_contract_is_unpaused()

        # Check provided parameters
        require(self._is_owner_of_token(sender, _tokenID) == True, "Sender does not own the token.")
        require(self._get_number_sell_orders_per_owner(sender) >= _user_index, "Provided user index is wrong.")
        
        mapping = self._get_address_index_to_tokenid_index(sender, _user_index).split("_") #tokenid_index
        require(int(mapping[0]) == _tokenID, "TokenID does not match stored tokenID")

        # Get number of locked tokens      
        quantity = self._get_mp_offer_quantity(_tokenID, mapping[1]) * -1
        
        # Remove and fix Index Mapping
        self._remove_sale_and_fix_index(sender, _tokenID, "_".join(mapping), _user_index, quantity)

        

    @external
    @payable
    def purchase_token(self, _tokenID: int, _token_index: int):
        """
        Purchase a token offer from the market place. The amount of ICX sent must match the token sale price,
        otherwise throws an error. When a correct amount is sent, the NFT will be sent from seller to buyer, and SCORE
        will send token's price worth of ICX to seller (minus fee, if applicable).
        """
        # General Checks
        self._check_that_contract_is_unpaused()

        buyer = self.msg.sender

        # Price related checks
        if not self.msg.value > 0:
            revert(f'Sent ICX amount needs to be greater than 0')
        
        token_price = self._get_mp_offer_price(_tokenID, _token_index)
        
        if self.msg.value != token_price:
            revert(f'Sent ICX amount ({self.msg.value}) does not match token price ({token_price})')
        
        # Get information about seller
        address_index = self._get_tokenid_index_to_address_indexing(_tokenID, _token_index).split("_")
        seller = Address.from_string(address_index[0])
        require(seller != buyer, "The seller and buyer can't have the same address.")

        user_index = address_index[1]
        quantity = self._get_mp_offer_quantity(_tokenID, _token_index) 

        # Clean up
        self._remove_sale_and_fix_index(seller, _tokenID, _token_index, user_index, quantity)

        # Transfer icx and tokens
        self._transfer(seller, buyer, _tokenID, quantity)
        
        fee = self._calculate_seller_fee(token_price)

        self.icx.transfer(seller, int(token_price - fee))

        self.icx.transfer(self.address, int(fee))

        self._create_sale_record(_token_id=_tokenID,
                                 _type='sale_success',
                                 _seller=seller,
                                 _buyer=buyer,
                                 _starting_price=token_price,
                                 _final_price=token_price,
                                 _end_time=self.now(),
                                 _number_tokens=quantity)

        self.PurchaseToken(seller, buyer, _tokenID)


    def _remove_sale_and_fix_index(self, _address: Address, _tokenID: int, _token_index: int, _user_index: int, _quantity: int):
        self._set_listed_token_balance_by_owner(_address, _tokenID, _quantity)
        last_index_tokenid = self._get_number_sell_orders_per_tokenid(_tokenID)
        last_index_address = self._get_number_sell_orders_per_owner(_address)

        last_index_tokenid_to_address = self._get_tokenid_index_to_address_indexing(_tokenID, last_index_tokenid).split("_")
        last_index_address_to_tokenid = self._get_address_index_to_tokenid_index(_address, last_index_address).split("_")

        self._remove_tokenid_index_to_address_index(_tokenID, _token_index)
        self._remove_tokenid_index_to_address_index(_tokenID, last_index_tokenid)

        self._remove_address_index_to_tokenid_index(_address, _user_index)
        self._remove_address_index_to_tokenid_index(_address, last_index_address)
        #TODO Fix setting removed index to last index
        if last_index_tokenid > 1:
            self._set_tokenid_index_to_address_index(last_index_tokenid_to_address[0], _tokenID, _token_index, last_index_tokenid_to_address[1])
        
        if last_index_address > 1:
            self._set_address_index_to_tokenid_index(_address, last_index_address_to_tokenid[0], last_index_address_to_tokenid[1], _user_index)

        # Decrease sell order count for tokenid and address
        self._decrease_number_sell_orders_per_tokenid(_tokenID)
        self._decrease_number_sell_orders_per_owner(_address)

        self._set_mp_offer_price(_tokenID, _token_index, 0)
        self._set_mp_offer_quantity(_tokenID, _token_index, 0)

    def _set_tokenid_index_to_address_index(self, _address: Address, _tokenID: int, _token_index: int, _user_token_index: int):
        self._index_mapping[str(_tokenID) + "_" + str(_token_index)] = str(_address) + "_" + str(_user_token_index)
    
    def _remove_tokenid_index_to_address_index(self, _tokenID: int, _token_index: int):
        self._index_mapping[str(_tokenID) + "_" + str(_token_index)] = ""

    def _get_tokenid_index_to_address_indexing(self, _tokenID: int, _token_index: int) -> str:
        return self._index_mapping[str(_tokenID) + "_" + str(_token_index)]

    def _set_address_index_to_tokenid_index(self, _address: Address, _tokenID: int, _token_index: int, _user_token_index: int):
        self._address_index_to_tokenid_index[str(_address) + "_" + str(_user_token_index)] = str(_tokenID) + "_" + str(_token_index)
    
    def _remove_address_index_to_tokenid_index(self, _address: Address, _user_token_index: int):
        self._address_index_to_tokenid_index[str(_address) + "_" + str(_user_token_index)] = ""
    
    def _get_address_index_to_tokenid_index(self, _address: Address, _index: int) -> str:
        return self._address_index_to_tokenid_index[str(_address) + "_" + str(_index)]
    
    def _increase_number_sell_orders_per_owner(self, _address: Address):
        self._number_sell_orders_per_owner[_address] += 1
    
    def _decrease_number_sell_orders_per_owner(self, _address: Address):
        self._number_sell_orders_per_owner[_address] -= 1
    
    def _get_number_sell_orders_per_owner(self, _address: Address) -> int:
        return self._number_sell_orders_per_owner[_address]

    #def _increase_number_token_types_listed_by_owner(self, _address: Address):
    #    self._listed_token_types_by_owner[_address] += 1
    
    #def _increase_number_token_types_listed_by_owner(self, _address: Address):
    #    self._listed_token_types_by_owner[_address] -= 1
    
    #def _get_number_token_types_listed_by_owner(self, _address: Address) -> int:
    #    return self._listed_token_types_by_owner[_address]
        
    def _increase_number_sell_orders_per_tokenid(self, _tokenID: int):
        self._number_sale_orders_per_tokenid[_tokenID] += 1
    
    def _decrease_number_sell_orders_per_tokenid(self, _tokenID: int):
        self._number_sale_orders_per_tokenid[_tokenID] -= 1
    
    def _get_number_sell_orders_per_tokenid(self, _tokenID: int) -> int:
        return self._number_sale_orders_per_tokenid[_tokenID]

    def _set_listed_token_balance_by_owner(self, _address: Address, _tokenID: int, _quantitiy: int):
        self._listed_token_balance_by_owner[_address][_tokenID] += _quantitiy
    
    def _get_listed_token_balance_by_owner(self, _address: Address, _tokenID: int) -> int:
        return self._listed_token_balance_by_owner[_address][_tokenID]

    def _increase_listed_sales_per_tokenID_by_owner(self, _address: Address, _tokenID: int):
        self._listed_sales_per_tokenid_by_owner[_address][_tokenID] += 1
    
    def _decrease_listed_sales_per_tokenID_by_owner(self, _address: Address, _tokenID: int):
        self._listed_sales_per_tokenid_by_owner[_address][_tokenID] -= 1
    
    def _get_listed_sales_per_tokenID_by_owner(self, _address: Address, _tokenID: int):
        return self._listed_sales_per_tokenid_by_owner[_address][_tokenID]
    
    def _set_mp_offer_price(self, _tokenID: int, _index: int, _price: int):
        self._mp_price_list[_tokenID][_index] = _price

    def _get_mp_offer_price(self, _tokenID: int, _index: int):
        return self._mp_price_list[_tokenID][_index]
    
    def _set_mp_offer_quantity(self, _tokenID: int, _index: int, _quantity: int):
        self._mp_quantity_list[_tokenID][_index] = _quantity

    def _get_mp_offer_quantity(self, _tokenID: int, _index: int) -> int:
        return self._mp_quantity_list[_tokenID][_index]

    # ================================================
    #  Marketplace - Buy Order
    # ================================================

    @external
    @payable
    def create_buy_order(self, _token_id: int, _price: int, _quantity: int):
        """
        Creates a buy order on the market place.
        Throws if sale is restricted or contract is paused. Throws when token is already listed.
        Throws when sender does not own the token. Throws when starting price is not positive.
        """
        self._check_that_sale_is_not_restricted()
        self._check_that_contract_is_unpaused()
        self._check_that_price_is_positive(_price)

        if not self.msg.value > 0:
            revert(f'Sent ICX amount needs to be greater than 0')
        
        if self.msg.value != _price:
            revert(f'Sent ICX amount ({self.msg.value}) does not match offer price ({_price})')

        sender = self.msg.sender
        
        # Get new indices
        _token_index = self._get_number_buy_orders_per_tokenid(_token_id)
        _user_token_index = self._get_number_buy_orders_per_owner(sender)

        # Set offer information
        self._set_mp_buy_price(_token_id, _token_index, _price)
        self._set_mp_buy_quantity(_token_id, _token_index, _quantity)

        # Set Index Mapping
        self._set_buy_tokenid_index_to_address_index(sender, _token_id, _token_index, _user_token_index)
        self._set_buy_address_index_to_tokenid_index(sender, _token_id, _token_index, _user_token_index)

        # Increase sell order count for tokenid and address
        self._increase_number_buy_orders_per_tokenid(_token_id)
        self._increase_number_buy_orders_per_owner(sender)
        self._increase_listed_purchases_per_tokenID_by_owner(sender, _token_id)
    
    @external
    def cancel_own_buy_order(self, _tokenID: int, _user_index: int):
        """
        Remove buy order.
        """
        
        sender = self.msg.sender
        tokenID_index = self._get_buy_address_index_to_tokenid_index(sender, _user_index)
        token_index = int(tokenID_index.split("_")[1])
        require(tokenID_index.split("_")[0] != _tokenID, "TokenID does not match stored tokenID")
        # TODO if it returns 0 in case it is wrong.
        #require(tokenID_index != 0, "Sender does not have a buy order with the provided id.")

        # User       
        #mapping = self._get_address_index_to_tokenid_index(sender, _user_index).split("_") #tokenid_index
        price = self._get_mp_buy_price(_tokenID, token_index)

        # Remove and fix Index Mapping
        self._remove_buy_order_and_fix_index(sender, _tokenID, token_index, _user_index)

        # Send the icx back
        # TODO remove fee
        self.icx.transfer(sender, price)
    
    @external
    def list_buy_orders(self,  _token_id: int, offset: int=0) -> dict:
        """
        List all buy orders for a specific token id.
        Throws when offset is higher than the available buy orders.
        """
        num_buy_orders = self._get_number_buy_orders_per_tokenid(_token_id)
        require(offset < num_buy_orders, "Offset is higher than available buy orders.")

        result_dict = {}
        for i in range(0 + offset, min(offset + 100, num_buy_orders)):
            price = self._get_mp_buy_price(_token_id, i)
            quantity = self._get_mp_buy_quantity(_token_id, i)
            address = self._get_buy_tokenid_index_to_address_indexing(_token_id, i).split("_")[0]
            result_dict[i] = [price, quantity, address]
            #TODO the tokenid index is missing for the accept_buy_order to be accepted.
        return result_dict
    
    @external
    def list_own_buy_orders(self, offset: int=0) -> dict:
        """
        List all active buy orders for the sender.
        """
        sender = self.msg.sender
        num_buy_orders = self._get_number_buy_orders_per_owner(sender)
        require(num_buy_orders > 0, "There is no sell order for that address.")
        require(offset < num_buy_orders, "Offset is higher than available sell orders.")

        result_dict = {}
        for i in range(0 + offset, min(offset + 100, num_buy_orders)):
            mapping = self._get_buy_address_index_to_tokenid_index(sender, i).split("_") #tokenid_index
            price = self._get_mp_buy_price(int(mapping[0]), int(mapping[1]))
            quantity = self._get_mp_buy_quantity(int(mapping[0]), int(mapping[1]))
        
            result_dict[i] = [int(mapping[0]), price, quantity]

        return result_dict

    @external
    def accept_buy_order(self, _tokenID: int, _token_index: int):
        """
        Accept a buy order for your tokens from the market place. The sender wallet needs to hold a sufficient amount
        of unlocked tockens, otherwise throws an error. When a correct amount is available, the tokens will be transfered
        to to the person offering the icx and icx will be send to the token holder (minus fee, if applicable).
        """
        self._check_that_contract_is_unpaused()
        self._check_that_sale_is_not_restricted()

        sender = self.msg.sender
        require(self._is_owner_of_token(sender, _tokenID) == True, "Sender does not own the token.")
        balance = self.balanceOf(sender, _tokenID)        

        quantity = self._get_mp_buy_quantity(_tokenID, _token_index)

        require(balance - self._get_listed_token_balance_by_owner(sender, _tokenID) >= quantity, "Number of tokens is less than available tokens.")

        address_index = self._get_buy_tokenid_index_to_address_indexing(_tokenID, _token_index).split("_")

        buyer = Address.from_string(address_index[0])
        user_index = int(address_index[1])
 
        self._remove_buy_order_and_fix_index(buyer, _tokenID, _token_index, user_index)
        self._transfer(sender, buyer, _tokenID, quantity)
        
        token_price = self._get_mp_buy_price(_tokenID, _token_index)

        fee = self._calculate_seller_fee(token_price)

        self.icx.transfer(sender, int(token_price - fee))

        self._create_sale_record(_token_id=_tokenID,
                                 _type='buy_success',
                                 _seller=sender,
                                 _buyer=buyer,
                                 _starting_price=token_price,
                                 _final_price=token_price,
                                 _end_time=self.now(),
                                 _number_tokens=quantity)

        self.PurchaseToken(sender, buyer, _tokenID)


    def _remove_buy_order_and_fix_index(self, _address: Address, _token_id: int, _token_index: int, _user_index: int):
        self._set_mp_buy_price(_token_id, _token_index, 0)
        self._set_mp_buy_quantity(_token_id, _token_index, 0)

        last_index_tokenid = self._get_number_buy_orders_per_tokenid(_token_id) - 1
        last_index_address = self._get_number_buy_orders_per_owner(_address) - 1

        last_index_tokenid_to_address = self._get_buy_tokenid_index_to_address_indexing(_token_id, last_index_tokenid).split("_")
        last_index_address_to_tokenid = self._get_buy_address_index_to_tokenid_index(_address, last_index_address).split("_")

        # Set Index Mapping
        self._remove_buy_tokenid_index_to_address_index(_token_id, _token_index)
        self._remove_buy_tokenid_index_to_address_index(_token_id, last_index_tokenid)
        self._remove_buy_address_index_to_tokenid_index(_address, _user_index)
        self._remove_buy_address_index_to_tokenid_index(_address, last_index_address)

        #TODO Fix setting removed index to last index
        if last_index_tokenid > 0:
            self._set_buy_tokenid_index_to_address_index(last_index_tokenid_to_address[0], _token_id, _token_index, last_index_tokenid_to_address[1])
        
        if last_index_address > 0:
            self._set_buy_address_index_to_tokenid_index(_address, last_index_address_to_tokenid[0], last_index_address_to_tokenid[1], _user_index)

        # Decrease sell order count for tokenid and address
        self._decrease_number_buy_orders_per_tokenid(_token_id)
        self._decrease_number_buy_orders_per_owner(_address)
        self._decrease_listed_purchases_per_tokenID_by_owner(_address, _token_id)

    def _set_mp_buy_price(self, _tokenID: int, _index: int, _price: int):
        self._mp_buy_price_list[_tokenID][_index] = _price

    def _get_mp_buy_price(self, _tokenID: int, _index: int):
        return self._mp_buy_price_list[_tokenID][_index]
    
    def _set_mp_buy_quantity(self, _tokenID: int, _index: int, _quantity: int):
        self._mp_buy_quantity_list[_tokenID][_index] = _quantity

    def _get_mp_buy_quantity(self, _tokenID: int, _index: int):
        return self._mp_buy_quantity_list[_tokenID][_index]
    
    def _increase_number_buy_orders_per_tokenid(self, _tokenID: int):
        self._number_buy_orders_per_tokenid[_tokenID] += 1
    
    def _decrease_number_buy_orders_per_tokenid(self, _tokenID: int):
        self._number_buy_orders_per_tokenid[_tokenID] -= 1
    
    def _get_number_buy_orders_per_tokenid(self, _tokenID: int) -> int:
        return self._number_buy_orders_per_tokenid[_tokenID]

    def _increase_number_buy_orders_per_owner(self, _address: Address):
        self._number_buy_orders_per_owner[_address] += 1
    
    def _decrease_number_buy_orders_per_owner(self, _address: Address):
        self._number_buy_orders_per_owner[_address] -= 1
    
    def _get_number_buy_orders_per_owner(self, _address: Address) -> int:
        return self._number_buy_orders_per_owner[_address]
    
    def _set_buy_tokenid_index_to_address_index(self, _address: Address, _tokenID: int, _token_index: int, _user_token_index: int):
        self._index_mapping_purchase[str(_tokenID) + "_" + str(_token_index)] = str(_address) + "_" + str(_user_token_index)
    
    def _remove_buy_tokenid_index_to_address_index(self, _tokenID: int, _token_index: int):
        self._index_mapping_purchase[str(_tokenID) + "_" + str(_token_index)] = ""

    def _get_buy_tokenid_index_to_address_indexing(self, _tokenID: int, _token_index: int) -> str:
        return self._index_mapping_purchase[str(_tokenID) + "_" + str(_token_index)]

    def _set_buy_address_index_to_tokenid_index(self, _address: Address, _tokenID: int, _token_index: int, _user_token_index: int):
        self._address_index_to_tokenid_index_purchase[str(_address) + "_" + str(_user_token_index)] = str(_tokenID) + "_" + str(_token_index)
    
    def _remove_buy_address_index_to_tokenid_index(self, _address: Address, _user_token_index: int):
        self._address_index_to_tokenid_index_purchase[str(_address) + "_" + str(_user_token_index)] = ""
    
    def _get_buy_address_index_to_tokenid_index(self, _address: Address, _index: int) -> str:
        return self._address_index_to_tokenid_index_purchase[str(_address) + "_" + str(_index)]
    
    def _increase_listed_purchases_per_tokenID_by_owner(self, _address: Address, _tokenID: int):
        self._listed_purchases_per_tokenid_by_owner[_address][_tokenID] += 1
    
    def _decrease_listed_purchases_per_tokenID_by_owner(self, _address: Address, _tokenID: int):
        self._listed_purchases_per_tokenid_by_owner[_address][_tokenID] -= 1
    
    def _get_listed_purchases_per_tokenID_by_owner(self, _address: Address, _tokenID: int):
        return self._listed_purchases_per_tokenid_by_owner[_address][_tokenID]
    

    # ================================================
    #  Exchange
    # ================================================

    @eventlog(indexed=2)
    def ApprovalForAll(self, _owner: Address, _operator: Address, _approved: bool):
        """
        Must trigger on any successful approval (either enabled or disabled) for a third party/operator address
        to manage all tokens for the `_owner` address.

        :param _owner: the address of the token holder
        :param _operator: the address of authorized operator
        :param _approved: true if the operator is approved, false to revoke approval
        """
        pass

    # Todo: Can be removed or replaced:
    def _check_that_token_is_not_auctioned(self, _token_id):
        if self._listed_token_prices[str(_token_id)] == -1:
            revert("Token is currently on auction")

    def _check_that_sale_is_not_restricted(self):
        if self._is_restricted_sale.get() and not self.msg.sender == self._minter.get():
            revert("Listing tokens is currently disabled")

    def _check_that_price_is_positive(self, _price):
        if _price < 0:
            revert("Price can not be negative")
        if _price == 0:
            revert("Price can not be zero")
    
    def _calculate_seller_fee(self, price: int) -> int:
        return price * self._seller_fee.get() / 100000

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
    
    def _record_number_tokens(self, _record_id: int) -> VarDB:
        return VarDB(f'RECORD_{str(_record_id)}_NUMBER_TOKENS', self._db, value_type=int)

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
                            _start_time: int = 0,
                            _number_tokens: int = 0
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
        if _number_tokens:
            self._record_number_tokens(record_id).set(_number_tokens)

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
            "number_tokens": self._record_number_tokens(_record_id).get(),
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