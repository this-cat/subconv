# Subconv(subscription conversion)

## 介绍
Subconv 是一个订阅转换项目，涉及到两个订阅。第一个订阅将被指定为主节点组，而第二个订阅将用作备用节点组(将第一个订阅配置的 Bak_* 和 Backup 替换掉)。

## 先决条件
要使用 Subconv，请使用 [template.ini](https://raw.githubusercontent.com/this-cat/clash-template/main/template.ini) 模板以确保正常功能。


## docker 部署
1. 构建 Docker Image
```commandline
docker build -t subconv-image .
```
2. 启动 Docker Container
```commandline
docker run --name subconv -p 8088:8088 -d subconv-image
```

## 贡献
如果您发现任何问题或想要贡献代码，请访问 [GitHub 仓库](https://github.com/this-cat/subconv)。

随时根据项目的发展和要求进一步补充 README.md 文件。