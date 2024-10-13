import time
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from eth_account import Account
import secrets
from random import randint, uniform, random
import os


router_abi = open('router_abi', 'r').read()
token_abi = open('token_abi', 'r').read()

networks = [{'name': 'ETH Mainnet',
             'currency': 'ETH',
             'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
             'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
             'rpcUrl': 'https://rpc.builder0x69.io',
             'chainId': 1
             },
            {'name': 'ETH Testnet',
             'currency': 'ETH',
             'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
             'WETH': '0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6',
             'rpcUrl': 'https://goerli.blockpi.network/v1/rpc/public',
             'chainId': 5},
            {'name': 'BSC Mainnet',
             'currency': 'BNB',
             'router': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
             'WETH': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
             'rpcUrl': 'https://bsc.meowrpc.com',
             'chainId': 56
             },
            {'name': 'BSC Testnet',
             'currency': 'BNB',
             'router': '0x9Ac64Cc6e4415144C455BD8E4837Fea55603e5c3',
             'WETH': '0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd',
             'rpcUrl': 'https://bsc-testnet.publicnode.com',
             'chainId': 97}
            ]


def generatePair():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    _account = Account.from_key(private_key)
    return _account


def _swapEthToToken(__account, _amount):
    try:
        txnDict = {'chainId': chainId,
                   'value': _amount,
                   'nonce': w3.eth.get_transaction_count(__account.address),
                   'gasPrice': int(w3.eth.gas_price*1.3)
                   }
        txnDict['gas'] = int(routerContract.functions.swapExactETHForTokens(
            0,
            [WETH, tokenAddress],
            __account.address,
            int(time.time())+100000
        ).estimate_gas(txnDict)*2)
        swap_txn = routerContract.functions.swapExactETHForTokens(
            0,
            [WETH, tokenAddress],
            __account.address,
            int(time.time())+100000
        ).build_transaction(txnDict)
        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(swap_txn, __account.key.hex())

        # Send the signed transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Swap transaction sent. Transaction hash: {tx_hash.hex()}")
        # wait = w3.eth.wait_for_transaction_receipt(tx_hash)

    except Exception as e:
        print(f"Error: {e}")


def _approveToken(__account, _amount):
    try:
        nonce = w3.eth.get_transaction_count(__account.address)
        print(f'Approving tokens for sale')
        txnDict = {'chainId': chainId,
                   'from': __account.address,
                   'nonce': nonce
                   }
        approveTxn = tokenContract.functions.approve(router_address, _amount).build_transaction(txnDict)
        approve_txn_signed = w3.eth.account.sign_transaction(approveTxn, __account.key.hex())
        tx_hash = w3.eth.send_raw_transaction(approve_txn_signed.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        print(f"Error: {e}")


def _swapTokenToEth(__account, _amount):
    try:
        print('checking approve')
        approved = tokenContract.functions.allowance(__account.address, router_address).call()
        print(f'allowance: {approved}')
        if approved < _amount:
            approveTxn = _approveToken(__account, _amount)
            wait = w3.eth.wait_for_transaction_receipt(approveTxn)
            while wait['blockNumber'] >= w3.eth.block_number:
                currentBlock = w3.eth.block_number
                print(f'waiting for approve to be mined', end='\r')
                if wait['blockNumber'] < w3.eth.block_number:
                    break
        nonce = w3.eth.get_transaction_count(__account.address)
        txnDict = {'chainId': chainId,
                   'from': __account.address,
                   'nonce': nonce,
                   'gasPrice': int(w3.eth.gas_price * 1.3)
                   }
        txnDict['gas'] = int(routerContract.functions.swapExactTokensForETH(
            _amount,
            0,
            [tokenAddress, WETH],
            __account.address,
            int(time.time())+100000
        ).estimate_gas(txnDict)*2)
        swap_txn = routerContract.functions.swapExactTokensForETH(
            _amount,
            0,
            [tokenAddress, WETH],
            __account.address,
            int(time.time())+100000
        ).build_transaction(txnDict)
        txnDict['gas'] = w3.eth.estimate_gas(swap_txn)
        swap_txn = routerContract.functions.swapExactTokensForETH(
            _amount,
            0,
            [tokenAddress, WETH],
            __account.address,
            int(time.time())+100000
        ).build_transaction(txnDict)
        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(swap_txn, __account.key.hex())

        # Send the signed transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Swap transaction sent. Transaction hash: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        print(f"Error: {e}")


# DONE
def _sendEth(_account, _to, _amount, nonce):
    _from = _account.address
    _pKey = _account.key.hex()
    print(f'Sending {w3.from_wei(_amount, "ether")} from {_from[:6]} to {_to[:6]}')
    txn = {'to': _to,
           'chainId': chainId,
           'gas': 21000,
           'gasPrice': w3.eth.gas_price,
           'value': _amount,
           'nonce': nonce}
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=_pKey)
    send_txn = w3.eth.send_raw_transaction(signed_txn.rawTransaction)


def _split(_number, minAmount):
    # max_part_value = _number - (10 - 1) * minAmount
    ratios = [random() for _ in range(10)]
    total_ratio = sum(ratios)
    parts = [int(_number * ratio / total_ratio) for ratio in ratios]
    for i in range(10):
        if parts[i] < minAmount:
            parts[i] = minAmount
    remaining = _number - sum(parts)
    while remaining > 0:
        for i in range(10):
            if remaining == 0:
                break
            parts[i] += 1
            remaining -= 1
    return parts


def waitingNewBlock(blockNumber):
    currentBlock = w3.eth.block_number
    while currentBlock < blockNumber + blocksToWait:
        print(
            f'Current block: {currentBlock} waiting for block {blockNumber + blocksToWait} diff: {(blockNumber + blocksToWait) - currentBlock}  ',
            end='\r')
        currentBlock = w3.eth.block_number
        if currentBlock >= blockNumber + blocksToWait:
            return


print('Choose option:\n'
      '[1] Generate volume\n'
      '[2] Clear wallets from tokens\n'
      '[3] Clear wallets from ETH/BNB')
opt = int(input('>>'))

networkSymbols = ['ethM', 'ethT', 'bscM', 'bscT']
if opt == 2:
    print('Name of file with wallets ?\n'
          'example: wallets-1532421-etht.txt')
    fName = input()
    print('Token address?')
    tokenAddress = input('>>')
    networkSymbol = fName.split('-')[2][:4]
    network = networks[networkSymbols.index(networkSymbol)]
    rpcUrl = network['rpcUrl']
    chainId = network['chainId']
    w3 = Web3(HTTPProvider(rpcUrl))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    router_address = network['router']
    routerContract = w3.eth.contract(address=router_address, abi=router_abi)
    WETH = network['WETH']
    if w3.is_checksum_address(tokenAddress) is False:
        tokenAddress = w3.to_checksum_address(tokenAddress)
    tokenContract = w3.eth.contract(address=tokenAddress, abi=token_abi)
    if os.path.isfile(fName) is True:
        wallets_ = open(fName, 'r').readlines()
        wallets = {}
        for x in wallets_:
            address = x.strip('\n').split(',')[0]
            pKey = x.strip('\n').split(',')[1]
            wallets[address] = pKey
        for x in wallets.keys():
            _acc = Account.from_key(wallets[x])
            __balance = int(tokenContract.functions.balanceOf(x).call())
            print(x)
            print(__balance)
            if __balance > 0:
                approved = tokenContract.functions.allowance(x, router_address).call()
                print(f'allowance: {approved}')
                if approved < __balance:
                    approveTxn = _approveToken(_acc, __balance)
        print('sleeping')
        time.sleep(15)
        for x in wallets.keys():
            _acc = Account.from_key(wallets[x])
            __balance = int(tokenContract.functions.balanceOf(x).call())
            if __balance > 0:
                _swapTokenToEth(_acc, __balance)
    exit()

elif opt == 3:
    print('Name of file with wallets ?\n'
          'example: wallets-1532421-etht.txt')
    fName = input()
    print('Address where to send funds')
    networkSymbol = fName.split('-')[2][:4]
    network = networks[networkSymbols.index(networkSymbol)]
    rpcUrl = network['rpcUrl']
    chainId = network['chainId']
    w3 = Web3(HTTPProvider(rpcUrl))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    router_address = network['router']
    routerContract = w3.eth.contract(address=router_address, abi=router_abi)
    WETH = network['WETH']
    to_ = input('>>')
    if w3.is_checksum_address(to_) is False:
        to_ = w3.to_checksum_address(to_)
    if os.path.isfile(fName) is True:
        wallets_ = open(fName, 'r').readlines()
        wallets = {}
        for x in wallets_:
            address = x.strip('\n').split(',')[0]
            pKey = x.strip('\n').split(',')[1]
            wallets[address] = pKey
        for x in wallets.keys():
            balance = w3.eth.get_balance(x)
            gasReq = w3.eth.gas_price*23000
            if balance > gasReq:
                print(f'wallet: {x} balance {balance}')
                nonce = w3.eth.get_transaction_count(x)
                _acc = Account.from_key(wallets[x])
                _sendEth(_acc, to_, balance-gasReq, nonce)
    exit()



print(f'Choose network:\n'
      f'[1] ETH Mainnet\n'
      f'[2] ETH Testnet\n'
      f'[3] BSC Mainnet\n'
      f'[4] BSC Testnet\n')
opt = int(input('>>'))
network = networks[opt-1]
rpcUrl = network['rpcUrl']
chainId = network['chainId']


fName = f'wallets-{int(time.time())}-{networkSymbols[opt-1]}.txt'

w3 = Web3(HTTPProvider(rpcUrl))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

router_address = network['router']
routerContract = w3.eth.contract(address=router_address, abi=router_abi)
WETH = network['WETH']

print(f'Paste token address')
tokenAddress = input('>>')
if w3.is_checksum_address(tokenAddress) is False:
    tokenAddress = w3.to_checksum_address(tokenAddress)
tokenContract = w3.eth.contract(address=tokenAddress, abi=token_abi)
tokenName = tokenContract.functions.name().call()
tokenSymbol = tokenContract.functions.symbol().call()


print(f'Generating main wallet')
mainWallet = generatePair()


with open(fName, 'a') as fp:
    fp.write(f'{mainWallet.address},{mainWallet.key.hex()}\n')
    fp.close()
print(f'Main wallet generated\n'
      f'---------------------\n'
      f'Address: {mainWallet.address}\n'
      f'Private key: {mainWallet.key.hex()}\n'
      f'---------------------')

print(f'Send funds to this wallet and press enter')
input()
_balance = w3.from_wei(w3.eth.get_balance(mainWallet.address), 'ether')
# _balance = 0
while _balance == 0:
    print(f'Wallet balance: {float(_balance)}\n'
          f'Send funds to wallet and press enter')
    input()
    _balance = w3.from_wei(w3.eth.get_balance(mainWallet.address), 'ether')
    if _balance > 0:
        break
print(f'Wallet balance: {float(_balance)}')

print(f'Rise holders amount?\n'
      f'[Y]es\n'
      f'[N]o')
opt = input('>>')
if opt.lower() != 'y' and opt.lower() != 'n':
    print(f'Choose y or n')
    exit(0)
if opt.lower() == 'y':
    riseHolders = True
elif opt.lower() == 'n':
    riseHolders = False

firstStage = 10
secondStage = 10


print(f'Generating first {firstStage} wallets')
first10Wallets = []
for x in range(0, firstStage):
    _account = generatePair()
    with open(fName, 'a') as fp:
        fp.write(f'{_account.address},{_account.key.hex()}\n')
        fp.close()
    first10Wallets.append(_account)


walletsToSwap = []
blocksToWait = 10

_gasCost = float(w3.from_wei((w3.eth.gas_price*21000)*11, 'ether'))
print(f'Settings:\n'
      f'Network: {network["name"]}\n'
      f'Wallet balance: {float(_balance)}\n'
      f'Gas fee: {_gasCost}\n'
      f'Starting funds: {float(_balance)-_gasCost}\n'
      f'Token address: {tokenAddress}\n'
      f'Token name: {tokenName}\n'
      f'Token symbol: {tokenSymbol}\n'
      f'Press "Enter" to start')
input()

_f = w3.eth.get_balance(mainWallet.address) - ((w3.eth.gas_price*21000)*11)
_firstStage = _f
_minToSend1 = _firstStage/100
_minToSend2 = _firstStage/1000


print(f'Spreading fund first stage')
amountList = _split(_firstStage, _minToSend1)
correction = sum(amountList) - _firstStage
while sum(amountList) > _firstStage:
    amountList = _split(_firstStage, _minToSend1)
    print(sum(amountList))
    if (sum(amountList) - _firstStage) == 0:
        break
non = w3.eth.get_transaction_count(mainWallet.address)
for x in first10Wallets:
    _sendEth(mainWallet, x.address, amountList[first10Wallets.index(x)], non)
    non += 1
print(f'First stage done, waiting {blocksToWait} blocks')
waitingNewBlock(w3.eth.block_number)
print(f'Spreading funds second stage')
for fi in first10Wallets:
    second10Wallets = []
    non = w3.eth.get_transaction_count(fi.address)
    for d in range(0, secondStage):
        _account = generatePair()
        with open(fName, 'a') as fp:
            fp.write(f'{_account.address},{_account.key.hex()}\n')
            fp.close()
        second10Wallets.append(_account)
        walletsToSwap.append(_account)
    _gasPrice = w3.eth.gas_price*21000
    __balance = w3.eth.get_balance(fi.address) - (_gasPrice * 11)
    _amountList = _split(__balance, _minToSend2)
    correction = sum(_amountList) - __balance
    while sum(_amountList) > __balance:
        _amountList = _split(__balance, _minToSend2)
        if (sum(_amountList) - __balance) == 0:
            break
    for y in second10Wallets:
        _sendEth(fi, y.address, _amountList[second10Wallets.index(y)], non)
        non += 1
print(f'Second stage done waiting {blocksToWait} blocks')
waitingNewBlock(w3.eth.block_number)
print(f'Buying!')
for wal in walletsToSwap:
    __balance = w3.eth.get_balance(wal.address)
    __maxAmount = int((__balance * 30) / 100)
    print(f'wallet: {wal.address[:6]} balance: {__balance}')
    print(f'swapping 30% for token')
    _swapEthToToken(wal, __maxAmount)
print(f'Done waiting {blocksToWait} blocks')
waitingNewBlock(w3.eth.block_number)
print(f'Randomly buying or selling')
while True:
    activeWallets = walletsToSwap
    walletsToRemove = []
    walletsToAdd = []
    print(f'active wallets: {len(activeWallets)}')
    for wal in activeWallets:
        print(f'wallet {activeWallets.index(wal)}/{len(activeWallets)}')
        decid = randint(0, 1)  # 0 is sell , 1 is buy more
        if decid == 0:
            print('sell')
            __balance = int(tokenContract.functions.balanceOf(wal.address).call())
            print(f'Token balance: {__balance}')
            if __balance == 0:
                __balance = w3.eth.get_balance(wal.address)
                __maxAmount = int((__balance * 30) / 100)
                _swapEthToToken(wal, __maxAmount)
                continue
            if riseHolders == True:
                __amountToSell = int((__balance * 80) / 100)
                check = _swapTokenToEth(wal, __amountToSell)
                wait = w3.eth.wait_for_transaction_receipt(check)
                while wait['blockNumber'] >= w3.eth.block_number:
                    currentBlock = w3.eth.block_number
                    print(f'waiting for txn to be mined', end='\r')
                    if wait['blockNumber'] < w3.eth.block_number:
                        break
                wait = w3.eth.wait_for_transaction_receipt(check)
                if wait['status'] == 0:
                    continue
                elif wait['status'] == 1:
                    __balanceETH = w3.eth.get_balance(wal.address)
                    _gasPrice = w3.eth.gas_price * 22000
                    if __balanceETH > _gasPrice:
                        newWallet = generatePair()
                        with open(fName, 'a') as fp:
                            fp.write(f'{newWallet.address},{newWallet.key.hex()}\n')
                            fp.close()
                        walletsToAdd.append(newWallet)
                        walletsToRemove.append(wal)
                        _sendEth(wal, newWallet.address, (__balanceETH-_gasPrice), w3.eth.get_transaction_count(wal.address))
            elif riseHolders == False:
                check = _swapTokenToEth(wal, __balance)
                wait = w3.eth.wait_for_transaction_receipt(check)
                while wait['blockNumber'] >= w3.eth.block_number:
                    currentBlock = w3.eth.block_number
                    print(f'waiting for txn to be mined', end='\r')
                    if wait['blockNumber'] < w3.eth.block_number:
                        break
                wait = w3.eth.wait_for_transaction_receipt(check)
                if wait['status'] == 0:
                    continue
                elif wait['status'] == 1:
                    __balanceETH = w3.eth.get_balance(wal.address)
                    _gasPrice = w3.eth.gas_price * 22000
                    if __balanceETH > _gasPrice:
                        newWallet = generatePair()
                        with open(fName, 'a') as fp:
                            fp.write(f'{newWallet.address},{newWallet.key.hex()}\n')
                            fp.close()
                        walletsToAdd.append(newWallet)
                        _sendEth(wal, newWallet.address, (__balanceETH - _gasPrice),
                                 w3.eth.get_transaction_count(wal.address))
                    walletsToRemove.append(wal)
        elif decid == 1:
            print('buy')
            __balance = w3.eth.get_balance(wal.address)
            __maxAmount = int((__balance * 30) / 100)
            _swapEthToToken(wal, __maxAmount)
    for x in walletsToAdd:
        walletsToSwap.append(x)
    for x in walletsToRemove:
        walletsToSwap.pop(walletsToSwap.index(x))
    print(f'Sleeping for 60 second')
    time.sleep(60)
