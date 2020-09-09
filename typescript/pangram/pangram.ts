class pangram{
    s:string;

    constructor(s:string) {
        this.s = s.toLowerCase();
    }

    isPangram(): boolean{
        for (let i=97;i<=122;i++){
            if( !(this.s.indexOf( String.fromCharCode(i)) > -1) ){
                return false;
            }
        }
        return true;
    }

}

export default pangram;