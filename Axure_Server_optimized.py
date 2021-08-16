# - * - coding:utf-8 - * -
from multiprocessing import freeze_support
import PySimpleGUI as Sg
import http.server
import socketserver
import socket
import os
import platform
import multiprocessing
from random import randint


USED_PORT = list()
SERVERS = dict()
ADDRESS_MESSAGE = str()


def cached(content, path) -> str:
    """
    :param content: List[list,],将当前运行的原型服务器信息格式化后进行存储
    :param path: 默认是当前路径，必须以axure.cache结尾
    :return:
    """
    result = "ready"
    try:
        with open(path, "w") as cache:
            cache.write(str(content))
        return result
    except Exception as e:
        result = f"error:{e}"
        return result


def get_computers_ip() -> str:
    """
    :return: 返回运行本程序的电脑的局域网ip，如无法获取则返回 localhost
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    address = "localhost"
    try:
        s.connect(('8.8.8.8', 80))
        address = s.getsockname()[0]
        s.close()
    except OSError as e:
        # 未联网时触发此错误
        print(e)
    finally:
        return address


def axure_server(directory: str, server_port: int = 8080) -> None:
    """
    启动一个静态文件服务器，等效于运行命令：python -m http.server: port
    :param directory: 服务的文件地址；
    :param server_port: 服务的端口；
    :return:
    """
    _dir = os.path.dirname(__file__) + '/prototypes' if not directory else directory
    os.chdir(_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", server_port), Handler)
    localIp = get_computers_ip()
    print(f"serving at: {localIp}:{server_port}\nprototypes directory: {_dir}")
    print("如你的原型由axure生成，请在地址后加上'/start.html'以保证浏览体验")
    global ADDRESS_MESSAGE
    ADDRESS_MESSAGE = f"serving at: {localIp}:{server_port}\nprototypes directory: {_dir}"
    httpd.serve_forever()


def is_there_a_default_prototype_folder() -> dict:
    if not os.path.exists(os.path.dirname(__file__) + '/prototypes'):
        system_name = platform.system()
        default_dir = os.path.dirname(__file__) + '/prototypes'
        try:
            if system_name.upper() != "WINDOWS":
                os.system(f"cd {os.path.dirname(__file__)}")
                os.system(f"mkdir prototypes")
            else:
                os.system(f"cd {os.path.dirname(__file__)}")
                os.system(f"md prototypes")
            return dict(exist=True, dir=default_dir)
        except Exception as e:
            return dict(exist=False, dir=e)


def spawn_new_server(target, args: tuple, name: str) -> None:
    server = multiprocessing.Process(target=target, args=args, name=name)
    server.daemon = True
    server.start()
    global SERVERS, USED_PORT
    SERVERS["{}".format(args[1])] = server
    USED_PORT.append(args[1])


def server_ui() -> None:
    """
    UI界面
    :return:
    """

    Sg.theme('Light Blue 1')

    layout_main = [
        [Sg.Text('设置原型路径:', font=("", 16)),
         Sg.Text('', size=(35, 1), auto_size_text=True, font=("", 12)),
         Sg.FolderBrowse(button_text="选择路径", pad=((10, 0), (0, 0)), font=("", 12), key="dir")],

        [Sg.Text('预设服务端口号:', font=("", 16)), Sg.InputText("8080", size=(43, 1), font=("", 12), key="port")],

        [Sg.Button('启动原型服务', pad=((140, 0), (10, 0)), font=("", 12), key="run"),
         Sg.Button('关闭全部服务', pad=((20, 0), (10, 0)), font=("", 12), key="close")],

        [Sg.Text(pad=((2, 0), (10, 0)))],

        [Sg.Table(key="alive_servers",
                  values=[],
                  headings=["服务", "网址", "原型路径", "端口"],
                  col_widths=[12, 20, 25, 12],
                  font=("", 12),
                  num_rows=24,
                  auto_size_columns=False,
                  enable_events=True,
                  ),
         ],

        [Sg.Text('', size=(49, 1), auto_size_text=True, font=("", 12)),
         Sg.FolderBrowse(button_text="选择路径", pad=((0, 0), (0, 0)), font=("", 12), key="bak_dir"),
         Sg.Button(key="backup", button_text="备份", font=("", 12)),
         Sg.Button(key="recover", button_text="恢复", font=("", 12))
         ]
    ]

    window_main = Sg.Window('产品原型服务器', layout_main, size=(720, 800))
    table_row = []
    while True:
        event, values = window_main.read()
        if event == 'close':  # if user closes window or clicks cancel
            break

        if event == "WIN_CLOSED":
            break

        if event == "run":

            try:
                dir_ = values["dir"] if os.path.exists(values["dir"]) else os.path.dirname(__file__) + '/prototypes'
                print(dir_)
                _port = int(values["port"])
                port = _port if _port and _port not in USED_PORT else randint(1025, 65534)
                spawn_new_server(target=axure_server, args=(dir_, port), name=f"{values['port']}")
                window_main["run"].Update("再启动一个")
                addr_ = get_computers_ip()
                table_row += [[port, f"{addr_}:{port}", dir_, port]]
                window_main["alive_servers"].Update(table_row)
                Sg.Popup(f'''{ADDRESS_MESSAGE}\n"如你的原型由axure生成，请在地址后加上'/start.html'以保证浏览体验"''',
                         title="❤❤❤❤❤",
                         keep_on_top=True,
                         auto_close=False,
                         font=("", 12))

            except Exception as e:
                Sg.PopupAutoClose(f"错误：{e} "
                                  f"\n1. 请检查输入端口是否为整数"
                                  f"\n2. 请检查输入路径是否合法",
                                  title="⚠️",
                                  keep_on_top=True,
                                  auto_close=False,
                                  font=("", 12))

        if event == "alive_servers":
            return_events = Sg.Popup("点击'OK'按钮将关闭此该项原型服务，原链接将失效。"
                                     "如需重新启用，需手动重启服务。"
                                     "关闭此窗口将不进行任何操作",
                                     title="⚠️是否要关闭此服务？⚠️",
                                     keep_on_top=True,
                                     font=("", 12))
            print(return_events)
            if return_events == "OK":
                severer_2b_stop = table_row[values["alive_servers"][0]][0]
                #  注意，terminate()方法在杀死进程时，并不能保证释放资源，所以有可能出现关闭服务后，端口仍被占用的情况
                SERVERS[f'''{severer_2b_stop}'''].terminate()
                table_row.pop(values["alive_servers"][0])
                window_main["alive_servers"].Update(table_row)
                print(f"已关闭服务: {severer_2b_stop}")
            else:
                pass

            pass

        if event == "backup":
            return_events = Sg.Popup("点击'OK'将覆盖旧备份文件。"
                                     "关闭此窗口将不进行任何操作",
                                     title="进行备份️",
                                     font=("", 12))
            print(return_events)
            print(event, values)
            if return_events == "OK":
                cache_path = os.path.dirname(__file__) + '/axure.cache' if not values["bak_dir"] + '/axure.cache' \
                                                                        else values["bak_dir"] + '/axure.cache'
                content = table_row
                result = cached(content=content, path=cache_path)
                print(result)
                Sg.Popup(f"备份成功，路径：{cache_path}", title="备份成功", font=("", 12))
            else:
                pass

        if event == "recover":
            cache = os.path.dirname(__file__) + '/axure.cache' if not values["bak_dir"] + '/axure.cache' \
                                                               else values["bak_dir"] + '/axure.cache'
            is_cache_there = os.path.exists(cache)
            if is_cache_there:
                try:
                    table_row_2_update = []
                    with open(cache, "r") as file:

                        for s in eval(file.read()):
                            directory = s[2]
                            port = s[0]
                            spawn_new_server(target=axure_server, args=(directory, port), name=f"{values['port']}")
                            table_row_2_update += [s]
                    window_main["alive_servers"].Update(table_row_2_update)
                    table_row = table_row_2_update
                    Sg.Popup(f"备份恢复成功\n"
                             f"注意：由于无法确定恢复前端口的占用情况，"
                             f"请手动检查各个地址是否仍然有效。如果失效请手动添加，更换端口即可",
                             title="备份恢复成功",
                             font=("", 12))

                except Exception as e:
                    Sg.Popup(f"备份恢复失败💣💣💣"
                             f"错误：{e}", title="💣备份恢复失败💣", font=("", 12))

        else:
            pass

    window_main.close()


if __name__ in "__main__":
    freeze_support()
    is_there_a_default_prototype_folder()
    server_ui()
