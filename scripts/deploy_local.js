const { ethers } = require("hardhat");

function formatToken(value) {
  return ethers.utils.formatEther(value);
}

function formatPctFrom1e18(value) {
  return (Number(ethers.utils.formatUnits(value, 18)) * 100).toFixed(2);
}

function formatRatioFrom1e18(value) {
  return Number(ethers.utils.formatUnits(value, 18)).toFixed(4);
}

async function printLoanInfo(pool, userAddress, label) {
  const info = await pool.getLoanInfo(userAddress);

  console.log(`\n--- ${label} ---`);
  console.log("Collateral ETH:", formatToken(info.collateralETH));
  console.log("Debt MockUSD:", formatToken(info.debtMockUSD));
  console.log("Collateral Value USD:", formatToken(info.collateralValueUSD));
  console.log("Max Borrowable MockUSD:", formatToken(info.maxBorrowable));
  console.log("Current LTV:", formatPctFrom1e18(info.currentLTV) + "%");

  if (info.healthFactor.eq(ethers.constants.MaxUint256)) {
    console.log("Health Factor: INF");
  } else {
    console.log("Health Factor:", formatRatioFrom1e18(info.healthFactor));
  }
}

async function main() {
  const [deployer, borrower, liquidator] = await ethers.getSigners();

  console.log("Deployer:", deployer.address);
  console.log("Borrower:", borrower.address);
  console.log("Liquidator:", liquidator.address);

  // 1. Deploy MockUSD token
  const MockUSDToken = await ethers.getContractFactory("MockUSDToken");
  const mockUSD = await MockUSDToken.deploy();
  await mockUSD.deployed();

  // 2. Deploy mock ETH/USD price feed
  // Chainlink price feed thường dùng 8 decimals.
  // 3,500 USD = 3500 * 10^8 = 350000000000
  const initialETHPrice = ethers.BigNumber.from("350000000000");

  const MockPriceFeed = await ethers.getContractFactory("MockPriceFeed");
  const priceFeed = await MockPriceFeed.deploy(initialETHPrice);
  await priceFeed.deployed();

  // 3. Deploy LendingPool
  const LendingPool = await ethers.getContractFactory("LendingPool");
  const pool = await LendingPool.deploy(mockUSD.address, priceFeed.address);
  await pool.deployed();

  // 4. Cho phép LendingPool mint/burn MockUSD
  await mockUSD.setLendingPool(pool.address);

  console.log("\nContracts deployed:");
  console.log("MockUSD:", mockUSD.address);
  console.log("MockPriceFeed:", priceFeed.address);
  console.log("LendingPool:", pool.address);

  const priceData = await pool.getETHPrice();
  console.log("\nInitial ETH/USD price:", Number(priceData.price.toString()) / 1e8);

  // 5. Borrower nạp 0.05 ETH làm collateral
  await pool.connect(borrower).depositCollateral({
    value: ethers.utils.parseEther("0.05"),
  });

  await printLoanInfo(pool, borrower.address, "After borrower deposits 0.05 ETH");

  // 6. Borrower vay 100 MockUSD
  await pool.connect(borrower).borrow(ethers.utils.parseEther("100"));

  await printLoanInfo(pool, borrower.address, "After borrower borrows 100 MockUSD");

  // 7. Liquidator tạo sẵn 100 MockUSD để có tiền thanh lý
  await pool.connect(liquidator).depositCollateral({
    value: ethers.utils.parseEther("0.10"),
  });

  await pool.connect(liquidator).borrow(ethers.utils.parseEther("100"));

  await printLoanInfo(pool, liquidator.address, "Liquidator position before liquidation");

  // 8. Stress test: ETH giảm từ 3,500 USD xuống 2,500 USD
  const stressedETHPrice = ethers.BigNumber.from("250000000000");
  await priceFeed.setPrice(stressedETHPrice);

  const stressedPriceData = await pool.getETHPrice();
  console.log("\nStress Test ETH/USD price:", Number(stressedPriceData.price.toString()) / 1e8);

  await printLoanInfo(pool, borrower.address, "Borrower after ETH price drops");

  // 9. Liquidator approve cho LendingPool đốt 100 MockUSD
  await mockUSD
    .connect(liquidator)
    .approve(pool.address, ethers.utils.parseEther("100"));

  // 10. Liquidate borrower
  await pool.connect(liquidator).liquidate(borrower.address);

  await printLoanInfo(pool, borrower.address, "Borrower after liquidation");
  await printLoanInfo(pool, liquidator.address, "Liquidator after liquidation");

  console.log("\nLocal test completed successfully.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});