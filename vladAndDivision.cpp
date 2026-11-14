#include <bits/stdc++.h>
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

	int c = 0, o = 2147483647;
	map<int, int> p;
	for (int i = 0; i < n; i++) {
		int t = o-a[i];
		if (p[t] > 0) {
			p[t]--;
		} else {
			c++;
			p[a[i]]++;
		}
	}

	cout << c << endl;
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
