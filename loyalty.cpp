#include <iostream>
#include <algorithm>

using namespace std;

int main() {
	#define int long long
	int t;
	cin >> t;
	while (t--) {
		int n, x;
		cin >> n >> x;
		int numbers[n];
		for (int i = 0; i < n; i++) {
			cin >> numbers[i];
		}

		sort(numbers, numbers + n);
		int l = 0, r = n - 1;
		int i = 0;
		int ans[n];
		int p = 0;
		int sum = 0;
		while (l <= r) {
			if (sum + numbers[r] < x) {
				sum += numbers[l];
				ans[i] = numbers[l];
				i++;
				l++;
			} else {
				sum = (sum + numbers[r]) % x;
				ans[i] = numbers[r];
				p += numbers[r];
				i++;
				r--;
			}
		}
		cout << p << endl;
		for (int i = 0; i < n; i++) {
			cout << ans[i] << " ";
		}
		cout << endl;
	}
}
