---
layout: post
title:  "WebSocket初体验——网页聊天室"
date:   2019-07-10
tags: Web应用
color: rgb(255,204,255)
---

> 受Yanni老板的启发，我的第一个Web应用打算做成一个网页聊天室。
> 之前用Go+TCPsocket实现过控制台版本，不过在控制台上体验很差。
> 今天来看一下Go+JS+Websocket是否能够实现预期的结果。

## 先看一下Golang的实现

主要逻辑很简单，采用典型的C/S结构，服务器监听端口，将所有的客户端连接都保存在`map`里，
当有任意客户端发送消息来了，服务端就遍历所有的活动连接，把消息广播出去。

### Go: ChatroomServer

```golang
var ConnMap map[string]*net.TCPConn

func Main_ChatroomServer() {
    var tcpAddr *net.TCPAddr
    ConnMap = make(map[string]*net.TCPConn)
    tcpAddr, _ = net.ResolveTCPAddr("tcp", "0.0.0.0:9999")

    tcpListener, _ := net.ListenTCP("tcp", tcpAddr)

    defer tcpListener.Close()

    for {
        tcpConn, err := tcpListener.AcceptTCP()
        if err != nil {
            continue
        }

        fmt.Println("A client connected : " + tcpConn.RemoteAddr().String())
        // 新连接加入map
        ConnMap[tcpConn.RemoteAddr().String()] = tcpConn
        go tcpPipe(tcpConn)
    }

}

func tcpPipe(conn *net.TCPConn) {
    ipStr := conn.RemoteAddr().String()
    defer func() {
        fmt.Println("disconnected :" + ipStr)
        conn.Close()
    }()
    reader := bufio.NewReader(conn)

    for {
        message, err := reader.ReadString('\n')
        if err != nil {
            return
        }
        fmt.Println(conn.RemoteAddr().String() + ":" + string(message))
        // 这里返回消息改为了广播
        boradcastMessage(conn.RemoteAddr().String() + ":" + string(message))
    }
}

func boradcastMessage(message string) {
    b := []byte(message)
    // 遍历所有客户端并发送消息
    for _, conn := range ConnMap {
        conn.Write(b)
    }
}
```

### Go: ChatroomClient

```golang
var quitSemaphore chan bool

func Main_ChatroomClient() {
    var tcpAddr *net.TCPAddr
    tcpAddr, _ = net.ResolveTCPAddr("tcp", "192.168.1.213:9999")

    conn, _ := net.DialTCP("tcp", nil, tcpAddr)
    defer conn.Close()
    fmt.Println("connected!")

    go onMessageRecived(conn)

    // 控制台聊天功能加入
    for {
        var msg string
        myScanln(&msg)
        if msg == "quit" {
            break
        }
        b := []byte(msg + "\n")
        conn.Write(b)
    }
    <-quitSemaphore
}

func onMessageRecived(conn *net.TCPConn) {
    reader := bufio.NewReader(conn)
    for {
        msg, err := reader.ReadString('\n')
        fmt.Println(msg)
        if err != nil {
            quitSemaphore <- true
            break
        }
    }
}

func myScanln(a *string) {
    reader := bufio.NewReader(os.Stdin)
    data, _, _ := reader.ReadLine()
    *a = string(data)
}
```
### 实现效果（客户端）

```shell
root@973b12641a87:/scripts/Learning/Golang/src# go run run2.go
connected!
yeah!
192.168.1.213:60894:yeah!

yahoo
192.168.1.213:60894:yahoo

^Csignal: interrupt
```

以上的Golang代码仅仅使用了`net`包，
我们可以很直观地感受到，连接非常简单轻量，并没有包含乱七八糟的头部数据（我指的是`http`那种头部）。
所以如果要实现一些高级特性，比如加密、浏览器支持之类的，还要自己另外想办法。

我们接下来看一下`WebSocket`：

## WebSocket简介

WebSocket 协议在2008年诞生，2011年成为国际标准。所有浏览器都已经支持了。

它的最大特点就是，服务器可以主动向客户端推送信息，客户端也可以主动向服务器发送信息，是真正的双向平等对话，属于服务器推送技术的一种。

### 为什么需要它

我们知道，正常的Web应用中，是客户端发起请求-服务器应答的模式。
那么对于一些复杂的应用，比如最简单的聊天室，要如何实现？能想到的就是用js脚本定时询问服务器。
但这种方法显然太低效了。

而原生的Socket，又太简单太底层了。

所以这种两种需求相加，自然就会催生出一种既有类似于Socket的效率，又像http那样兼容丰富的技术，那就是Websocket了。

![WebSocket结构图](/screenshot/2019-07-10-WebSocket-Structure.jpg)

### WebSocket 数据帧结构

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 +-+-+-+-+-------+-+-------------+-------------------------------+
 |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
 |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
 |N|V|V|V|       |S|             |   (if payload len==126/127)   |
 | |1|2|3|       |K|             |                               |
 +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
 |     Extended payload length continued, if payload len == 127  |
 + - - - - - - - - - - - - - - - +-------------------------------+
 |                               |Masking-key, if MASK set to 1  |
 +-------------------------------+-------------------------------+
 | Masking-key (continued)       |          Payload Data         |
 +-------------------------------- - - - - - - - - - - - - - - - +
 :                     Payload Data continued ...                :
 + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
 |                     Payload Data continued ...                |
 +---------------------------------------------------------------+
 ```

 我们自己写服务端和客户端测试一下：

```golang
func Main_WebSocketServer() {
    var tcpAddr *net.TCPAddr
    ConnMap = make(map[string]*net.TCPConn)
    tcpAddr, _ = net.ResolveTCPAddr("tcp", "0.0.0.0:9999")

    tcpListener, _ := net.ListenTCP("tcp", tcpAddr)

    defer tcpListener.Close()

    for {
        tcpConn, err := tcpListener.AcceptTCP()
        if err != nil {
            continue
        }
        fmt.Println("A client connected : " + tcpConn.RemoteAddr().String())
        // 把客户端请求全文打印出来
        reader := bufio.NewReader(tcpConn)
        for {
            message, err := reader.ReadString('\n')
            if err != nil {
                return
            }
            fmt.Println(string(message))
        }
    }
}
```

然后在浏览器中执行：

```js
var ws = new WebSocket("ws://192.168.1.213:9999");
```

可以看到服务端输出：

```text
A client connected : 192.168.1.213:63930

GET / HTTP/1.1

Host: 192.168.1.213:9999

Connection: Upgrade

Pragma: no-cache

Cache-Control: no-cache

Upgrade: websocket

Origin: chrome-search://local-ntp

Sec-WebSocket-Version: 13

User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36

Accept-Encoding: gzip, deflate

Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7

Sec-WebSocket-Key: /v/rffaLbTlI2yvDFqxIaQ==

Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits
```

另外，如果我们使用`wss`连接，我们会看到服务器输出一堆乱码，因为传输的内容被加密了：

```js
var ws = new WebSocket("wss://192.168.1.213:9999");
```

## 初步实现：Websocket的建立

那么我们开始进入主题。首先来试一下这个方案是否可行。

```golang
package learnWeb

import (
	"fmt"
	"golang.org/x/net/websocket"
	"net/http"
)

func Main_WebSocketServer() {
	http.Handle("/echo", websocket.Handler(wssHandler))
	http.HandleFunc("/", func(writer http.ResponseWriter, request *http.Request) {
		http.ServeFile(writer,request,"C:/Users/lewin/github/Learning/Golang/src/learnWeb/20190710-WebSocketClient.html")
	})
	http.ListenAndServe("0.0.0.0:9999",nil)
}

func wssHandler(conn *websocket.Conn)  {
	fmt.Println("connect +1 ")
	defer func() {
		fmt.Println("connect closed: ")
    }()
    
	rec := make([]byte, 4096)
	var n int
	var err error
	for {
		n, err = conn.Read(rec)
		if err != nil {
			break
		}
		if n > 0 {
			fmt.Println(string(rec[:n]))
			wssBroadcast(rec[:n])
		}
	}
}
```

在上面的代码中，我们依然使用`http`包去监听`http请求`，
但是使用了`websocket.Handler`来建立`WebSocket`连接。
它们会帮我们处理好线程的问题，我们这里就不多费心了。

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test WebSocket</title>
</head>
<body>

<input id="input" type="text"/>
<button onclick="send()">Send</button>
<pre id="output"></pre>


<script>
    var input = document.getElementById("input");
    var output = document.getElementById("output");
    var wss = new WebSocket("ws://192.168.1.213:9999/echo");

    wss.onopen = function (evt) {
        output.innerHTML += "Status: Connected\n";
    };

    wss.onmessage = function (evt) {
        output.innerHTML += "Server: " + evt.data + "\n";
    };

    wss.onclose = function (evt) {
        output.innerHTML += "Connection closed.\n";
    };

    function send() {
        wss.send(input.value);
        input.value = "";
    }
</script>
</body>
</html>
```

配合上面这个html页面，我们就可以确认前端与后端的Websocket是否连接正常。
接下来我们可以开始完善业务逻辑了。

## 完善聊天业务逻辑

### 保存用户信息(更新中)

那首先我们要设立一个用户列表，这样才能实现广播。用一个`map`就好了，用户名作为key，socket作value。

```golang
var wssConnmap map[string]*websocket.Conn
```














## 参考文献

> 参考1：[用Golang实现 文本广播式聊天服务器/客户端](https://victoriest.gitbooks.io/golang-tcp-server/content/chapter3.html)  
> 参考2：[WebSocket 教程 - 阮一峰的网络日志](http://www.ruanyifeng.com/blog/2017/05/websocket.html)
