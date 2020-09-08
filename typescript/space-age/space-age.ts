
class SpaceAge{
    seconds: number;

    constructor(s:number) {
        this.seconds = s;
    }

    round(value: number, precision:number) {
        let multiplier = Math.pow(10, precision || 0);
        return Math.round(value * multiplier) / multiplier;
    }

    onEarth(): number{
        return this.round(this.seconds / 31557600, 2);
    }

    onMercury(): number{
        return this.round(this.seconds / 31557600 / 0.2408467, 2);
    }

    onVenus(): number{
        return this.round(this.seconds / 31557600 / 0.61519726, 2);
    }

    onMars(): number{
        return this.round(this.seconds/ 31557600 / 1.8808158,2);
    }

    onJupiter(): number{
        return this.round(this.seconds / 31557600 / 11.862615,2);
    }

    onSaturn(): number{
        return this.round(this.seconds / 31557600 / 29.447498,2);
    }

    onUranus(): number{
        return this.round(this.seconds / 31557600 / 84.016846, 2);
    }

    onNeptune(): number{
        return this.round(this.seconds / 31557600 / 164.79132,2 );
    }



}

export default SpaceAge