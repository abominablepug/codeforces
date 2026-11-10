// Complete 11/10/26

#include <bits/stdc++.h>
#include <unordered_set>
#include <stack>
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

	stack<int> l;
	unordered_set<int> f;
	for (int i = 0; i < s.length(); i++) {
		if (s[i] == '1') {
			l.push(i + 1);
		} else if (s[i] == '2') {
			if (l.empty()) {
				f.insert(i + 1);
			} else {
				f.insert(l.top());
				l.pop();
			}
		} else if (s[i] == '3') {
			f.insert(i + 1);
		}
	}

	cout << n - f.size() << endl;
	for (int i = 0; i < n; i++) {
		if (!f.contains(i + 1)) {
			cout << i + 1 << " ";
		}
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
