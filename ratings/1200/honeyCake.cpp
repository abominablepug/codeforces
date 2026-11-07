// Complete 4/15/26

#include <iostream>
#include <algorithm>
#include <vector>

using namespace std;

vector<long long> prime(long long n) {
	vector<long long> p;
	for (long long i = 1; i * i <= n; i++) {
		if (n % i == 0) {
			p.push_back(i);
			if (i != n / i) p.push_back(n / i);
		}
	}
	sort(p.begin(), p.end());
	return p;
}

int main() {
	#define int long long
	int w, h, d, n;
	cin >> w >> h >> d >> n;
	vector<int> p = prime(n);
	for (int x : p) {
		if (w % x != 0) continue;
		for (int y : p) {
			if (h % y != 0) continue;
			int r = x * y;
			if (r > n || n % r != 0) continue;
			int z = n / r;
			if (d % z == 0) {
				cout << (x - 1) << " " << (y - 1) << " " << (z - 1) << endl;
				return 0;
			}
		}
	}
	cout << -1 << endl;
	return 0;
}
