const hre = require("hardhat");

async function main() {
  const [user] = await hre.ethers.getSigners();

  const LENDING_POOL_ADDRESS = "0x07d306Fa4941e7f6734A2bFAD8c03279762032a4";

  const lendingPool = await hre.ethers.getContractAt(
    "LendingPool",
    LENDING_POOL_ADDRESS
  );

  console.log("Testing partial collateral withdraw on Sepolia...");
  console.log("User:", user.address);

  const withdrawAmount = hre.ethers.utils.parseEther("0.0002");

  const ethBalanceBefore = await user.getBalance();
  const loanBefore = await lendingPool.getLoanInfo(user.address);

  console.log("\nBefore withdraw:");
  console.log("Wallet ETH balance:", hre.ethers.utils.formatEther(ethBalanceBefore));
  console.log("Collateral ETH:", hre.ethers.utils.formatEther(loanBefore[0]));
  console.log("Debt MockUSD:", hre.ethers.utils.formatEther(loanBefore[1]));

  const ltvBeforePercent =
    parseFloat(hre.ethers.utils.formatEther(loanBefore[4])) * 100;

  console.log("Current LTV:", ltvBeforePercent.toFixed(2), "%");
  console.log("Health Factor:", hre.ethers.utils.formatEther(loanBefore[5]));

  console.log(
    "\nWithdrawing collateral:",
    hre.ethers.utils.formatEther(withdrawAmount),
    "ETH"
  );

  const withdrawTx = await lendingPool.withdrawCollateral(withdrawAmount);
  await withdrawTx.wait();

  console.log("Withdraw successful.");

  const ethBalanceAfter = await user.getBalance();
  const loanAfter = await lendingPool.getLoanInfo(user.address);

  console.log("\nAfter withdraw:");
  console.log("Wallet ETH balance:", hre.ethers.utils.formatEther(ethBalanceAfter));
  console.log("Collateral ETH:", hre.ethers.utils.formatEther(loanAfter[0]));
  console.log("Debt MockUSD:", hre.ethers.utils.formatEther(loanAfter[1]));

  const ltvAfterPercent =
    parseFloat(hre.ethers.utils.formatEther(loanAfter[4])) * 100;

  console.log("Current LTV:", ltvAfterPercent.toFixed(2), "%");
  console.log("Health Factor:", hre.ethers.utils.formatEther(loanAfter[5]));

  console.log("\nPartial withdraw test completed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});