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

    int m = 1;
    int c = 0;
    vint d;
    for (int i = n-1; i >= 0; i--) {
        if (a[i] * m > 0) {
            c++;
            d.pb(i + 1);
            m *= -1;
        }
    }

    cout << c << endl;
    for (int i : d) {
        cout << i << " ";
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