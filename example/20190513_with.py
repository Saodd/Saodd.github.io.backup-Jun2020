def example1():
    class Dream:
        def __init__(self, name):
            print("我是%s。" % name)

        def __enter__(self):
            print("我要准备睡觉了。")
            return "别偷看！"

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("我要醒来了！")

    with Dream("Lewin") as f:
        print(f)


def example2():
    class Dream:
        def __init__(self, name):
            print("我是%s。" % name)

        def __enter__(self):
            print("我要准备睡觉了。")
            return "别偷看！"

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("我要醒来了！")

    with Dream("Lewin") as f:
        print(f)
        raise Exception("做噩梦了！！吓死我了！！")
        print("这里的不会被执行了。")


def example3():
    class Dream:
        def __init__(self, name):
            print("我是%s。" % name)

        def __enter__(self):
            print("我要准备睡觉了。")
            return "别偷看！"

        def __exit__(self, *args):
            print("我梦到了:", args)
            print("我要醒来了！")

    with Dream("Lewin") as f:
        print(f)
        raise Exception("做噩梦了！！吓死我了！！")
        print("这里的不会被执行了。")


def example4():
    class Dream:
        def __init__(self, name):
            print("我是%s。" % name)

        def __enter__(self):
            print("我要准备睡觉了。")
            return "别偷看！"

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("我梦到了:", exc_type, exc_val, exc_tb)
            print("我要醒来了！")
            return True

    with Dream("Lewin") as f:
        print(f)
        raise Exception("做噩梦了！！吓死我了！！")
        print("这里的不会被执行了。")


def example5():
    class Dream:
        def __init__(self, name):
            print("我是%s。" % name)

        def __enter__(self):
            print("我要准备睡觉了。")
            return "别偷看！"

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("我梦到了:", exc_type, exc_val, exc_tb)
            print("我要醒来了！")
            return False

    with Dream("Lewin") as f:
        print(f)
        raise Exception("做噩梦了！！吓死我了！！")
        print("这里的不会被执行了。")


def example6():
    class Dream:
        def __init__(self, name):
            print("我是%s。" % name)

        def __enter__(self):
            print("我要准备睡觉了。")
            return "别偷看！"

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("我梦到了:", exc_type, exc_val, exc_tb)
            print("我要醒来了！")
            if exc_type == TimeoutError:  # 或者都isinstance(exc_val, TimeoutError)都可以
                print("指定异常处理完毕！")
                return True

    with Dream("Lewin") as f:
        print(f)
        raise TimeoutError("做噩梦了！！吓死我了！！")


if __name__ == '__main__':
    example6()
