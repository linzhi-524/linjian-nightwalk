import nightwalk


def play(command: str) -> None:
    print(f"\n> {command}")
    print(nightwalk.cmd(command))


if __name__ == "__main__":
    play("options")       # 第一次调用自动播放序章
    play("open 门")
    play("travel 雾林")
    play("inspect 无脸旅人")
    play("options")
