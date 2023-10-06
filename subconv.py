from typing import Tuple

import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from urllib.parse import urlparse, urlencode, parse_qs
import uvicorn
import yaml

app = FastAPI()


class Subscription:
    def __init__(self, params: str, headers: dict):
        self.domain = "api.dler.io"
        self.api = f"{self.domain}/sub"

        self.params = params
        self.headers = headers
        self.headers["host"] = self.domain
        self.url = f"http://{self.api}?{self.params}"
        self.code: int or None = None

    def url_param_replace(self, url_param: str) -> str:
        parsed_url = urlparse(self.url)
        query_params = parse_qs(parsed_url.query)
        query_params["url"] = [url_param]
        encoded_params = urlencode(query_params, doseq=True)

        return f"http://{self.api}?{encoded_params}"

    @staticmethod
    def secondary_proxies(secondary: dict, key: str) -> list:
        secondary_groups = secondary["proxy-groups"]

        for group in secondary_groups:
            name = group["name"]

            # 找就返回组
            if name == key:
                return group["proxies"]

        # 返回一个空的组
        return []

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
            name = group["name"]

            if name == "Backup":
                group["proxies"] = self.secondary_proxies(secondary, "Backup")
            elif name == "Bak_HK":
                group["proxies"] = self.secondary_proxies(secondary, "Bak_HK")
            elif name == "Bak_TW":
                group["proxies"] = self.secondary_proxies(secondary, "Bak_TW")
            elif name == "Bak_SG":
                group["proxies"] = self.secondary_proxies(secondary, "Bak_SG")
            elif name == "Bak_JP":
                group["proxies"] = self.secondary_proxies(secondary, "Bak_JP")

        return yaml.dump(primary, default_flow_style=False)

    def get(self) -> Tuple[str, dict]:
        # 解析URL并提取查询参数
        parsed_url = urlparse(self.url)
        query_params = parse_qs(parsed_url.query)
        url_param_value = query_params.get("url", [""])[0]

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
        conf = self.join(primary, secondary)

        return str(conf), dict(primary_req.headers)


@app.get('/')
def index(request: Request):
    try:
        sub = Subscription(str(request.query_params), dict(request.headers))
        text, headers = sub.get()
        headers["content-type"] = "text/yaml;charset=utf-8"
        headers.pop("Content-Encoding")     # 删除 Content-Encoding

        return PlainTextResponse(content=text, media_type="text/yaml", headers=headers)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8088,
        timeout_keep_alive=3600,
    )
