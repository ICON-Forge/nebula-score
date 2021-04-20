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


class NebulaTokenAuction(IconScoreBase):
    _NFT_CONTRACT_ADDRESS = 'nft_contract_address'  # Tracks NFT contract address that this contract points to
    _DIRECTOR = 'director'  # Role responsible for assigning other roles.
    _TREASURER = 'treasurer'  # Role responsible for transferring money to and from the contract
    _OPERATOR = 'operator'  # Role responsible for listing tokens
    _DISTRIBUTOR = 'distributor'  # Role responsible for sending out tokens claimed in-game
    _WHITELIST_DURATION = 'whitelist_duration'  # Duration of how long a whitelist record is valid for (in minutes)
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

        self._db = db


    def on_install(self) -> None:
        super().on_install()
        self._nft_contract_address.set(ZERO_SCORE_ADDRESS)
        self._director.set(self.msg.sender)
        self._treasurer.set(self.msg.sender)
        self._operator.set(self.msg.sender)
        self._distributor.set(self.msg.sender)

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


    # Add whitelist duration in minutes (how long whitelist is valid)
    @external
    def set_whitelist_duration(self, _duration_in_minutes: int):
        self._whitelist_duration.set(_duration_in_minutes)

        return

    @external(readonly=True)
    def get_whitelist_duration(self):
        return self._whitelist_duration.get()

    # Add (or update) token listing (or record) (args: token_id, base_price)
    @external
    def list_token(self, _token_id: int, _base_price: int):
        if self.msg.sender != self._operator.get():
            revert('You are not allowed to list a token')

        self._token_base_price(_token_id).set(_base_price)

    # Get token listing (args: token_id; returns token_id, base_price, claimed(boolean))
    @external(readonly=True)
    def get_token_listing(self, _token_id: int):
        return {
            "token_id": _token_id,
            "base_price": self._token_base_price(_token_id).get()
        }

    # Add whitelist record (args: token_id, address, modified_price)
    @external
    def add_whitelist_record(self, _token_id: int, _address: Address, _modified_price: int):
        if self.msg.sender != self._distributor.get():
            revert('You are not allowed to whitelist a token')

        self._user_token_whitelist_time(_token_id, _address).set(self.now())
        self._user_token_whitelist_modified_price(_token_id, _address).set(_modified_price)

    # Get whitelist status (args: token_id, address; returns: everything)
    @external(readonly=True)
    def get_record(self, _token_id: int, _address: Address):
        whitelist_time = self._user_token_whitelist_time(_token_id, _address).get()
        whitelist_duration = self._whitelist_duration.get() * 60 * 1000 * 1000
        whitelist_expiration_time = whitelist_time + whitelist_duration

        is_valid_whitelist: bool
        if (self.now() > whitelist_expiration_time):
            is_valid_whitelist = False
        else:
            is_valid_whitelist = True

        return {
            "token_id": _token_id,
            "address": _address,
            "valid": is_valid_whitelist,
            "base_price": int,
            "modified_price": int,
            "whitelist_time": whitelist_time,
            "whitelist_expiration_time": whitelist_expiration_time
        }


    # Claim token (args: token_id)
    @external
    @payable
    def claim_token(self, _token_id: int):
        sender = self.msg.sender
        # Check that token base_price is not zero
        if not self.msg.value > 0:
            revert(f'Sent ICX amount needs to be greater than 0')

        # Check if address (sender) and token is whitelisted (and not expired)
        whitelist_record = self.get_record(_token_id, sender)
        if not whitelist_record:
            revert(f'No whitelist entry for given token_id')

        is_valid = whitelist_record["valid"]
        if not is_valid:
            revert(f'Whitelist is not valid')

        # Check if modified price is not less than half of base_price
        if whitelist_record["modified_price"] < whitelist_record["base_price"] / 2:
            revert('Modified is too low')

        # Check that payable amount matches modified_price
        if self.msg.value != whitelist_record["modified_price"]:
            revert(f'Whitelist record price does not match sent amount')

        self._transferToken(sender, _token_id)



    @eventlog(indexed=3)
    def TokenTransfer(self, _from: Address, _to: Address, _tokenId: int):
        pass

    @eventlog(indexed=1)
    def SetNonFungibleTokenContractAddress(self, _owner: Address):
        pass

    @eventlog(indexed=2)
    def AssignRole(self, _role: str, _owner: Address):
        pass
