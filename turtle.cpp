#include <iostream>
#include <algorithm>

using namespace std;

int main() {
	#define int long long
	int t;
	cin >> t;
	while (t--) {
		int n;
		cin >> n;
		int a[n];
		for (int i = 0; i < n; i++) {
			cin >> a[i];
		}
		bool p = false;
		sort(a, a + n);
		if (a[0] != a[1]) {
			p = true;
		} else {
			for (int i = 1; i < n; i++) {
				if (a[i] % a[0] != 0) {
					p = true;
					break;
				}
			}
		}
		cout << (p ? "YES" : "NO") << endl;

	}

	return 0;
}
