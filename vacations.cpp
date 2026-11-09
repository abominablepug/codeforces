// Complete 11/8/26

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
	cin >> n;
	vint dp(n + 1, 0);
	dp[0] = 0;

	for (int i = 1; i <= n; i++) {
		cin >> dp[i];
	}

	int c = 0;
	for (int i = 1; i <= n; i++) {
		if (dp[i] == 0) {
			c++;
		} else if (dp[i] == 1 && dp[i-1] == 1) {
			dp[i] = 0;
			c++;
		} else if (dp[i] == 2 && dp[i-1] == 2) {
			dp[i] = 0;
			c++;
		} else if (dp[i] == 3) {
			if (dp[i-1] == 2) {
				dp[i] = 1;
			} else if (dp[i-1] == 1) {
				dp[i] = 2;
			}
		}
	}

	cout << c << endl;
}

int main() {
	startt

	int t = 1;
	while (t--) {
		solve();
	}

	return 0;
}
