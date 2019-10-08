package main

import (
	"fmt"
	"testing"
)

func Test_readDir(t *testing.T) {
	posts := readDir()
	for _, p := range posts {
		fmt.Println(p.Brev)
	}
}
