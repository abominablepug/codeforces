#include <iostream>

int main() {
    int sum = 0;
    for (int i = 0; i < 4; i++) {
        int num;std::cin>>num;
        sum+=num;
    }
    std::cout<<15-sum<<std::endl;
}