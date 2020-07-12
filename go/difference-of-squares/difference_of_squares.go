package diffsquares

func SquareOfSum(n int) int{
	sum := 0
	i := 1
	for i <= n{
		sum += i
		i++
	}
	return sum * sum
}

func SumOfSquares(n int) int{
	sum := 0
	i := 1
	for i <= n{
		sum += i*i
		i++
	}
	return sum
}

func Difference(n int) int{
	return SquareOfSum(n) - SumOfSquares(n)
}
