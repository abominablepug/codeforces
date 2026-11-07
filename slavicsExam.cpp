// Complete 11/7/26

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

string s, t;

void solve() {
	cin >> s >> t;

	int j = 0;
	int n = s.length();
	int m = t.length();
	for (int i = 0; i < n && j < m; i++) {
		if (s[i] == t[j]) {
			j++;
		} else if (s[i] == '?') {
			s[i] = t[j];
			j++;
		}
	}

	if (j < m) {
		NO;
	} else {
		YES;
		replace(all(s), '?', 'a');
		cout << s << endl;
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
