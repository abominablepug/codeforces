#include <iostream>

int main() {
    int tests;
    std::cin >> tests;
    for (int _ = 0; _ < tests; _++) {
        int candies;
        std::cin >> candies;
        int candiesToBuy = (3 - (candies % 3)) % 3;
        std::cout << candiesToBuy << std::endl;
    }
    return 0;
}