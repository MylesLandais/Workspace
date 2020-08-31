package main

import(
    "fmt"
    "log"
    "os"

    "golang.org/x/crypto/ssh"
)

func main(){

    sshConfig := &ssh.ClientConfig{
        User: "Root",

    }
   	sshConfig.HostKeyCallback = ssh.InsecureIgnoreHostKey()

    if err != nil{
        panic(err)
    }


}