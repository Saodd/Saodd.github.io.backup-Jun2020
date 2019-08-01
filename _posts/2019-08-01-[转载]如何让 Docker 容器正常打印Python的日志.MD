---
layout: post
title:  "如何让Docker容器正常打印Python的日志"
date:   2019-08-01
tags: Docker 
color: rgb(102,204,255)
---

> 在本地通过Swarm进行完整的容器部署调试。
> 但是非常诡异的事情出现了，Django中的print就是打印不出来，可急死我了。
> 最后终于看到这篇文章，找到了问题所在。终于可以正常地开发了。

原文地址：[原文](https://farer.org/2017/10/09/python-log-in-docker-container/)，
[转载](https://www.jianshu.com/p/61ea6bd09daa)。

## 原文

> 在 Docker 容器里跑 Python 程序时，我们经常遇到通过print函数或者logging模块输出的信息在容器 log 中迷之失踪，过了好久又迷之出现。这是因为 Python 在写 stdout 和 stderr 的时候有缓冲区，导致输出无法实时更新进容器 log。

1. 增加环境变量

    对于使用print函数打印的内容，在运行容器时增加环境变量PYTHONUNBUFFERED=0就可以解决。

2. 配置 logging 的 stream 参数

    ```python
    import logging
    logging.basicConfig(stream=sys.stdout)
    ```

    这样，通过 logging 模块打印的日志都会直接写到标准输出 stdout。

    或者自定义两个StreamHandler分别配置为输出到 stdout 和 stderr，来对不同 log 分别进行输出处理。

3. WSGI server 配置参数

    如果是以 WSGI server 运行的 web 应用，以 gunicorn 为例，在 gunicorn 的启动命令中增加参数--access-logfile - --error-logfile -即可。

## 小结

亲测有效。Docker真的坑啊……话说回来，觉得我接触的好几个Google体系的东西，都感觉特别坑。
不是有多难，而是出了问题都找不到原因在哪的。真的很烦。