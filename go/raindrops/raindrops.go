package raindrops

import "strconv"

func Convert(i int) string {
	rstr := ""
	if i%3 == 0 {
		rstr += "Pling"
	}
	if i%5 == 0 {
		rstr += "Plang"
	}
	if i%7 == 0 {
		rstr += "Plong"
	}
	if rstr == "" {
		rstr = strconv.Itoa(i)
	}
	return rstr
}
