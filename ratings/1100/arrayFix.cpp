// Complete 11/1/25

#include <iostream>
#include <vector>

bool isSorted(std::vector<int> &nums) {
    int i = 0;
    while (i < nums.size() - 1) {
        if (nums[i] > nums[i + 1]) {
            return false;
        }
        i++;
    }
    return true;
};

bool isPossible(std::vector<int> &nums) {
    while (!isSorted(nums)) {
        for (int i = 0; i < nums.size() - 1; i++) {
            if (nums[i] > nums[i + 1]) {
                if (nums[i] < 10) {
                    return false;
                } else {
                    nums.insert(nums.begin() + i, nums[i] % 10);
                    nums.insert(nums.begin() + i, nums[i + 1] / 10);
                    nums.erase(nums.begin() + i + 2);
                    continue;
                }
            }
        }
    }
    return true;
}

int main() {
    int tests;
    std::cin >> tests;
    for (int _ = 0; _ < tests; _++) {
        int length;
        std::cin >> length;
        std::vector<int> nums(length);
        for (int i = 0; i < length; i++) {
            std::cin >> nums[i];
        };

        if (isPossible(nums)) {
            std::cout << "YES" << std::endl;
        } else {
            std::cout << "NO" << std::endl;
        }
    }
    return 0;
}
