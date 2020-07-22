package grains

import (
	"errors"
)

// func powtwo(n uint64) uint64 {
// 	var r uint64 = 1
// 	var i uint64
// 	if n != 0 {
// 		for i = 1; i <= n; i++ {
// 			r = r * 2
// 		}
// 	}
// 	return r
// }

//Square this
func Square(n int) (uint64, error) {
	var total uint64 = 1
	if n == 1 {
		return total, nil
	}
	if n > 1 && n <= 64 {
		for i := 0; i < n-1; i++ {
			total *= 2
		}
		return total, nil
	}
	return total, errors.New("Some error")
}

//Total that
func Total() uint64 {
	var sum uint64 = 0
	var i int
	for i = 1; i <= 64; i++ {
		n, _ := Square(i)
		sum += n
	}
	return sum
}
