const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  const MOCK_USD_ADDRESS = "0x7e8D9056BeA20ceF8abA9009660128E6657434C6";
  const LENDING_POOL_ADDRESS = "0x07d306Fa4941e7f6734A2bFAD8c03279762032a4";
  const ETH_USD_PRICE_FEED_SEPOLIA =
    "0x694AA1769357215DE4FAC081bf1f309aDC325306";

  const network = await hre.ethers.provider.getNetwork();
  const balance = await deployer.getBalance();

  console.log("Network chainId:", network.chainId);
  console.log("Deployer address:", deployer.address);
  console.log("Deployer balance:", hre.ethers.utils.formatEther(balance), "ETH");

  console.log("\nContract addresses:");
  console.log("MockUSDToken:", MOCK_USD_ADDRESS);
  console.log("LendingPool:", LENDING_POOL_ADDRESS);
  console.log("ETH/USD Price Feed:", ETH_USD_PRICE_FEED_SEPOLIA);

  const mockUSD = await hre.ethers.getContractAt(
    "MockUSDToken",
    MOCK_USD_ADDRESS
  );

  const lendingPool = await hre.ethers.getContractAt(
    "LendingPool",
    LENDING_POOL_ADDRESS
  );

  const priceFeed = await hre.ethers.getContractAt(
    "AggregatorV3Interface",
    ETH_USD_PRICE_FEED_SEPOLIA
  );

  console.log("\nMockUSD info:");
  console.log("Name:", await mockUSD.name());
  console.log("Symbol:", await mockUSD.symbol());

  console.log("\nChainlink Price Feed info:");
  console.log("Description:", await priceFeed.description());
  console.log("Decimals:", await priceFeed.decimals());

  const roundData = await priceFeed.latestRoundData();
  const decimals = await priceFeed.decimals();

  console.log("Raw Chainlink answer:", roundData.answer.toString());
  console.log(
    "ETH/USD from Chainlink:",
    hre.ethers.utils.formatUnits(roundData.answer, decimals),
    "USD"
  );

    console.log("\nLendingPool Oracle Check:");

        const ethPriceData = await lendingPool.getETHPrice();

    const price = ethPriceData.price || ethPriceData[0];
    const priceDecimals = ethPriceData.decimals ?? ethPriceData[1];
    const updatedAt = ethPriceData.updatedAt || ethPriceData[2];

    console.log("Raw ETH price from LendingPool:", price.toString());
    console.log("Decimals from LendingPool:", priceDecimals);
    console.log("UpdatedAt from LendingPool:", updatedAt.toString());

    console.log(
      "ETH/USD from LendingPool:",
      hre.ethers.utils.formatUnits(price, priceDecimals),
      "USD"
    );

  console.log("\nCheck completed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});