package main

import (
	"bufio"
	"bytes"
	"context"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"
	"io/ioutil"
	"log"
	"os"
	"path"
	"strings"
	"time"
)

const PostPath = "../_posts"

type postMeta struct {
	FileName string
	Title    string
	Date     time.Time
	Tags     []string
	Brev     string
}

func dialMongo() (client *mongo.Client) {
	var err error
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	client, _ = mongo.Connect(ctx, options.Client().ApplyURI("mongodb://blog_mongo:27017"))

	// ping MongoServer
	err = client.Ping(ctx, readpref.Primary())
	if err != nil {
		log.Fatalf("[ERROR] Connecting Mongo server: %s\n", err)
	}
	return client
}

func readDir() []*postMeta {
	var posts = []*postMeta{}
	files, err := ioutil.ReadDir(PostPath)
	if err != nil {
		log.Fatalf("[ERROR] Reading post-dir: ", err)
	}

	for _, file := range files[:2] {
		posts = append(posts, readFile(file.Name()))
	}
	return posts
}

func readFile(name string) *postMeta {
	f, _ := os.Open(path.Join(PostPath, name))
	defer f.Close()

	b := bufio.NewReader(f)
	post := &postMeta{FileName: name}

	for i := 0; i < 20; i++ {
		line, _, err := b.ReadLine()
		if err != nil {
			break
		}
		if len(line) < 3 {
			continue
		}
		switch line[0] {
		case '#':
			i = 20 // break {for}
		case '-':
			continue
		case 't':
			if line[1] == 'i' { // title
				s := bytes.Split(line, []byte{' '})
				title := string(s[len(s)-1])
				post.Title = strings.Trim(title, "\"")
			} else if line[1] == 'a' { // title
				tags := strings.Split(string(line), " ")
				post.Tags = tags[1:]
			}
		case 'd':
			if line[1] == 'a' { // date
				s := bytes.Split(line, []byte{' '})
				dateStr := string(s[len(s)-1])
				post.Date, err = time.Parse("2006-01-02", dateStr)
				if err != nil {
					log.Printf("[ERROR] Parsing date<%s>: %s\n", dateStr, err)
				}
			}
		case '>':
			post.Brev += string(line)
		}
	}
	return post
}

func updateMongo(client *mongo.Client, posts []*postMeta) {
	collect := client.Database("Blog").Collection("Post")
	// 1. 先整个删掉旧的
	err := collect.Drop(context.TODO())
	if err != nil {
		log.Println("[ERROR] Dropping collection: ", err)
	} else {
		log.Println("[INFO] Dropped collection.")
	}
	// 2. 然后把所有文件都注册进去
	for _, p := range posts {
		_, err := collect.InsertOne(context.TODO(), p)
		if err != nil {
			log.Printf("[ERROR] Inserting <%s>: %s\n", p.FileName, err)
		} else {
			log.Printf("[INFO] Inserted <%s>.\n", p.FileName)
		}
	}
}

func main() {
	// Step1: Connect Mongo
	client := dialMongo()
	// Step2: Read post files
	posts := readDir()
	// Setp3: Update DB
	updateMongo(client, posts)
}
