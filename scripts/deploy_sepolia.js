const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  console.log("Deploying contracts to Sepolia...");
  console.log("Deployer address:", deployer.address);

  const balance = await deployer.getBalance();
  console.log("Deployer balance:", hre.ethers.utils.formatEther(balance), "ETH");

  // Chainlink ETH/USD Price Feed on Sepolia
  const ETH_USD_PRICE_FEED_SEPOLIA =
    "0x694AA1769357215DE4FAC081bf1f309aDC325306";

  console.log("Using Chainlink ETH/USD Price Feed:");
  console.log(ETH_USD_PRICE_FEED_SEPOLIA);

  // 1. Deploy MockUSDToken
  const MockUSDToken = await hre.ethers.getContractFactory("MockUSDToken");
  const mockUSD = await MockUSDToken.deploy();
  await mockUSD.deployed();

  console.log("MockUSDToken deployed to:", mockUSD.address);

  // 2. Deploy LendingPool with MockUSDToken and Chainlink Price Feed
  const LendingPool = await hre.ethers.getContractFactory("LendingPool");
  const lendingPool = await LendingPool.deploy(
    mockUSD.address,
    ETH_USD_PRICE_FEED_SEPOLIA
  );
  await lendingPool.deployed();

  console.log("LendingPool deployed to:", lendingPool.address);

  // 3. Allow LendingPool to mint/burn MockUSD
  const tx = await mockUSD.setLendingPool(lendingPool.address);
  await tx.wait();

  console.log("LendingPool set in MockUSDToken successfully.");

  console.log("\nDeployment completed.");
  console.log("--------------------------------");
  console.log("Network: Sepolia");
  console.log("MockUSDToken:", mockUSD.address);
  console.log("LendingPool:", lendingPool.address);
  console.log("ETH/USD Price Feed:", ETH_USD_PRICE_FEED_SEPOLIA);
  console.log("--------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});