// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./MockUSDToken.sol";
import "./interfaces/AggregatorV3Interface.sol";

contract LendingPool {
    MockUSDToken public mockUSD;
    AggregatorV3Interface public priceFeed;

    uint256 public constant BPS_DIVISOR = 10_000;
    uint256 public constant MAX_LTV_BPS = 6_000; // 60%
    uint256 public constant LIQUIDATION_THRESHOLD_BPS = 7_500; // 75%
    uint256 public constant LIQUIDATION_BONUS_BPS = 500; // 5%
    uint256 public constant PRECISION = 1e18;

    bool private locked;

    struct LoanPosition {
        uint256 collateralETH;
        uint256 debtMockUSD;
    }

    mapping(address => LoanPosition) public positions;

    event CollateralDeposited(address indexed user, uint256 amountETH);
    event Borrowed(address indexed user, uint256 amountMockUSD);
    event Repaid(address indexed user, uint256 amountMockUSD);
    event CollateralWithdrawn(address indexed user, uint256 amountETH);
    event Liquidated(
        address indexed borrower,
        address indexed liquidator,
        uint256 debtRepaid,
        uint256 collateralSeized
    );

    modifier nonReentrant() {
        require(!locked, "Reentrancy blocked");
        locked = true;
        _;
        locked = false;
    }

    constructor(address _mockUSD, address _priceFeed) {
        require(_mockUSD != address(0), "Invalid MockUSD address");
        require(_priceFeed != address(0), "Invalid price feed address");

        mockUSD = MockUSDToken(_mockUSD);
        priceFeed = AggregatorV3Interface(_priceFeed);
    }

    receive() external payable {
        depositCollateral();
    }

    function getETHPrice()
        public
        view
        returns (
            uint256 price,
            uint8 decimals,
            uint256 updatedAt
        )
    {
        (, int256 answer, , uint256 feedUpdatedAt, ) = priceFeed.latestRoundData();

        require(answer > 0, "Invalid oracle price");

        return (uint256(answer), priceFeed.decimals(), feedUpdatedAt);
    }

    function depositCollateral() public payable {
        require(msg.value > 0, "Collateral must be greater than zero");

        positions[msg.sender].collateralETH += msg.value;

        emit CollateralDeposited(msg.sender, msg.value);
    }

    function getCollateralValueUSD(address user) public view returns (uint256) {
        LoanPosition memory position = positions[user];

        if (position.collateralETH == 0) {
            return 0;
        }

        (uint256 price, uint8 priceDecimals, ) = getETHPrice();

        return (position.collateralETH * price) / (10 ** priceDecimals);
    }

    function getMaxBorrowable(address user) public view returns (uint256) {
        uint256 collateralValueUSD = getCollateralValueUSD(user);

        return (collateralValueUSD * MAX_LTV_BPS) / BPS_DIVISOR;
    }

    function getCurrentLTV(address user) public view returns (uint256) {
        uint256 collateralValueUSD = getCollateralValueUSD(user);
        uint256 debt = positions[user].debtMockUSD;

        if (collateralValueUSD == 0) {
            return 0;
        }

        return (debt * PRECISION) / collateralValueUSD;
    }

    function getHealthFactor(address user) public view returns (uint256) {
        uint256 debt = positions[user].debtMockUSD;

        if (debt == 0) {
            return type(uint256).max;
        }

        uint256 collateralValueUSD = getCollateralValueUSD(user);
        uint256 adjustedCollateralValue = (collateralValueUSD * LIQUIDATION_THRESHOLD_BPS) / BPS_DIVISOR;

        return (adjustedCollateralValue * PRECISION) / debt;
    }

    function borrow(uint256 amountMockUSD) external nonReentrant {
        require(amountMockUSD > 0, "Borrow amount must be greater than zero");

        LoanPosition storage position = positions[msg.sender];

        require(position.collateralETH > 0, "No collateral");

        uint256 newDebt = position.debtMockUSD + amountMockUSD;
        uint256 maxBorrowable = getMaxBorrowable(msg.sender);

        require(newDebt <= maxBorrowable, "Borrow amount exceeds max LTV");

        position.debtMockUSD = newDebt;

        mockUSD.mint(msg.sender, amountMockUSD);

        emit Borrowed(msg.sender, amountMockUSD);
    }

    function repay(uint256 amountMockUSD) external nonReentrant {
        require(amountMockUSD > 0, "Repay amount must be greater than zero");

        LoanPosition storage position = positions[msg.sender];

        require(position.debtMockUSD > 0, "No debt");

        uint256 repayAmount = amountMockUSD;

        if (repayAmount > position.debtMockUSD) {
            repayAmount = position.debtMockUSD;
        }

        position.debtMockUSD -= repayAmount;

        mockUSD.burnFrom(msg.sender, repayAmount);

        emit Repaid(msg.sender, repayAmount);
    }

    function withdrawCollateral(uint256 amountETH) external nonReentrant {
        require(amountETH > 0, "Withdraw amount must be greater than zero");

        LoanPosition storage position = positions[msg.sender];

        require(position.collateralETH >= amountETH, "Insufficient collateral");

        position.collateralETH -= amountETH;

        if (position.debtMockUSD > 0) {
            require(getHealthFactor(msg.sender) >= PRECISION, "Health factor too low");
        }

        (bool success, ) = payable(msg.sender).call{value: amountETH}("");
        require(success, "ETH transfer failed");

        emit CollateralWithdrawn(msg.sender, amountETH);
    }

    function liquidate(address borrower) external nonReentrant {
        require(borrower != address(0), "Invalid borrower");
        require(borrower != msg.sender, "Cannot liquidate yourself");

        LoanPosition storage borrowerPosition = positions[borrower];

        require(borrowerPosition.debtMockUSD > 0, "Borrower has no debt");
        require(getHealthFactor(borrower) < PRECISION, "Position is not liquidatable");

        uint256 debtToRepay = borrowerPosition.debtMockUSD;

        (uint256 price, uint8 priceDecimals, ) = getETHPrice();

        uint256 collateralEquivalentETH = (debtToRepay * (10 ** priceDecimals)) / price;
        uint256 collateralWithBonus = (collateralEquivalentETH * (BPS_DIVISOR + LIQUIDATION_BONUS_BPS)) / BPS_DIVISOR;

        uint256 collateralToSeize = collateralWithBonus;

        if (collateralToSeize > borrowerPosition.collateralETH) {
            collateralToSeize = borrowerPosition.collateralETH;
        }

        borrowerPosition.debtMockUSD = 0;
        borrowerPosition.collateralETH -= collateralToSeize;

        mockUSD.burnFrom(msg.sender, debtToRepay);

        (bool success, ) = payable(msg.sender).call{value: collateralToSeize}("");
        require(success, "ETH transfer failed");

        emit Liquidated(borrower, msg.sender, debtToRepay, collateralToSeize);
    }

    function getLoanInfo(address user)
        external
        view
        returns (
            uint256 collateralETH,
            uint256 debtMockUSD,
            uint256 collateralValueUSD,
            uint256 maxBorrowable,
            uint256 currentLTV,
            uint256 healthFactor
        )
    {
        LoanPosition memory position = positions[user];

        collateralETH = position.collateralETH;
        debtMockUSD = position.debtMockUSD;
        collateralValueUSD = getCollateralValueUSD(user);
        maxBorrowable = getMaxBorrowable(user);
        currentLTV = getCurrentLTV(user);
        healthFactor = getHealthFactor(user);
    }
}