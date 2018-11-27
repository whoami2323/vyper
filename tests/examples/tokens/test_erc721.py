import pytest

SOMEONE_TOKEN_IDS = [1, 2, 3]
OPERATOR_TOKEN_ID = 10
NEW_TOKEN_ID = 20
INVALID_TOKEN_ID = 99
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
ERC165_INTERFACE_ID = '0x0000000000000000000000000000000000000000000000000000000001ffc9a7'
ERC721_INTERFACE_ID = '0x0000000000000000000000000000000000000000000000000000000080ac58cd'
INVALID_INTERFACE_ID = '0x0000000000000000000000000000000000000000000000000000000012345678'


@pytest.fixture
def c(get_contract, w3):
    with open('examples/tokens/ERC721.vy') as f:
        code = f.read()
    c = get_contract(code)
    minter, someone, operator = w3.eth.accounts[:3]
    # someone owns 3 tokens
    for i in SOMEONE_TOKEN_IDS:
        c.mint(someone, i, transact={'from': minter})
    # operator owns 1 tokens
    c.mint(operator, OPERATOR_TOKEN_ID, transact={'from': minter})
    return c


def test_supportsInterface(c, assert_tx_failed):
    assert c.supportsInterface(ERC165_INTERFACE_ID) == 1
    assert c.supportsInterface(ERC721_INTERFACE_ID) == 1
    assert c.supportsInterface(INVALID_INTERFACE_ID) == 0


def test_balanceOf(c, w3, assert_tx_failed):
    someone = w3.eth.accounts[1]
    assert c.balanceOf(someone) == 3
    assert_tx_failed(lambda: c.balanceOf(ZERO_ADDRESS))


def test_ownerOf(c, w3, assert_tx_failed):
    someone = w3.eth.accounts[1]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[0]) == someone
    assert_tx_failed(lambda: c.ownerOf(INVALID_TOKEN_ID))


def test_getApproved(c, w3, assert_tx_failed):
    someone, operator = w3.eth.accounts[1:3]

    assert c.getApproved(SOMEONE_TOKEN_IDS[0]) is None

    c.approve(operator, SOMEONE_TOKEN_IDS[0], transact={'from': someone})

    assert c.getApproved(SOMEONE_TOKEN_IDS[0]) == operator


def test_isApprovedForAll(c, w3):
    someone, operator = w3.eth.accounts[1:3]

    assert c.isApprovedForAll(someone, operator) == 0

    c.setApprovalForAll(operator, True, transact={'from': someone})

    assert c.isApprovedForAll(someone, operator) == 1


def test_transferFrom_by_owner(c, w3, assert_tx_failed, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # transfer from zero address
    assert_tx_failed(lambda: c.transferFrom(
        ZERO_ADDRESS, operator, SOMEONE_TOKEN_IDS[0], transact={'from': someone}))

    # transfer to zero address
    assert_tx_failed(lambda: c.transferFrom(
        someone, ZERO_ADDRESS, SOMEONE_TOKEN_IDS[0], transact={'from': someone}))

    # transfer token without ownership
    assert_tx_failed(lambda: c.transferFrom(
        someone, operator, OPERATOR_TOKEN_ID, transact={'from': someone}))

    # transfer invalid token
    assert_tx_failed(lambda: c.transferFrom(
        someone, operator, INVALID_TOKEN_ID, transact={'from': someone}))

    # transfer by owner
    tx_hash = c.transferFrom(
        someone, operator, SOMEONE_TOKEN_IDS[0], transact={'from': someone})

    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == operator
    assert args._tokenId == SOMEONE_TOKEN_IDS[0]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[0]) == operator
    assert c.balanceOf(someone) == 2
    assert c.balanceOf(operator) == 2


def test_transferFrom_by_approved(c, w3, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # transfer by approved
    c.approve(operator, SOMEONE_TOKEN_IDS[1], transact={'from': someone})
    tx_hash = c.transferFrom(
        someone, operator, SOMEONE_TOKEN_IDS[1], transact={'from': operator})

    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == operator
    assert args._tokenId == SOMEONE_TOKEN_IDS[1]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[1]) == operator
    assert c.balanceOf(someone) == 2
    assert c.balanceOf(operator) == 2


def test_transferFrom_by_operator(c, w3, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # transfer by operator
    c.setApprovalForAll(operator, True, transact={'from': someone})
    tx_hash = c.transferFrom(
        someone, operator, SOMEONE_TOKEN_IDS[2], transact={'from': operator})

    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == operator
    assert args._tokenId == SOMEONE_TOKEN_IDS[2]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[2]) == operator
    assert c.balanceOf(someone) == 2
    assert c.balanceOf(operator) == 2


def test_safeTransferFrom_by_owner(c, w3, assert_tx_failed, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # transfer from zero address
    assert_tx_failed(lambda: c.safeTransferFrom(
        ZERO_ADDRESS, operator, SOMEONE_TOKEN_IDS[0], transact={'from': someone}))

    # transfer to zero address
    assert_tx_failed(lambda: c.safeTransferFrom(
        someone, ZERO_ADDRESS, SOMEONE_TOKEN_IDS[0], transact={'from': someone}))

    # transfer token without ownership
    assert_tx_failed(lambda: c.safeTransferFrom(
        someone, operator, OPERATOR_TOKEN_ID, transact={'from': someone}))

    # transfer invalid token
    assert_tx_failed(lambda: c.safeTransferFrom(
        someone, operator, INVALID_TOKEN_ID, transact={'from': someone}))

    # transfer by owner
    tx_hash = c.safeTransferFrom(
        someone, operator, SOMEONE_TOKEN_IDS[0], transact={'from': someone})

    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == operator
    assert args._tokenId == SOMEONE_TOKEN_IDS[0]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[0]) == operator
    assert c.balanceOf(someone) == 2
    assert c.balanceOf(operator) == 2


def test_safeTransferFrom_by_approved(c, w3, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # transfer by approved
    c.approve(operator, SOMEONE_TOKEN_IDS[1], transact={'from': someone})
    tx_hash = c.safeTransferFrom(
        someone, operator, SOMEONE_TOKEN_IDS[1], transact={'from': operator})

    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == operator
    assert args._tokenId == SOMEONE_TOKEN_IDS[1]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[1]) == operator
    assert c.balanceOf(someone) == 2
    assert c.balanceOf(operator) == 2


def test_safeTransferFrom_by_operator(c, w3, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # transfer by operator
    c.setApprovalForAll(operator, True, transact={'from': someone})
    tx_hash = c.safeTransferFrom(
        someone, operator, SOMEONE_TOKEN_IDS[2], transact={'from': operator})

    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == operator
    assert args._tokenId == SOMEONE_TOKEN_IDS[2]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[2]) == operator
    assert c.balanceOf(someone) == 2
    assert c.balanceOf(operator) == 2


def test_safeTransferFrom_to_contract(c, w3, assert_tx_failed, get_logs, get_contract):
    someone = w3.eth.accounts[1]

    # Can't transfer to a contract that doesn't implement the receiver code
    assert_tx_failed(lambda: c.safeTransferFrom(someone, c.address, SOMEONE_TOKEN_IDS[0], transact={'from': someone}))

    # Only to an address that implements that function
    receiver = get_contract("""
@public
def onERC721Received(
        _operator: address,
        _from: address,
        _tokenId: uint256,
        _data: bytes[1024]
    ) -> bytes32:
    return method_id("onERC721Received(address,address,uint256,bytes)", bytes32)
    """)
    tx_hash = c.safeTransferFrom(someone, receiver.address, SOMEONE_TOKEN_IDS[0], transact={'from': someone})

    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == receiver.address
    assert args._tokenId == SOMEONE_TOKEN_IDS[0]
    assert c.ownerOf(SOMEONE_TOKEN_IDS[0]) == receiver.address
    assert c.balanceOf(someone) == 2
    assert c.balanceOf(receiver.address) == 1


def test_approve(c, w3, assert_tx_failed, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # approve myself
    assert_tx_failed(lambda: c.approve(
        someone, SOMEONE_TOKEN_IDS[0], transact={'from': someone}))

    # approve token without ownership
    assert_tx_failed(lambda: c.approve(
        operator, OPERATOR_TOKEN_ID, transact={'from': someone}))

    # approve invalid token
    assert_tx_failed(lambda: c.approve(
        operator, INVALID_TOKEN_ID, transact={'from': someone}))

    tx_hash = c.approve(operator, SOMEONE_TOKEN_IDS[0], transact={'from': someone})
    logs = get_logs(tx_hash, c, 'Approval')

    assert len(logs) > 0
    args = logs[0].args
    assert args._owner == someone
    assert args._approved == operator
    assert args._tokenId == SOMEONE_TOKEN_IDS[0]


def test_setApprovalForAll(c, w3, assert_tx_failed, get_logs):
    someone, operator = w3.eth.accounts[1:3]
    approved = True

    # setApprovalForAll myself
    assert_tx_failed(lambda: c.setApprovalForAll(
        someone, approved, transact={'from': someone}))

    tx_hash = c.setApprovalForAll(operator, True, transact={'from': someone})
    logs = get_logs(tx_hash, c, 'ApprovalForAll')

    assert len(logs) > 0
    args = logs[0].args
    assert args._owner == someone
    assert args._operator == operator
    assert args._approved == approved


def test_mint(c, w3, assert_tx_failed, get_logs):
    minter, someone = w3.eth.accounts[:2]

    # mint by non-minter
    assert_tx_failed(lambda: c.mint(
        someone, SOMEONE_TOKEN_IDS[0], transact={'from': someone}))

    # mint to zero address
    assert_tx_failed(lambda: c.mint(
        ZERO_ADDRESS, SOMEONE_TOKEN_IDS[0], transact={'from': minter}))

    # mint by minter
    tx_hash = c.mint(someone, NEW_TOKEN_ID, transact={'from': minter})
    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == ZERO_ADDRESS
    assert args._to == someone
    assert args._tokenId == NEW_TOKEN_ID
    assert c.ownerOf(NEW_TOKEN_ID) == someone
    assert c.balanceOf(someone) == 4


def test_burn(c, w3, assert_tx_failed, get_logs):
    someone, operator = w3.eth.accounts[1:3]

    # burn token without ownership
    assert_tx_failed(lambda: c.burn(SOMEONE_TOKEN_IDS[0], transact={'from': operator}))

    # burn token by owner
    tx_hash = c.burn(SOMEONE_TOKEN_IDS[0], transact={'from': someone})
    logs = get_logs(tx_hash, c, 'Transfer')

    assert len(logs) > 0
    args = logs[0].args
    assert args._from == someone
    assert args._to == ZERO_ADDRESS
    assert args._tokenId == SOMEONE_TOKEN_IDS[0]
    assert_tx_failed(lambda: c.ownerOf(SOMEONE_TOKEN_IDS[0]))
    assert c.balanceOf(someone) == 2
