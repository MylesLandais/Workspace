class Bob {
    hey(s:string): string{
        let clean = s.replace(/\s/g, "");
        // question check
        if(clean.charAt( clean.length -1 ) == '?'){
            return 'Sure.'
        }
        // blank string
        else if(clean == ''){
            return 'Fine. Be that way!'
        }
        // caps lock check
        else if(s.toUpperCase() == s && s.match(/[A-Za-z]/g) != null){
            return 'Whoa, chill out!'
        }

        return "Whatever."
    }
}

export default Bob