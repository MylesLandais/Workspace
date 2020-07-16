package grains

func powtwo(n uint64) uint64 {
	var r uint64 = 1
	var i uint64
	if n != 0 {
		for i = 1; i <= n; i++ {
			r = r * 2
		}
	}
	return r
}

func Square(n uint64) (uint64, error) {
	i := powtwo(n)
	return i, nil
}

func Total() uint64 {
	var sum uint64 = 0
	var i uint64
	for i = 0; i <= 63; i++ {
		n, _ := uint64(Square(i))
		sum += n
	}
	return sum
}
