"""
Problem statement: 1561. maximum number of coins you can pick
Leetcode description : https://leetcode.com/problems/maximum-number-of-coins-you-can-get/description/

"""

from typing import List


class Solution:
    """
    sample testcases:
    Input: piles = [2,4,1,2,7,8]
    Output: 9

    Input: piles = [9,8,7,6,5,1,2,3,4]
    Output: 18

    """
    @classmethod
    def maxCoins(cls, piles: List[int]) -> int:
        if not piles:  # empty piles
            return 0

        # to understand, in sorted piles, Alice picks first (highest), then us -> 2nd highest
        piles.sort()
        piles_len = len(piles)

        # Alice picks -> n-1, n-3, n-5 ...
        # For us, we'll pick -> n-2, n-4, n-6 ...
        # to decide the skips -> triplet - 1
        skips = piles_len // 3  # as to pick from triplet
        pick_idx = piles_len - 2
        max_coins = 0

        while skips:
            max_coins += piles[pick_idx]
            skips -= 1  # deduce the triplet skips
            pick_idx -= 2  # next 2nd highest pick

        return max_coins
