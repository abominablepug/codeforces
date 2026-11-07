// Complete 11/2/25

#include <iostream>
#include <vector>

int main() {
    int tests;
    std::cin >> tests;
    for (int _ = 0; _ < tests; _++) {
        int length;
        std::cin >> length;
        int prev = -1;
        std::vector<int> nums;
        for (int i = 0; i < length; i++) {
            int num; std::cin >> num;
            if (num != prev) {
                nums.push_back(num);
                prev = num;
            }
        }
        int answer = 2;
        if (nums.size() == 1) {
            std::cout << 1 << std::endl;
        } else {
            for (int i = 1; i < nums.size() - 1; i++) {
                if (nums[i] < nums[i-1] && nums[i] < nums[i+1]) {
                    answer++;
                } else if (nums[i] > nums[i-1] && nums[i] > nums[i+1]) {
                    answer++;
                }
            }
            std::cout << answer << std::endl;
        }
    }
}
