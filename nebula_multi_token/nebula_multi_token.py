# Copyright 2021 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from iconservice import *
from util import ZERO_ADDRESS, require

#from .irc31_receiver import IRC31ReceiverInterface
#from ..util import ZERO_ADDRESS, require
#from ..util.rlp import rlp_encode_list


class NebulaMultiToken(IconScoreBase):
    _OWNED_TOKEN_COUNT = 'owned_token_count'  # Track token count per address
    _OWNED_TOKEN_COUNT_BY_ID = 'owned tokens'  # Track the owned tokens per address, per tokenID

    _TOTAL_SUPPLY = 'total_supply'  # Tracks total number of valid tokens (excluding ones with zero address)
    _TOTAL_SUPPLY_TOKEN = 'total_supply_token'  # Tracks total supply for each token (excluding ones with zero address)
    _LISTED_TOKEN_PRICES = 'listed_planet_prices'  # Tracks listed token prices against token IDs
    _DIRECTOR = 'director'  # Role responsible for assigning other roles.
    _TREASURER = 'treasurer'  # Role responsible for transferring money to and from the contract
    _MINTER = 'minter'  # Role responsible for minting and burning tokens
    _IS_PAUSED = 'is_paused' # Boolean value that indicates whether a contract is paused
    _IS_RESTRICTED_SALE = 'is_restricted_sale' # Boolean value that indicates if secondary token sales are restricted
    _METADATA_BASE_URL = 'metadata_base_url' # Base URL that is combined with provided token_URI when token gets minted
    _SELLER_FEE = 'seller_fee' # Percentage that the marketplace takes from each token sale. Number is divided by 100000 to get the percentage value. (e.g 2500 equals 2.5%)

    def __init__(self, db: 'IconScoreDatabase') -> None:
        super().__init__(db)
        # id => (owner => balance)
        self._owned_token_count = DictDB(self._OWNED_TOKEN_COUNT, db, value_type=int) #[address]->count
        self._owned_token_count_by_id = DictDB(self._OWNED_TOKEN_COUNT_BY_ID, db, value_type=int, depth=2) #[address][tokenID]->count


        # owner => (operator => approved)
        self._operatorApproval = DictDB('approval', db, value_type=bool, depth=2)
        # id => token URI
        self._token_URIs = DictDB('token_uri', db, value_type=str)
        self._total_number_tokens = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._total_supply_per_token = DictDB(self._TOTAL_SUPPLY_TOKEN, db, value_type=int)
        self._tokenNames = DictDB('token_name', db, value_type=str)
        self._tokenSymbol = DictDB('token_symbol', db, value_type=str)

        self._is_paused = VarDB(self._IS_PAUSED, db, value_type=bool)
        self._is_restricted_sale = VarDB(self._IS_RESTRICTED_SALE, db, value_type=bool)
        self._listed_token_prices = DictDB(self._LISTED_TOKEN_PRICES, db, value_type=int)
        self._director = VarDB(self._DIRECTOR, db, value_type=Address)
        self._treasurer = VarDB(self._TREASURER, db, value_type=Address)
        self._minter = VarDB(self._MINTER, db, value_type=Address)
        self._minters = DictDB(self._MINTER, db, value_type=Address)

        self._metadataBaseURL = VarDB(self._METADATA_BASE_URL, db, value_type=str)
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
            balances.append(self._balances[_ids[i]][_owners[i]])
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
        self._check_that_token_is_not_auctioned(_tokenId)
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
        require(_to != ZERO_ADDRESS, "_to must be non-zero")
        require(_from == self.msg.sender or self.isApprovedForAll(_from, self.msg.sender),
                "You don't have permission to transfer this NFT")
        require(0 <= _value <= self._owned_token_count_by_id[_from][_id], "Insufficient funds")

        self._check_that_contract_is_unpaused()

        self._check_that_token_is_not_auctioned(_id)

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

    def _create_new_token_index(self, _token_id: int):
        """
        Creates an index for _token_id and increases _totalSupply
        """
        new_supply = self._total_number_tokens.get() + 1
        self._set_token_index(new_supply, _token_id)
        self._increment_total_supply()
    
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
        if self._owned_token_count[_tokenId][_from] > 0:
            return True
        else:
            False
    
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
    #  Exchange
    # ================================================

    def _check_that_token_is_not_auctioned(self, _token_id):
        if self._listed_token_prices[str(_token_id)] == -1:
            revert("Token is currently on auction")

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

    def _calculate_seller_fee(self, price: int) -> int:
        return price * self._seller_fee.get() / 100000