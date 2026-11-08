// Complete 11/7/26

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
	int n, k;
	int a[31] = {};
	cin >> n >> k;
	int sum = 0;

	for (int i = 0; i < n; i++) {
		int j;
		cin >> j;
		for (int i = 0; j != 0; ++i) {
			a[i] += j % 2;
			j /= 2;
		}
	}

	for (int i = 30; i >= 0; i--) {
		int c = n - a[i];
		if (k >= c) {
			sum += pow(2, i);
			k -= c;
		}
	}

	cout << sum << endl;
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
