// Complete 11/10/26

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
	vint a(n);
	for (int i = 0; i < n; i++) {
		cin >> a[i];
	}

	int t = 0;
	for (int i = n - 1; i >= 0; i--) {
		t = t + (a[i] - t) * 2;
	}

	cout << t / 2 << endl;
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
