#include <iostream>
#include <vector>

int cost(std::vector<int> &a) {
    for(int i = 0; i < a.size(); i++){
        int l = 1, r = i + 1;
        while(l <= r){
            int m = (l + r) / 2;
            if(a[i - m + 1] >= m){
                l = m + 1;
            }else{
                r = m - 1;
            }
        }
        std::cout << r << ' ';
    }
    return 0;
}

int main() {
    int t;std::cin>>t;
    while (t--) {
        int l;std::cin>>l;
        std::vector<int> a;
        for (int i = 0; i < l; i++) {
            int n;std::cin>>n;
            a.push_back(n);
        }
        cost(a);
        std::cout << std::endl;
    }

    return 0;
}