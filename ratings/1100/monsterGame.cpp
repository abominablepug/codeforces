// Completed 11/7/26

#include <bits/stdc++.h>
#include <vector>
#include <algorithm>
#include <functional>
using namespace std;

using ll = long long;

void solve() {
	int n;
	cin >> n;
	vector<int> a(n), b(n);
	for (int i = 0; i < n; i++) {
		cin >> a[i];
	}
	for (int i = 0; i < n; i++) {
		cin >> b[i];
	}
	sort(a.begin(), a.end(), greater<int>());

	int t = 0;
	ll nc = 0;
	ll ma = 0;
	for (int i = 0; nc < n; i++) {
		nc++;
		t += b[i];
		if (t > n) break;

		ma = max(ma, a[t - 1] * nc);
	}

	cout << ma << '\n';
}

int main() {
	ios_base::sync_with_stdio(false);
	cin.tie(NULL);

	int t = 1;
	cin >> t;
	while (t--) {
		solve();
	}

	return 0;
}
