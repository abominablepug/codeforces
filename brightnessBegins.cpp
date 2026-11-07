// Complete 4/13/26

#include <iostream>
#include <vector>
#include <cmath>

using namespace std;

int main() {
	int t, k;
	cin >> t;
	while (t--) {
		long long k;
		cin >> k;
		long long left = k, right = 2e18;
		long long ans = right;

		while (left <= right) {
			long long mid = left + (right - left) / 2;
			long long sq = sqrt(mid);
			if (sq * sq > mid) sq--;
			while ((sq + 1) * (sq + 1) <= mid) sq++;

			if (mid - sq >= k) {
				ans = mid;
				right = mid - 1;
			} else {
				left = mid + 1;
			}
		}
		cout << ans << endl;
	}
	return 0;
}
