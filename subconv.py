from typing import Tuple
from urllib.parse import urlparse, urlencode, parse_qs, ParseResult

from requests import Response, Session
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn
import yaml

app = FastAPI()


# 在字符串中查找指定目标字符串，然后替换为新的字符串
def replace_str(original: str, replacement: str, target: str) -> str:
    """
    original (str): 原始字符串
    replacement (str): 要替换为的新字符串
    target (str): 要查找并替换的目标字符串
    """

    index = original.find(target)      # 查找目标字符串的索引

    if index != -1:
        # 使用切片操作，在目标字符串的位置进行替换
        result_str = original[:index] + replacement + original[index + len(target):]
    else:
        result_str = original

    return result_str


# 将 dict 的 key 字符串转换为小写
def lowercase_dict_keys(data: dict):
    return {k.lower(): v for k, v in data.items()}


class Subscription:
    def __init__(self, params: str, headers: dict):
        self.domain: str = "www.mywrt.org:25500"
        self.api: str = f"{self.domain}/sub"

        self.params = params
        self.headers = headers
        self.headers["host"]: str = self.domain
        self.url: str = f"http://{self.api}?{self.params}"
        self.parsed_url: ParseResult = urlparse(self.url)                                       # 解析 URL
        self.query_params: dict = parse_qs(self.parsed_url.query, keep_blank_values=True)       # 解析参数

        self.session: Session = Session()
        self.code: int = 200

    @staticmethod
    def code_ok(code: int) -> bool:
        return 200 <= code <= 299

    def url_param_replace(self, url_param: str) -> str:
        query_params = self.query_params.copy()
        query_params["url"] = [url_param]

        # 默认 udp 参数
        if query_params.get("udp", ['']) == ['']:
            query_params["udp"] = ["false"]

        encoded_params = urlencode(query_params, doseq=True)

        return f"http://{self.api}?{encoded_params}"

    @staticmethod
    def secondary_names(secondary: dict, key: str) -> list:
        secondary_groups = secondary["proxy-groups"]

        for group in secondary_groups:
            name = group["name"]

            # 找到就返回组
            if name == key:
                return group["proxies"]

        # 返回一个空的组
        return []

    def get_emoji_param(self):
        emoji_param = self.query_params.get("emoji", [])

        if not emoji_param:
            return False
        else:
            return True if emoji_param[0].lower() == "true" else False  # 转换为 bool 类型

    # 向 proxies 组插入字符串
    def proxies_insert_str(self, secondary: dict, text: str):
        proxies = secondary.get("proxies")

        for proxie in proxies:
            name = proxie.get("name", "")

            if self.get_emoji_param():
                proxie["name"] = replace_str(name, f" {text} ", " ")
            else:
                proxie["name"] = f"{text} {name}"

    # 向 names 组插入字符串
    def group_names_insert_str(self, names: list, text: str) -> list:
        new_names = []

        for name in names:
            if self.get_emoji_param():
                new_names.append(replace_str(name, f" {text} ", " "))
            else:
                new_names.append(f"{text} {name}")

        return new_names

    def merge(self, primary_names: list, secondary_names: list) -> list:
        diff = [item for item in secondary_names if item not in primary_names]      # 获取差异值

        # 找到差异值的插入位置
        index = 0
        for primary_name, secondary_name in zip(primary_names[::-1], secondary_names[::-1]):
            if primary_name != secondary_name:
                break
            else:
                index -= 1

        new_list = primary_names.copy()
        diff = self.group_names_insert_str(diff, "bak")     # 在差异值中插入字符串 "bak"

        # 合并差异值到新列表
        if index == 0:
            new_list += diff
        else:
            new_list[index:index] = diff

        return new_list

    def join(self, primary: dict, secondary: dict) -> str:
        secondary_proxies = secondary.get("proxies")
        if not secondary_proxies:
            raise HTTPException(
                status_code=400,
                detail="Secondary proxies is null"
            )

        # 加入 proxies
        primary["proxies"] += secondary_proxies

        # 加入 proxy-groups
        groups = primary["proxy-groups"]
        for group in groups:
            name = group.get("name", "")
            type_ = group.get("type", "")
            proxies = group.get("proxies", [])

            # 匹配 Backup 和 Bak_*
            if name == "Backup" or "bak_" in name.lower():
                group["proxies"] = self.group_names_insert_str(
                    self.secondary_names(secondary, name),
                    "bak"
                )
            # 合并
            elif type_.lower() == "select":
                group["proxies"] = self.merge(
                    proxies,
                    self.secondary_names(secondary, name)
                )

        return yaml.dump(primary, default_flow_style=False)

    def req(self, url_param: str, detail: str) -> Response:
        url = self.url_param_replace(url_param)
        r = self.session.get(url, headers=self.headers)

        # 检查主要请求的状态码
        if not self.code_ok(r.status_code):
            raise HTTPException(status_code=r.status_code, detail=detail)

        return r

    def get(self) -> Tuple[str, dict]:
        url_param_value = self.query_params.get("url", [""])[0]
        url_params = url_param_value.split("|")

        # 如果 URL 参数为空，抛出 HTTP 异常
        if len(url_params) == 0:
            raise HTTPException(
                status_code=400,
                detail="URL parameter is null"
            )
        # 如果只有一个 URL 参数，发送请求并返回响应内容和响应头
        elif len(url_params) == 1:
            req = self.req(url_params[0], "Status code error")

            return req.text, dict(req.headers)
        # 如果有两个 URL 参数，获取主要和备用订阅的数据
        elif len(url_params) == 2:
            # 获取主要和备用订阅的数据
            primary = self.req(url_params[0], "Primary status code error")
            secondary = self.req(url_params[1], "Secondary status code error")

            # 解析 YAML 数据
            primary_yaml = yaml.load(primary.text, Loader=yaml.FullLoader)
            secondary_yaml = yaml.load(secondary.text, Loader=yaml.FullLoader)

            self.proxies_insert_str(secondary_yaml, "bak")  # 在备用数据中插入 "bak" 字段
            conf = self.join(primary_yaml, secondary_yaml)  # 合并主要和备用数据

            # 修改内容长度，使其等于合并后数据的长度
            primary.headers["content-length"] = str(len(conf))

            return str(conf), dict(primary.headers)
        # 如果 URL 参数数量不符合预期，抛出 HTTP 异常
        else:
            raise HTTPException(status_code=400, detail="Too many URL parameters")


@app.get('/')
def web(request: Request):
    try:
        sub = Subscription(str(request.query_params), dict(request.headers))
        text, headers = sub.get()
        headers = lowercase_dict_keys(headers)
        headers["content-type"] = "text/yaml;charset=utf-8"

        # 删除 content-encoding
        headers.pop("content-encoding", None)

        return PlainTextResponse(content=text, media_type="text/yaml", headers=headers)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


if __name__ == '__main__':
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8088,
        timeout_keep_alive=3600,
    )
