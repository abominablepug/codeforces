// Complete 11/8/26

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


void solve() {
	int n, a, b, c;
	cin >> n >> a >> b >> c;
	vint dp(n + 1, -1e9);
	dp[0] = 0;

	for (int i = 1; i <= n; i++) {
		if (i >= a) dp[i] = max(dp[i], dp[i-a] + 1);
		if (i >= b) dp[i] = max(dp[i], dp[i-b] + 1);
		if (i >= c) dp[i] = max(dp[i], dp[i-c] + 1);
	}

	cout << dp[n] << endl;
}

int main() {
	startt

	int t = 1;
	while (t--) {
		solve();
	}

	return 0;
}
