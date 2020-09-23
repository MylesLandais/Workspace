import {match} from "assert";

const usedNames= new Set()

export class RobotName{

    public name: string;

    constructor(){
        this.name = this.newName()
    }

    newName(): string{
        let s = Math.random().toString(36).replace(/[^a-z]+/g, '').substr(0, 2).toUpperCase()
        + Math.floor((Math.random() * 899) + 100).toString();
        while (true){
            if (!(s in usedNames )){
                usedNames.add(s)
                return(s)
            }
        }
    }

    resetName(): void{
        this.name = this.newName();
    }
}

