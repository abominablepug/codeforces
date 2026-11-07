// Complete 11/7/26

#include <bits/stdc++.h>
using namespace std;

using ll = long long;
const int N = 1005;

int a[N][N];
int n, m;

int s(int i, int j) {
	if (i < 0 || j < 0 || i >= n || j >= m || !a[i][j]) {
		return 0;
	}
	int v = a[i][j];
	a[i][j] = 0;
	return v + s(i,j-1) + s(i-1,j) + s(i,j+1) + s(i,j-1) + s(i+1,j);
}

void solve() {
	cin >> n >> m;
	
	for (int i = 0; i < n; i++) {
		for (int j = 0; j < m; j++) {
			cin >> a[i][j];
		}
	}

	int max = 0;
	for (int i = 0; i < n; i++) {
		for (int j = 0; j < m; j++) {
			if (a[i][j] > 0) {
				int c = s(i, j);
				if (c > max) max = c;
			}
		}
	}

	cout << max << endl;
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
