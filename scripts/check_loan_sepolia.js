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

  console.log("Checking Sepolia loan status...");
  console.log("User:", user.address);

  const ethBalance = await user.getBalance();
  const mockUSDBalance = await mockUSD.balanceOf(user.address);

  console.log("Wallet ETH balance:", hre.ethers.utils.formatEther(ethBalance), "ETH");
  console.log("Wallet MockUSD balance:", hre.ethers.utils.formatEther(mockUSDBalance), "MockUSD");

  const ethPriceData = await lendingPool.getETHPrice();
  const price = ethPriceData.price || ethPriceData[0];
  const priceDecimals = ethPriceData.decimals ?? ethPriceData[1];

  console.log(
    "ETH/USD price:",
    hre.ethers.utils.formatUnits(price, priceDecimals),
    "USD"
  );

  const loanInfo = await lendingPool.getLoanInfo(user.address);

  const collateralETH = loanInfo[0];
  const debtMockUSD = loanInfo[1];
  const collateralValueUSD = loanInfo[2];
  const maxBorrowableUSD = loanInfo[3];
  const currentLTVRaw = loanInfo[4];
  const healthFactor = loanInfo[5];

  const currentLTVPercent =
    parseFloat(hre.ethers.utils.formatEther(currentLTVRaw)) * 100;

  console.log("\nLoan info:");
  console.log("Collateral ETH:", hre.ethers.utils.formatEther(collateralETH));
  console.log("Debt MockUSD:", hre.ethers.utils.formatEther(debtMockUSD));
  console.log("Collateral Value USD:", hre.ethers.utils.formatEther(collateralValueUSD));
  console.log("Max Borrowable USD:", hre.ethers.utils.formatEther(maxBorrowableUSD));
  console.log("Current LTV:", currentLTVPercent.toFixed(2), "%");
  console.log("Health Factor:", hre.ethers.utils.formatEther(healthFactor));

  console.log("\nRead-only check completed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});