#include <iostream>

using namespace std;

int main() {
	#define int long long
	int t;
	cin >> t;
	while (t--) {
		int n, lv, rv, w = 0, l = 0, r = 0;
		cin >> n >> lv >> rv;

		int c[n];
		for (int i = 0; i < n; i++) {
			cin >> c[i];
		}

		int s = 0;
		while (l <= r && r < n) {
			s+=c[r];
			if (s < lv) {
				r++;
			} else if (s > rv && l == r) {
				r++;
				l++;
				s=0;
			} else if (s > rv) {
				s-=c[l];
				s-=c[r];
				l++;
			} else {
				w++;
				r++;
				l=r;
				s=0;
			}
		}
		cout << w << endl;
	}
}
