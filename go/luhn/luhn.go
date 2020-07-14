package luhn

import (
	"strconv"
	"strings"
)

func Valid(s string) bool {
	sum := 0
	s = strings.ReplaceAll(s, " ", "")
	if len(s) > 1 {
		// pad odd length strings to begin with 0
		if len(s)%2 == 1 {
			s = "0" + s
		}
		for i := len(s) - 1; i >= 0; i-- {
			// Parity Bit, Even Numbers only
			d, err := strconv.Atoi(string(s[i]))
			if err != nil {
				return false
			}
			if i%2 == 0 {
				d = d * 2
				if d > 9 {
					d = d - 9
				}
			}
			sum += d
		}
		return (sum % 10) == 0
	}
	return false
}
