# Subconv(subscription conversion)

## 介绍
Subconv 是一个订阅转换项目，涉及到两个订阅。第一个订阅将被指定为主节点组，而第二个订阅将用作备用节点组(将第一个订阅配置的 Bak_* 和 Backup 替换掉)。

## 先决条件
要使用 Subconv，请使用 [template.ini](https://raw.githubusercontent.com/this-cat/clash-template/main/template.ini) 模板以确保正常功能。

## (可选)subconverter 部署
1. 根据 [subconverter]() 链接的教程进行部署
2. 比如 [subconv.py](https://github.com/this-cat/subconv/blob/master/subconv.py) 修改为 0.0.0.0:25500 ↓ 
```patch
--- subconv.py	2023-10-06 15:23:13.480000000 +0800
+++ subconv-b.py	2023-10-07 20:51:12.818742833 +0800
@@ -12,7 +12,7 @@
 
 class Subscription:
     def __init__(self, params: str, headers: dict):
-        self.domain = "api.dler.io"
+        self.domain = "0.0.0.0:25500"
         self.api = f"{self.domain}/sub"
 
         self.params = params
```

## docker 部署
1. 构建 Docker Image
```commandline
docker build -t subconv-image .
```
2. 启动 Docker Container
```commandline
docker run -it -d --restart=always --name subconv -p 8088:8088 subconv-image:latest
```

## 贡献
如果您发现任何问题或想要贡献代码，请访问 [GitHub 仓库](https://github.com/this-cat/subconv)。

随时根据项目的发展和要求进一步补充 README.md 文件。