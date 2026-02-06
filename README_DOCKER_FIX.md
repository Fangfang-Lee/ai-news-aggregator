# Docker 镜像源问题修复指南

## 问题描述

构建时出现错误：
```
failed to solve: rpc error: code = Unknown desc = failed to solve with frontend dockerfile.v0: 
failed to create LLB definition: failed to do request: 
Head "https://docker.mirrors.ustc.edu.cn/v2/library/python/manifests/3.11-slim?ns=docker.io": EOF
```

这是因为 Docker 配置了中科大镜像源，但镜像源可能无法访问或网络有问题。

## 解决方案

### 方案一：修改 Docker 镜像源配置（推荐）

1. **备份并修改 Docker 配置**：
   ```bash
   # 备份原配置
   cp ~/.docker/daemon.json ~/.docker/daemon.json.backup
   
   # 编辑配置文件，移除或替换镜像源
   nano ~/.docker/daemon.json
   ```

2. **修改配置内容**，将 `registry-mirrors` 部分改为：
   ```json
   {
     "builder": {
       "gc": {
         "defaultKeepStorage": "20GB",
         "enabled": true
       }
     },
     "experimental": false,
     "registry-mirrors": [
       "https://dockerhub.azk8s.cn",
       "https://reg-mirror.qiniu.com"
     ]
   }
   ```
   
   或者完全移除镜像源，使用官方 Docker Hub：
   ```json
   {
     "builder": {
       "gc": {
         "defaultKeepStorage": "20GB",
         "enabled": true
       }
     },
     "experimental": false
   }
   ```

3. **重启 Docker Desktop**：
   - 点击菜单栏的 Docker 图标
   - 选择 "Quit Docker Desktop"
   - 重新启动 Docker Desktop
   - 等待完全启动

4. **重新构建和启动**：
   ```bash
   cd /Users/jason/cursor/ai-news-aggregator
   ./start.sh
   ```

### 方案二：使用修复脚本

运行修复脚本（会自动移除镜像源配置）：
```bash
cd /Users/jason/cursor/ai-news-aggregator
./fix-docker-mirror.sh
```

然后按照脚本提示重启 Docker Desktop。

### 方案三：手动拉取镜像后构建

如果镜像源有问题，可以先手动拉取镜像：

```bash
# 直接使用官方 Docker Hub 拉取镜像
docker pull python:3.11-slim
docker pull postgres:15-alpine
docker pull redis:7-alpine

# 然后重新构建
cd /Users/jason/cursor/ai-news-aggregator
docker-compose build
docker-compose up -d
```

### 方案四：使用代理或 VPN

如果网络访问 Docker Hub 有问题，可以：
1. 配置 Docker 使用代理
2. 或使用 VPN 连接

## 验证修复

修复后，运行以下命令验证：
```bash
docker pull python:3.11-slim
```

如果成功拉取镜像，说明问题已解决。
