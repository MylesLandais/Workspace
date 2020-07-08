package reverse

func Reverse(s string) string {
	rstr := ""
	for i := len(s); i > 0; i-- {
		rstr += string(s[i-1])
	}
	return rstr
}
