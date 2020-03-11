package main

import(
	"fmt"
	"encoding/json"
	"bytes"
	"net/http"
	"io/ioutil"
	"net/url"
)

type LoginToken struct{
	Token string `json:"token"`
}

var Token string;

func main(){
	// API - LOGIN
	type Payload struct {
		Apikey string `json:"apikey"`
	}

	data := Payload{
		Apikey: "96684acf0539d4cd97547f773828ec3b",
	}

	payloadBytes, err := json.Marshal(data)
	if err != nil {
		fmt.Print("JSON machine broke")
	}
	body := bytes.NewReader(payloadBytes)

	req, err := http.NewRequest("POST", "https://api.thetvdb.com/login", body)
	if err != nil {
		fmt.Println("HTTP machine broke")
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Println("http broke again")
	}
	fmt.Println(resp)
	defer resp.Body.Close()

	rspbody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println("\n \n resp:", (string(rspbody)))

	var t LoginToken
	err = json.Unmarshal( rspbody, &t)
	if err != nil {
		fmt.Print("JSON machine broke")
	}

	fmt.Printf("bearer: %v\n", t.Token)
	Token = t.Token
	// NEEDS TO RETURN/SET LOGIN TOKEN

	// API - Search Series
	SearchSeries("Mr Robot")

}

func SearchSeries(name string){
	auth_header := fmt.Sprintf("\n \n Bearer %s", Token)
	base_url := "https://api.thetvdb.com/"
	func_url := "search/series?name="
	url := fmt.Sprintf("%s%s%s",base_url,func_url,url.PathEscape(name))
	fmt.Println("Prepared URL ", url)

	req, err := http.NewRequest("GET", "url", nil)
	if err != nil {
		fmt.Println("HTTP machine broke")
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Authorization", auth_header)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Println("http broke again")
	}
	fmt.Println(resp)
	defer resp.Body.Close()

	rspbody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println("\n \n resp:", (string(rspbody)))
}
