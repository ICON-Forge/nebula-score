from iconservice import *

TAG = 'NebulaTokenClaimer'

# Interface of NonFungibleToken (IRC3) - only required methods
class NonFungibleToken(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _tokenId: int):
        pass

    @interface
    def ownerOf(self, _tokenId: int) -> Address:
        pass


class NebulaTokenClaiming(IconScoreBase):
    _NFT_CONTRACT_ADDRESS = 'nft_contract_address'  # Tracks NFT contract address that this contract points to
    _DIRECTOR = 'director'  # Role responsible for assigning other roles.
    _TREASURER = 'treasurer'  # Role responsible for transferring money to and from the contract
    _OPERATOR = 'operator'  # Role responsible for listing tokens
    _DISTRIBUTOR = 'distributor'  # Role responsible for sending out tokens claimed in-game
    _WHITELIST_DURATION = 'whitelist_duration'  # Duration of how long a whitelist record is valid for (in minutes)
    _TOTAL_LISTED_TOKEN_COUNT = 'total_listed_token_count'  # Tracks total number of listed tokens
    _MINIMUM_BID_INCREMENT = 5
    _ICX_TO_LOOPS = 1000000000000000000
    _MAX_ITERATION_LOOP = 100

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._nft_contract_address = VarDB(self._NFT_CONTRACT_ADDRESS, db, value_type=Address)
        self._director = VarDB(self._DIRECTOR, db, value_type=Address)
        self._treasurer = VarDB(self._TREASURER, db, value_type=Address)
        self._operator = VarDB(self._OPERATOR, db, value_type=Address)
        self._distributor = VarDB(self._DISTRIBUTOR, db, value_type=Address)
        self._whitelist_duration = VarDB(self._WHITELIST_DURATION, db, value_type=int)
        self._total_listed_token_count = VarDB(self._TOTAL_LISTED_TOKEN_COUNT, db, value_type=int)

        self._db = db


    def on_install(self) -> None:
        super().on_install()
        self._nft_contract_address.set(ZERO_SCORE_ADDRESS)
        self._director.set(self.msg.sender)
        self._treasurer.set(self.msg.sender)
        self._operator.set(self.msg.sender)
        self._distributor.set(self.msg.sender)
        self._whitelist_duration.set(60) # Default whitelist duration is 1 hour

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "NebulaTokenAuction"

    @external
    def assign_treasurer(self, _address: Address):
        """ Assigns treasurer role to _address. Treasurer can deposit and withdraw ICX from this contract. """
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._treasurer.set(_address)
        self.AssignRole("Treasurer", _address)

    @external
    def assign_operator(self, _address: Address):
        """ Assigns operator role to _address. Operator can list tokens. """
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._operator.set(_address)
        self.AssignRole("Operator", _address)

    @external
    def assign_distributor(self, _address: Address):
        """ Assigns distributor role to _address. Distributor can whitelist addresses and send tokens to players. """
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to assign roles')
        self._distributor.set(_address)
        self.AssignRole("Distributor", _address)

    @external
    def set_nonfungible_token_contract(self, _address: Address):
        """ Assigns NFT contract address to this auction SCORE """
        self._nft_contract_address.set(_address)
        self.SetNonFungibleTokenContractAddress(_address)

    @external(readonly=True)
    def get_nonfungible_token_contract_address(self) -> Address:
        """ Returns address of the NFT contract this auction contract is for."""
        return self._nft_contract_address.get()

    @external
    def transferToken(self, _to: Address, _tokenId: int):
        """ Used for initiating token transfer from current SCORE to address (_to) """
        if self.msg.sender != self._operator.get():
            revert('You are not allowed to transfer tokens')
        self._transferToken(_to, _tokenId)

    def _transferToken(self, _to: Address, _tokenId: int):
        nft_contract = self.create_interface_score(self._nft_contract_address.get(), NonFungibleToken)
        nft_contract.transfer(_to, _tokenId)
        self.TokenTransfer(self.address, _to, _tokenId)

    def _owner_of(self, _tokenId: int) -> Address:
        nft_contract = self.create_interface_score(self._nft_contract_address.get(), NonFungibleToken)
        return nft_contract.ownerOf(_tokenId)

    @external
    def withdraw(self, amount: int):
        """
        Used to withdraw funds from the contract.
        Throws if sender is not the Treasurer.
        """
        treasurer = self._treasurer.get()
        if self.msg.sender != treasurer:
            revert('You are not allowed to withdraw from this contract')
        self.icx.transfer(treasurer, amount)

    @payable
    def fallback(self):
        """
        Called when funds are sent to the contract.
        Throws if sender is not the Treasurer.
        """
        if self._treasurer.get() != self.msg.sender:
            revert('You are not allowed to deposit to this contract')

    # ================================================
    # Token Claims
    # ================================================

    def _token_base_price(self, _token_id: int) -> VarDB:
        return VarDB(f'TOKEN_{str(_token_id)}_BASE_PRICE', self._db, value_type=int)

    def _user_token_whitelist_time(self, _token_id: int, _address: Address) -> VarDB:
        return VarDB(f'WHITELIST_TOKEN_{str(_token_id)}_ADDRESS_{str(_address)}_TIME', self._db, value_type=int)

    def _user_token_whitelist_modified_price(self, _token_id: int, _address: Address) -> VarDB:
        return VarDB(f'WHITELIST_TOKEN_{str(_token_id)}_ADDRESS_{str(_address)}_MODIFIED_PRICE', self._db, value_type=int)

    @external(readonly=True)
    def total_listed_token_count(self) -> int:
        """ Returns total number of tokens listed for claims. """
        return self._total_listed_token_count.get()

    def _increment_listed_token_count(self):
        self._total_listed_token_count.set(self._total_listed_token_count.get() + 1)

    def _decrement_listed_token_count(self):
        self._total_listed_token_count.set(self._total_listed_token_count.get() - 1)

    @external
    def set_whitelist_duration(self, _duration_in_minutes: int):
        if self._director.get() != self.msg.sender:
            revert('You are not allowed to set whitelist duration')

        self._whitelist_duration.set(_duration_in_minutes)

    @external(readonly=True)
    def get_whitelist_duration(self) -> int:
        return self._whitelist_duration.get()

    @external
    def list_token(self, _token_id: int, _base_price: int):
        """
        Lists a token for claiming (requires whitelisting first) with a base price.
        Can be done by operator only. Token has to be in contract wallet.
        Throws if token is already listed.
        """
        if self.msg.sender != self._operator.get():
            revert('You are not allowed to list a token')

        # # Check if token is owned by contract
        # if self.address != self._owner_of(_token_id): ## TODO: Comment back in
        #     revert('Token is not owned by contract')

        if self._token_base_price(_token_id).get() != 0:
            revert('Token is already listed')

        self._token_base_price(_token_id).set(_base_price)
        self._increment_listed_token_count()

    @external
    def delist_token(self, _token_id: int):
        """
        Method used for delisting tokens. Throws if token is already delisted
        """
        if self.msg.sender != self._operator.get():
            revert('You are not allowed to delist a token')

        self._delist_token(_token_id)

    def _delist_token(self, _token_id: int):
        if self._token_base_price(_token_id).get() is None:
            revert('Token is already delisted')

        self._token_base_price(_token_id).remove()
        self._decrement_listed_token_count()

    @external(readonly=True)
    def get_token_listing(self, _token_id: int) -> dict:
        """
        Returns a token listing for a given token_id.
        """
        token_price = self._token_base_price(_token_id).get()
        if token_price:
            return {
                "token_id": _token_id,
                "base_price": self._token_base_price(_token_id).get()
            }
        else:
            return {}

    @external
    def add_whitelist_record(self, _token_id: int, _address: Address, _modified_price: int):
        """
        Creates a whitelist record for a token that is listed. Whitelisting is done to restrict what
        wallets can claim tokens. One whitelist record applies to one address and token pair and expires
        some time after record creation (specified by whitelist_duration).
        Can be done only by distributor role.
        Throws if token is not listed. Throws if modified price is less than half of base price.
        """
        if self.msg.sender != self._distributor.get():
            revert('You are not allowed to whitelist a token')

        token_price = self._token_base_price(_token_id).get()
        if not token_price:
            revert('Token is not listed')

        # Check if modified price is not less than half of base_price
        if _modified_price < token_price / 2:
            revert('Modified price is too low')

        self._user_token_whitelist_time(_token_id, _address).set(self.now())
        self._user_token_whitelist_modified_price(_token_id, _address).set(_modified_price)

    @external(readonly=True)
    def get_whitelist_record(self, _token_id: int, _address: Address) -> dict:
        """
        Returns info about token listing and details of the whitelisting record.
        """
        whitelist_time = self._user_token_whitelist_time(_token_id, _address).get()
        if whitelist_time == 0:
            return {}

        whitelist_duration = self._whitelist_duration.get() * 60 * 1000 * 1000
        whitelist_expiration_time = whitelist_time + whitelist_duration

        token_price = self._token_base_price(_token_id).get()
        is_valid_whitelist: bool
        if token_price and self.now() < whitelist_expiration_time:
            is_valid_whitelist = True
        else:
            is_valid_whitelist = False

        return {
            "token_id": _token_id,
            "address": _address,
            "valid": is_valid_whitelist,
            "base_price": token_price,
            "modified_price": self._user_token_whitelist_modified_price(_token_id, _address).get(),
            "whitelist_time": whitelist_time,
            "whitelist_expiration_time": whitelist_expiration_time
        }

    @external
    @payable
    def claim_token(self, _token_id: int):
        """
        Method is used for claiming previously whitelisted tokens. It checks the whitelist records for
        sender address, correct ICX amount and if whitelisting is still valid.
        Throws when address is not whitelisted. Throws when sending ICX that doesn't match price.
        Throws when whitelisting has expired.
        """
        sender = self.msg.sender
        if not self.msg.value > 0:
            revert(f'Sent ICX amount needs to be greater than 0')

        # Check if address (sender) and token is whitelisted (and not expired)
        whitelist_record = self.get_whitelist_record(_token_id, sender)
        if not whitelist_record:
            revert(f'This address is not whitelisted for token_id {_token_id}')

        is_valid = whitelist_record["valid"]
        if not is_valid:
            revert(f'Whitelist is not valid')

        # Check that payable amount matches modified_price
        if self.msg.value != whitelist_record["modified_price"]:
            revert(f'Whitelist record price does not match sent amount')

        # self._transferToken(sender, _token_id) # TODO: Comment back in
        self._delist_token(_token_id)


    @eventlog(indexed=3)
    def TokenTransfer(self, _from: Address, _to: Address, _tokenId: int):
        pass

    @eventlog(indexed=1)
    def SetNonFungibleTokenContractAddress(self, _owner: Address):
        pass

    @eventlog(indexed=2)
    def AssignRole(self, _role: str, _owner: Address):
        pass
