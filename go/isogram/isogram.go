package isogram

import "strings"

func IsIsogram(s string) bool {
	used := ""
	s = strings.ReplaceAll(s, "-", "")
	s = strings.ReplaceAll(s, " ", "")

	for _, v := range strings.ToLower(s) {
		if strings.Contains(used, string(v)) {
			return false
		} else {
			used += string(v)
		}
	}
	return true
}
