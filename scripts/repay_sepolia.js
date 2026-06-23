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

  console.log("Testing partial repay on Sepolia...");
  console.log("User:", user.address);

  const repayAmount = hre.ethers.utils.parseEther("0.2");

  const balanceBefore = await mockUSD.balanceOf(user.address);
  const loanBefore = await lendingPool.getLoanInfo(user.address);

  console.log("\nBefore repay:");
  console.log("MockUSD balance:", hre.ethers.utils.formatEther(balanceBefore));
  console.log("Debt:", hre.ethers.utils.formatEther(loanBefore[1]));
  console.log("Health Factor:", hre.ethers.utils.formatEther(loanBefore[5]));

  console.log("\nApproving LendingPool to spend:", hre.ethers.utils.formatEther(repayAmount), "MockUSD");

  const approveTx = await mockUSD.approve(LENDING_POOL_ADDRESS, repayAmount);
  await approveTx.wait();

  console.log("Approve successful.");

  console.log("\nRepaying:", hre.ethers.utils.formatEther(repayAmount), "MockUSD");

  const repayTx = await lendingPool.repay(repayAmount);
  await repayTx.wait();

  console.log("Repay successful.");

  const balanceAfter = await mockUSD.balanceOf(user.address);
  const loanAfter = await lendingPool.getLoanInfo(user.address);

  console.log("\nAfter repay:");
  console.log("MockUSD balance:", hre.ethers.utils.formatEther(balanceAfter));
  console.log("Debt:", hre.ethers.utils.formatEther(loanAfter[1]));
  console.log("Health Factor:", hre.ethers.utils.formatEther(loanAfter[5]));

  console.log("\nPartial repay test completed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});