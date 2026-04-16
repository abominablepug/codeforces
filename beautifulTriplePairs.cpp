#include <iostream>
#include <vector>
using namespace std;

int main() {
    int t;cin>>t;
    while (t--) {
        int l;cin>>l;
        vector<int> n;
        for (int i = 0; i < l; i++) {
            int a;cin>>a;
            n.push_back(a);
        }
        int count = 0;
        for (int i = 0; i < l - 3; i++) {
            if (n[i] != n[i+1] && n[i+1] == n[i+2] && n[i+2] == n[i+3]) {
                count++;
            } else if (n[i] == n[i+1] && n[i+1] != n[i+2] && n[i+2] == n[i+3]) {
                count++;
            } else if (n[i] == n[i+1] && n[i+1] == n[i+2] && n[i+2] != n[i+3]) {
                count++;
            }
        }
        cout << count << endl;
    }
    return 0;
}