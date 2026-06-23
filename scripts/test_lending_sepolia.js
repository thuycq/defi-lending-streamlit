const hre = require("hardhat");

async function main() {
  const [user] = await hre.ethers.getSigners();

  const MOCK_USD_ADDRESS = "0x7e8D9056BeA20ceF8abA9009660128E6657434C6";
  const LENDING_POOL_ADDRESS = "0x07d306Fa4941e7f6734A2bFAD8c03279762032a4";

  const mockUSD = await hre.ethers.getContractAt(
    "MockUSDToken",
    MOCK_USD_ADDRESS
  );

  const lendingPool = await hre.ethers.getContractAt(
    "LendingPool",
    LENDING_POOL_ADDRESS
  );

  console.log("Testing lending flow on Sepolia...");
  console.log("User:", user.address);

  const balanceBefore = await user.getBalance();
  console.log(
    "User ETH balance before:",
    hre.ethers.utils.formatEther(balanceBefore),
    "ETH"
  );

  // 1. Check real ETH/USD price from LendingPool
  const ethPriceData = await lendingPool.getETHPrice();
  const price = ethPriceData.price || ethPriceData[0];
  const priceDecimals = ethPriceData.decimals ?? ethPriceData[1];

  console.log(
    "ETH/USD price from LendingPool:",
    hre.ethers.utils.formatUnits(price, priceDecimals),
    "USD"
  );

  // 2. Deposit small collateral: 0.001 ETH
  const depositAmount = hre.ethers.utils.parseEther("0.001");

  console.log("\nDepositing collateral:", hre.ethers.utils.formatEther(depositAmount), "ETH");

  const depositTx = await lendingPool.depositCollateral({
    value: depositAmount,
  });
  await depositTx.wait();

  console.log("Deposit successful.");

  // 3. Read max borrowable
  const maxBorrowable = await lendingPool.getMaxBorrowable(user.address);

  console.log(
    "Max borrowable:",
    hre.ethers.utils.formatEther(maxBorrowable),
    "MockUSD"
  );

  // 4. Borrow 0.5 MockUSD
  const borrowAmount = hre.ethers.utils.parseEther("0.5");

  console.log("\nBorrowing:", hre.ethers.utils.formatEther(borrowAmount), "MockUSD");

  const borrowTx = await lendingPool.borrow(borrowAmount);
  await borrowTx.wait();

  console.log("Borrow successful.");

  // 5. Check MockUSD balance
  const mockUSDBalance = await mockUSD.balanceOf(user.address);

  console.log(
    "User MockUSD balance:",
    hre.ethers.utils.formatEther(mockUSDBalance),
    "MockUSD"
  );

  // 6. Check loan info
  const loanInfo = await lendingPool.getLoanInfo(user.address);

  console.log("\nLoan info:");
  console.log("Collateral ETH:", hre.ethers.utils.formatEther(loanInfo[0]));
  console.log("Debt MockUSD:", hre.ethers.utils.formatEther(loanInfo[1]));
  console.log("Collateral Value USD:", hre.ethers.utils.formatEther(loanInfo[2]));
  console.log("Max Borrowable USD:", hre.ethers.utils.formatEther(loanInfo[3]));
  console.log("Current LTV:", loanInfo[4].toString(), "bps");
  console.log("Health Factor:", hre.ethers.utils.formatEther(loanInfo[5]));

  const balanceAfter = await user.getBalance();
  console.log(
    "\nUser ETH balance after:",
    hre.ethers.utils.formatEther(balanceAfter),
    "ETH"
  );

  console.log("\nSepolia lending test completed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});