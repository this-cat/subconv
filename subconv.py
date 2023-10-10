from typing import Tuple
from urllib.parse import urlparse, urlencode, parse_qs

import requests
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
        self.domain = "192.168.0.2:25500"
        self.api = f"{self.domain}/sub"

        self.params = params
        self.headers = headers
        self.headers["host"] = self.domain
        self.url = f"http://{self.api}?{self.params}"
        self.parsed_url = urlparse(self.url)                    # 解析 URL
        self.query_params = parse_qs(self.parsed_url.query)     # 解析参数

        self.code: int or None = None

    def url_param_replace(self, url_param: str) -> str:
        query_params = self.query_params.copy()
        query_params["url"] = [url_param]
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

        # 找到差异位置
        index = 0
        for primary_name, secondary_name in zip(primary_names[::-1], secondary_names[::-1]):
            if primary_name != secondary_name:
                break
            else:
                index -= 1

        new_list = primary_names.copy()
        diff = self.group_names_insert_str(diff, "bak")

        # 合并
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

    def get(self) -> Tuple[str, dict]:
        url_param_value = self.query_params.get("url", [""])[0]

        # 检查URL参数是否为空
        if url_param_value == "":
            raise HTTPException(
                status_code=400,
                detail="URL parameter is null"
            )

        # 拆分URL参数并检查其长度是否符合要求
        url_params = url_param_value.split("|")
        if len(url_params) < 2:
            raise HTTPException(
                status_code=400,
                detail="URL parameter Less than 2"
            )

        # 分别处理主要和次要参数
        primary_url_params = url_params[0]
        secondary_url_params = url_params[1]
        primary_url = self.url_param_replace(primary_url_params)
        secondary_url = self.url_param_replace(secondary_url_params)

        # 发送主要和次要请求
        primary_req = requests.get(primary_url, headers=self.headers)
        secondary_req = requests.get(secondary_url, headers=self.headers)

        # 检查主要请求的状态码
        if primary_req.status_code != 200:
            raise HTTPException(
                status_code=primary_req.status_code,
                detail=f"Primary status code error: {primary_req.status_code}"
            )

        # 检查次要请求的状态码
        if secondary_req.status_code != 200:
            raise HTTPException(
                status_code=secondary_req.status_code,
                detail=f"Secondary status code error: {secondary_req.status_code}"
            )

        # 设置成功的响应信息
        self.code = 200

        # 将YAML字符串解析为Python对象
        primary = yaml.load(primary_req.text, Loader=yaml.FullLoader)
        secondary = yaml.load(secondary_req.text, Loader=yaml.FullLoader)
        self.proxies_insert_str(secondary, "bak")
        conf = self.join(primary, secondary)

        return str(conf), dict(primary_req.headers)


@app.get('/')
def web(request: Request):
    try:
        sub = Subscription(str(request.query_params), dict(request.headers))
        text, headers = sub.get()
        headers = lowercase_dict_keys(headers)
        headers["content-type"] = "text/yaml;charset=utf-8"
        headers["content-length"] = str(len(text))

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
