// Complete 11/2/25

#include <iostream>

int main() {
    int x = 1;
    for (int i = 0; i < 4; i++) {
        int num;std::cin>>num;
        x^=num;
    }
    std::cout<<x<<std::endl;
}
