// Complete 11/8/26

#include <bits/stdc++.h>
#include <unordered_map>
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
	int n;
	cin >> n;
	unordered_map<int, int> m;
	vint a(n + 1, 0);
	for (int i = 1; i <= n; i++) {
		cin >> a[i];
	}
	vint dp(n + 1, 0);
	vint best(n + 1, 1e9);

	for (int i = 1; i <= n; i++) {
		int c = a[i];
		dp[i] = dp[i - 1] + 1;
		dp[i] = min(dp[i], best[c]);

		best[c] = min(best[c], dp[i - 1]);
	}

	cout << n - dp[n] << endl;
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
