// Complete 4/16/26

#include <iostream>
#include <string>
#include <unordered_map>

using namespace std;

int main() {
	int t;
	cin >> t;
	unordered_map<string, int> values = {{"**", -1}, {">*", -1}, {"*<", -1}, {"><", -1}, {"*>", 1}, {">>", 1}, {"<*", 1}, {"<<", 1}};
	while (t--) {
		string s;
		cin >> s;
		int n = s.size();
		int l = 0, r = 0, a = 0;

		for (int i = 0; i < n; i++) {
			int v = values[s.substr(i, 2)];
			if (v == -1) {
				a = -1;
			}
			if (s[i] == '*') {
				l++;
				r++;
			} else if (s[i] == '>') {
				r++;
			} else {
				l++;
			}
		}
		cout << (a == -1 ? -1 : max(l, r)) << endl;
	}

	return 0;
}
