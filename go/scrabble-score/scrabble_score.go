package scrabble

import "strings"

func Score(s string) int {
	rcount := 0

	for _, v := range strings.ToUpper(s) {
		if strings.Contains("A, E, I, O, U, L, N, R, S, T", string(v)) {
			rcount += 1
		}
		if strings.Contains("D, G", string(v)) {
			rcount += 2
		}
		if strings.Contains("B, C, M, P ", string(v)) {
			rcount += 3
		}
		if strings.Contains("F, H, V, W, Y", string(v)) {
			rcount += 4
		}
		if strings.Contains("K", string(v)) {
			rcount += 5
		}
		if strings.Contains("J, X", string(v)) {
			rcount += 8
		}
		if strings.Contains("Q, Z", string(v)) {
			rcount += 10
		}
	}
	return rcount
}
