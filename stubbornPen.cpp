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
    string s;
    cin >> n >> s;

    char m = 'R';
    int c = 0;
    for (int i = 0; i < s.length(); i++) {
        if (s[i] != m) {
            c++;
            if (m == 'R') {
                m = 'B';
            } else {
                m = 'R';
            }
        }

        if (m == 'R') {
            m = 'B';
        } else {
            m = 'R';
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