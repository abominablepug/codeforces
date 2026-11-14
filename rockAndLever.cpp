#include <bits/stdc++.h>
using namespace std;

using ll = long long;
#define startt ios_base::sync_with_stdio(false);cin.tie(0);
#define vint vector<int>
#define all(v) v.begin(), v.end()
#define pb push_back
#define NO cout << "NO" << "\n"
#define YES cout << "YES" << "\n"

int bitSize(int ai) {
    int c = 0;
    while (ai != 0) {
        ai /= 2;
        c++;
    }

    return c;
}

ll t(int fi) {
    ll k = fi - 1;
    return k * (k + 1) / 2;
}

void solve() {
    int n;
    cin >> n;
    vint a(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i];
    }

    int f[31] = {};
    for (int ai : a) {
        f[bitSize(ai) - 1]++;
    }

    ll s = 0;
    for (int fi : f) {
        s += t(fi);
    }

    cout << s << endl;
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