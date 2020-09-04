class Transcriptor {
    toRna( s:string ): string {
        let r:string = "";
        for(let c of s){
            if( c === "C"){
                r += "G"
                continue
            }
            if( c === "G") {
                r += "C"
                continue
            }
            if( c === "A"){
                r += "U"
                continue
            }
            if( c==="T") {
                r += "A"
                continue
            }
            throw new Error("Invalid input DNA.")
        }
        return r;
    }
}

export default Transcriptor