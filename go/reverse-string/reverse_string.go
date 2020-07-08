package reverse

import (
	"fmt"
	"unicode/utf8"
)

func Reverse(s string) string {
	rstr := ""
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		rstr = fmt.Sprintf("%c", r) + rstr
		i += size
	}
	return rstr
}
