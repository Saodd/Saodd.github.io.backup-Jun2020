---
layout: post
title:  "Go源码：context标准库"
date:   2019-11-26
tags: Golang
color: rgb(255,0,0)
---

> 在读`net/http`包之前，先来看一下`context`这个包。它主要是针对请求来进行资源管理，提供了跨Go程的资源组织功能。希望通过学习这个包，深入了解一下chan的使用。

## context包 简介

看一下[官方定义](https://golang.org/pkg/context/)

> Package context defines the Context type, which carries deadlines, cancellation signals, and other request-scoped values across API boundaries and between processes.  
> Incoming requests to a server should create a Context, and outgoing calls to servers should accept a Context. The chain of function calls between them must propagate the Context, optionally replacing it with a derived Context created using WithCancel, WithDeadline, WithTimeout, or WithValue. When a Context is canceled, all Contexts derived from it are also canceled.

包上下文定义了上下文类型，它跨API边界和进程之间传递截止日期、取消信号和其他请求范围的值。

对服务器的传入请求应该创建上下文，而对服务器的传出调用应该接受上下文。它们之间的函数调用链必须传播上下文，可以选择将其替换为使用WithCancel、WithDeadline、WithTimeout或WithValue创建的派生上下文。当一个上下文被取消时，它派生的所有上下文也被取消。

## Demo 示例

拷贝自[MojoTech的博客](https://mojotv.cn/2018/12/26/what-is-context-in-go):

```go
func someHandler() {
    // 创建继承Background的子节点Context
    ctx, cancel := context.WithCancel(context.Background())
    go doSth(ctx)

    //模拟程序运行 - Sleep 5秒
    time.Sleep(5 * time.Second)
    cancel()
}

//每1秒work一下，同时会判断ctx是否被取消，如果是就退出
func doSth(ctx context.Context) {
    var i = 1
    for {
        time.Sleep(1 * time.Second)
        select {
        case <-ctx.Done():
            fmt.Println("done")
            return
        default:
            fmt.Printf("work %d seconds: \n", i)
        }
        i++
    }
}

func main() {
    fmt.Println("start...")
    someHandler()
    fmt.Println("end.")
}
```

核心语句是`select {case <-ctx.Done() }`，只要调用了`Cancel()`（或者被其他条件比如Deadline触发Cancel），这个chan就是可读的，下面就写一些撤销资源的语句吧。

有个语法细节强调一下，`select`语句中，既可以识别普通的chan数据（比如`someChan <- 1`），也会识别`close()`信号；前者传递来的数据只能被抽取一次，而后者会通知所有的等待读取者。

在实际运用中，我们以`context.Background()`作为根节点，然后调用`WithCancel()`之类的方法，派生出子节点。父节点可以主动调用Cancel，所有的子孙节点都随之取消。

## 核心：Context接口

看名字也知道它是这个包里最核心的内容了，它是一个接口，定义了几个方法：

```go
type Context interface {
	// 如果返回 ok==false 则表示没有设置Deadline时间
	Deadline() (deadline time.Time, ok bool)

	Done() <-chan struct{}

    // 如果ctx没有被取消，返回nil；如果是，则返回相应的原因（错误类型）
	Err() error

	// 用于储存一些键值对。要注意使用类型断言。
	Value(key interface{}) interface{}
}
```

有个语法细节强调一下，`<-chan struct{}`是一个只读的chan，数据类型是`struct{}`是一个空结构体。在Go的世界中，如果仅仅只需要传递信号而不需要附带额外的数据，使用空结构体是最佳的。
更多有关空结构体的介绍，可以参考[一只IT小小鸟的博客](https://blog.csdn.net/qq_34777600/article/details/87195673)

### 常量：Background 和 TODO

这两个值我们往往用作根节点，他们被定义为常量：

```go
var (
	background = new(emptyCtx)
	todo       = new(emptyCtx)
)
```

他们的类型是`emptyCtx`，这个类是符合`Context`接口的，只不过所有的方法都是空白的，啥也不做。

## 1. 方法一：WithCancel

```go
func WithCancel(parent Context) (ctx Context, cancel CancelFunc) {
	c := newCancelCtx(parent)
	propagateCancel(parent, &c)
	return &c, func() { c.cancel(true, Canceled) }
}
```

```go
func newCancelCtx(parent Context) cancelCtx {
	return cancelCtx{Context: parent}
}
```

这个方法会将parent复制一份，返回一个新的`cancelCtx`对象（继承自parent）和它对应的`cancel`方法。如果调用这个cancel方法，就会将Done返回的chan关闭掉（会影响子孙，不影响父对象）。

### 1.1 子类：cancelCtx

```go
type cancelCtx struct {
	Context

	mu       sync.Mutex            // protects following fields
	done     chan struct{}         // created lazily, closed by first cancel call
	children map[canceler]struct{} // set to nil by the first cancel call
	err      error                 // set to non-nil by the first cancel call
}
```

这个类非常简单，啥也没有。唯一有点意外的是带了一把锁，不过仔细想想也是应该的。

### 1.2 绑定父对象

这里用的是注册的机制，即，每次生成一个子对象时，去找到父对象中的一个注册表，将子对象加进去。这样，父对象cancel的时候就可以顺利地传播到所有子孙。

```go
func propagateCancel(parent Context, child canceler) {
	if parent.Done() == nil {
		return // parent is never canceled
	}
	if p, ok := parentCancelCtx(parent); ok {
		p.mu.Lock()
		if p.err != nil {
			// parent has already been canceled
			child.cancel(false, p.err)
		} else {
			if p.children == nil {
				p.children = make(map[canceler]struct{})
			}
			p.children[child] = struct{}{}
		}
		p.mu.Unlock()
	} else {
		go func() {
			select {
			case <-parent.Done():
				child.cancel(false, parent.Err())
			case <-child.Done():
			}
		}()
	}
}
```

上面`parentCancelCtx`这个方法，是检查父对象是否能够被cancel。如果能被取消，那就简单地注册一下；如果不能取消，例如`Background`，那么这个子对象就自立门户，直接监听父对象的Done。

### 1.3 取消

好的，现在已经能够形成一个cancel链条了，只要上游cancel了，下游都会跟着生效。那么调用cancel时发生了什么？

上面那个函数还有个邪门的地方，看它的签名参数`child canceler`，子对象本身并不是声明为`cancelCtx`类，而是声明为`canceler`这个接口。

```go
type canceler interface {
	cancel(removeFromParent bool, err error)
	Done() <-chan struct{}
}
```

那我们回去找一下`cancelCtx`类的`cancel`方法：

```go
func (c *cancelCtx) cancel(removeFromParent bool, err error) {
	if err == nil {
		panic("context: internal error: missing cancel error")
	}
	c.mu.Lock()
	if c.err != nil {
		c.mu.Unlock()
		return // already canceled
	}
	c.err = err
	if c.done == nil {
		c.done = closedchan
	} else {
		close(c.done)
	}
	for child := range c.children {
		// NOTE: acquiring the child's lock while holding parent's lock.
		child.cancel(false, err)
	}
	c.children = nil
	c.mu.Unlock()

	if removeFromParent {
		removeChild(c.Context, c)
	}
}
```

从上面可以看出，调用cancel时，做了四件事：第一，设置自己的err；第二，关闭自己的done；第三，调用所有子孙的cancel；第四，从父对象的注册表中除掉自己的名字。

那么到此为止，`context`包的主要的逻辑其实已经梳理清楚了。还有一些方法都是些锦上添花的功能。我们接下来看一下。

## 2. 方法二：WithTimeout

## 3. 方法三：WithDeadline

## 4. 方法四：WithValue

（未完待续）
