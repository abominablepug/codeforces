#include <bits/stdc++.h>
#include <cmath>
using namespace std;

using ll = long long;
#define startt ios_base::sync_with_stdio(false);cin.tie(0);
#define vint vector<int>
#define all(v) v.begin(), v.end()
#define pb push_back
#define NO cout << "NO" << "\n"
#define YES cout << "YES" << "\n"

void solve() {
    int n, k, q;
    cin >> n >> k >> q;
    vint a(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i];
    }

    int c = 1;
    ll s = 0;
    for (int i : a) {
        if (i <= q) {
            s += max(0, c - k + 1);
            c++;
        } else {
            c = 1;
        }
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