package hamming

import "fmt"

func Distance(a, b string) (int, error) {
	count := 0
	if len(a) == len(b) {
		for k, v := range a {
			if string(v) != string(b[k]) {
				count += 1
			}
		}
		return count, nil
	}
	return 0, fmt.Errorf("string length not equal")
}
