// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MockPriceFeed {
    uint8 public decimals = 8;
    string public description = "Mock ETH / USD Price Feed";
    uint256 public version = 1;

    int256 private price;
    uint256 private updatedAt;

    constructor(int256 _initialPrice) {
        price = _initialPrice;
        updatedAt = block.timestamp;
    }

    function setPrice(int256 _newPrice) external {
        require(_newPrice > 0, "Invalid price");
        price = _newPrice;
        updatedAt = block.timestamp;
    }

    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 feedUpdatedAt,
            uint80 answeredInRound
        )
    {
        return (
            1,
            price,
            updatedAt,
            updatedAt,
            1
        );
    }
}