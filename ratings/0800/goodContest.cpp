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

    int f = max(max(n-a, n-b), n-c);

    cout << f << endl;
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