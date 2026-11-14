#include <bits/stdc++.h>
#include <algorithm>
#include <unordered_map>
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
	vint h(n);
	for (int i = 0; i < n; i++) {
		cin >> h[i];
	}

	sort(all(h));

	int c = 0;
	int a = 0;

	vint f(n);
	int left = 0, right = n - 1;
	for (int i = 0; i < n; i++) {
		if (i == 0 || h[i] != h[i-1]) {
			a = 1;
			c++;
		} else if (a < 2) {
			a++;
			c++;
		}

		if (i % 2 == 0) {
			f[left++] = h[i];
		} else {
			f[right--] = h[i];
		}
	}

	cout << c << endl;
	for (int i = 0; i < n; i++) {
		cout << f[i] << " ";
	}
	cout << endl;
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
