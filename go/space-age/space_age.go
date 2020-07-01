package space

type Planet string

func Age(t float64, p Planet) float64 {
	switch p {
	case "Mercury":
		return (t / 31557600) / 0.2408467
	case "Venus":
		return (t / 31557600) / 0.61519726
	case "Earth":
		return (t / 31557600)
	case "Mars":
		return (t / 31557600) / 1.8808158
	case "Jupiter":
		return (t / 31557600) / 11.862615
	case "Saturn":
		return (t / 31557600) / 29.447498
	case "Uranus":
		return (t / 31557600) / 84.016846
	case "Neptune":
		return (t / 31557600) / 164.79132
	}
	return 0
}
