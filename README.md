# Subconv([subconverter](https://github.com/tindy2013/subconverter#external-configuration-file))

## 介绍
Subconv 是一个用于订阅合并的工具。
它的主要功能是将两个订阅文件合并在一起，其中第一个订阅被视为主要节点组，而第二个订阅将作为备用节点组。
在合并过程中，第一个订阅中的特定配置项（例如 Bak_* 和 Backup ）将被第二个订阅相应配置所替代。
如果只存在一个订阅，它将同时充当主要节点组和备用节点组，使用相同的订阅数据。
这个工具的目的是简化多个订阅的管理，以确保在主要节点组不可用时，能够无缝切换到备用节点组，从而提高可用性和稳定性。

## 先决条件
要使用 Subconv，请使用 [template.ini](https://raw.githubusercontent.com/this-cat/clash-template/main/template.ini) 模板以确保正常功能。

## (可选)subconverter 部署
1. 根据 [subconverter](https://github.com/tindy2013/subconverter#external-configuration-file) 链接的教程进行部署
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
3. (可选)进入容器
````
docker exec -it subconv bash
````

## 贡献
如果您发现任何问题或想要贡献代码，请访问 [GitHub 仓库](https://github.com/this-cat/subconv)。

随时根据项目的发展和要求进一步补充 README.md 文件。