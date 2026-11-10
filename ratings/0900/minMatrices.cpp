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

const int N = 1005;

void solve() {
    int n, k;
    cin >> n >> k;

    if (k < n || k > 2*n - 1) {
        cout << -1 << endl;
        return;
    }

    int c = k;
    int a[N][N];
    for (int i = n - 1; i >= 0; i--) {
        a[i][i] = c;
        c--;
    }
    c = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i == j) continue;

            if (c < k - n || c > k) {
                c++;
            } else {
                c += n + 1;
            }
            a[i][j] = c;
        }
    }

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            cout << a[i][j] << " ";
        }
        cout << endl;
    }
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