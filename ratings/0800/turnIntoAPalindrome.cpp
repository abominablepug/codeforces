#include <bits/stdc++.h>
using namespace std;

using ll = long long;
#define startt ios_base::sync_with_stdio(false);cin.tie(0);
#define vint vector<int>
#define all(v) v.begin(), v.end()
#define pb push_back
#define NO cout << "NO" << "\n"
#define YES cout << "YES" << "\n"

void solve() {
    int n;
    char c;
    string s;
    cin >> n >> c >> s;

    int l = 0, r = n - 1, f = 0;
    for (int i = 0; i < n / 2; i ++) {
        if (s[l] != s[r]) {
            if (s[l] != c) f++;
            if (s[r] != c) f++;
        }
        
        l++;
        r--;
    }

    cout << f << endl;
}

int main() {
	startt

	int t = 1;
	cin >> t;
	while (t--) {
		solve();
	}

	return 0;
}