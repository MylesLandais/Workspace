package main

import (
	"fmt"
	"io"
	"os"
)

// PacketReader io.read
type PacketReader struct{}

func (packetReader *PacketReader) Read(b []byte) (int, error) {
	fmt.Println("in > ")
	return os.Stdin.Read(b)
}

// PacketWriter io.write
type PacketWriter struct{}

func (packetWriter *PacketWriter) Write(b []byte) (int, error) {
	fmt.Println("out >")
	return os.Stdout.Write(b)
}

func main() {
	var (
		r PacketReader
		w PacketWriter
	)

	if _, err := io.Copy(&w, &r); err != nil {
		fmt.Println("Unable to read/write data")
	}
}
