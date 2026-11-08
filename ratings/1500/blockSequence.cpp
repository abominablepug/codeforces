// Complete 11/7/26

#include <bits/stdc++.h>
#include <algorithm>
using namespace std;

using ll = long long;
#define startt ios_base::sync_with_stdio(false);cin.tie(0);
#define vint vector<int>
#define all(v) v.begin(), v.end()
#define pb push_back
#define NO cout << "NO" << "\n"
#define YES cout << "YES" << "\n"

const int N = 2e5 + 5;

void solve() {
	int n, a[N];
	cin >> n;
	for (int i = 0; i < n; i++) {
		cin >> a[i];
	}

	vint dp(n + 1, 0);

	for (int i = n - 1; i >= 0; i--) {
		int j = 1e9;
		int d = 1 + dp[i + 1];
		if (i + a[i] + 1 <= n) {
			j = dp[i + a[i] + 1];
		}
		dp[i] = min(j, d);
	}

	cout << dp[0] << endl;
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
