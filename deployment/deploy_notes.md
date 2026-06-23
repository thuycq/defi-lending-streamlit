# DeFi Lending Demo - Sepolia Deployment Notes

## 1. Network

- Network: Ethereum Sepolia Testnet
- Chain ID: 11155111
- RPC Provider: QuickNode
- Deployer address: 0x09428D10764503E9158374e556398b409d37381E

## 2. Deployed contracts

### MockUSDToken

- Address: 0x7e8D9056BeA20ceF8abA9009660128E6657434C6
- Token name: Mock USD
- Token symbol: MockUSD
- Decimals: 18

### LendingPool

- Address: 0x07d306Fa4941e7f6734A2bFAD8c03279762032a4
- Role: Main lending contract for deposit, borrow, repay, withdraw and liquidation logic.

### Chainlink ETH/USD Price Feed

- Address: 0x694AA1769357215DE4FAC081bf1f309aDC325306
- Network: Sepolia
- Description: ETH / USD
- Decimals: 8

## 3. Deployment result

Deployment completed successfully.

MockUSDToken was deployed first. LendingPool was then deployed with two constructor parameters:

1. MockUSDToken address
2. Chainlink ETH/USD Price Feed address

After deployment, LendingPool was set as the authorized lending pool in MockUSDToken so it can mint and burn MockUSD during borrow, repay and liquidation operations.

## 4. Oracle check

The deployed LendingPool successfully reads ETH/USD price from the Chainlink Sepolia Price Feed.

Latest checked value:

- ETH/USD from Chainlink: 1723.89557291 USD
- ETH/USD from LendingPool: 1723.89557291 USD

The values matched, confirming that the LendingPool is connected to the real Chainlink oracle on Sepolia.

## 5. Sepolia lending flow test

A small lending flow was tested directly on Sepolia.

Initial test:

- Deposited collateral: 0.001 ETH
- Borrowed amount: 0.5 MockUSD
- Collateral value: 1.72389557291 USD
- Maximum borrowable amount: 1.034337343746 MockUSD
- Health Factor after borrow: 2.585843359365

Partial repay test:

- Repaid amount: 0.2 MockUSD
- Debt decreased from 0.5 MockUSD to 0.3 MockUSD
- MockUSD balance decreased from 0.5 MockUSD to 0.3 MockUSD
- Health Factor increased from 2.585843359365 to 4.309738932275

Partial withdraw test:

- Withdrawn collateral: 0.0002 ETH
- Collateral decreased from 0.001 ETH to 0.0008 ETH
- Debt remained 0.3 MockUSD
- LTV increased from 17.40% to 21.75%
- Health Factor decreased from 4.309738932275 to 3.44779114582

## 6. Final checked loan status

- Collateral ETH: 0.0008
- Debt MockUSD: 0.3
- Collateral Value USD: 1.379116458328
- Max Borrowable USD: 0.8274698749968
- Current LTV: 21.75%
- Health Factor: 3.44779114582

The loan remains safe because Health Factor is greater than 1.

## 7. Files generated for frontend integration

Contract addresses:

- deployment/contract_addresses.json

ABI files:

- deployment/abi/LendingPool.json
- deployment/abi/MockUSDToken.json

These files will be used later by the Streamlit frontend through web3.py.