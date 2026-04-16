#include <iostream>
#include <vector>
#include <map>
#include <queue>

std::string isPossible(std::vector<int> &original, std::vector<int> &modified, std::map<int,std::queue<int>> &changes, int l) {
    int current = 0;
    for (int i = 0; i < l; i++) {
        if (original[i] != modified[i]) {
            if (changes[modified[i]].size() == 0) {
                return "NO";
            } else {
                int front = changes[modified[i]].front();
                while (front < current && changes[modified[i]].size() > 0) {
                    changes[modified[i]].pop();
                    front = changes[modified[i]].front();
                }
                if (front < current) {
                    return "NO";
                } else {
                    current = front;
                    changes[modified[i]].pop();
                }
            }
        }
    }
    return "YES";
}

int main() {
    int t;std::cin>>t;
    while(t--) {
        int l;std::cin>>l;
        std::vector<int> original;
        for (int i = 0; i < l; i++) {
            int a;std::cin>>a;
            original.push_back(a);
        }
        std::vector<int> modified;
        for (int i = 0; i < l; i++) {
            int a;std::cin>>a;
            modified.push_back(a);
        }
        int m;std::cin>>m;
        std::map<int,std::queue<int>> changes;
        for (int i = 0; i < m; i++) {
            int a;std::cin>>a;
            changes[a].push(i);
        }
        std::cout << isPossible(original, modified, changes, l) << std::endl;
    }

    return 0;
}