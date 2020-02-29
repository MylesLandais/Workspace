package main

import (
	"fmt"
	"flag"
	"strings"
	"strconv"
	"sync"
	"net"
)

type Target struct{
	hostname string
	port int
}

func scan(t Target, wg *sync.WaitGroup){
	defer wg.Done()
	a := fmt.Sprintf("%s:%d",t.hostname,t.port)
	conn, err := net.Dial("tcp",a)
	if err != nil {
		fmt.Printf("[-] %d closed \n",t.port)
	}else{
		fmt.Printf("[+] %d open \n",t.port)
		conn.Close()
	}
}

func main() {
		hostPtr := flag.String("h","scanme.nmap.org","hostname or ip adress to scan")
		portsPtr :=  flag.String("p", "22,25,80", "list or range of ports to scan")

		flag.Parse()

		//fmt.Println("[+] ports:",*portsPtr)

		var wg sync.WaitGroup

		if strings.Contains(*portsPtr,"-") {
			//fmt.Println("[+] Processing as range")
			portsRange := strings.Split(*portsPtr,"-")
			begin, _ := strconv.Atoi( portsRange[0] )
			//fmt.Println(begin)
			end, _ := strconv.Atoi( portsRange[1])
			for i := begin; i <= end; i++ {
				wg.Add(1)
				//fmt.Println(i)
				t := Target{*hostPtr, i}
				scan(t,&wg)
			}
		} else{
			//fmt.Println("[+] Checking individual ports")
			portsRange := strings.Split(*portsPtr,",")
			for i:= 0; i < len(portsRange); i++{
				//fmt.Println(portsRange[i])
				p,_ := strconv.Atoi( portsRange[i]) 
				t := Target{*hostPtr,p}
				wg.Add(1)
				scan(t,&wg)
			}
		}
		wg.Wait()
}
