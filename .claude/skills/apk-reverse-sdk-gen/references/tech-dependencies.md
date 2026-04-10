# 工具依赖与技术栈

## 必需工具

### Java JDK

**用途**: 反编译工具运行基础

**版本要求**: >= 11

**安装方式**:

```bash
# Windows (使用scoop或choco)
scoop install openjdk11
choco install openjdk11

# Linux
sudo apt install openjdk-11-jdk

# macOS
brew install openjdk@11
```

**验证**:
```bash
java -version
# 应显示 11.x.x 或更高版本
```

---

### apktool

**用途**: APK解包，提取资源和smali代码

**版本要求**: >= 2.8

**安装方式**:

```bash
# Windows
# 1. 下载 apktool_2.x.x.jar 和 apktool.bat wrapper
# 2. 放置到 PATH 目录

# Linux/macOS
sudo apt install apktool  # Linux
brew install apktool      # macOS

# 或手动安装
wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar
sudo mv apktool_2.9.3.jar /usr/local/bin/apktool.jar
echo '#!/bin/bash\njava -jar /usr/local/bin/apktool.jar "$@"' | sudo tee /usr/local/bin/apktool
sudo chmod +x /usr/local/bin/apktool
```

**验证**:
```bash
apktool --version
```

**常用命令**:
```bash
# 解包APK
apktool d app.apk -o output_dir

# 重新打包
apktool b input_dir -o new_app.apk
```

---

### jadx

**用途**: DEX/APK反编译为Java源码

**版本要求**: >= 1.4

**安装方式**:

```bash
# Windows
# 下载 https://github.com/skylot/jadx/releases
# 解压后将bin目录添加到PATH

# Linux/macOS
# 使用snap或brew
sudo snap install jadx  # Linux
brew install jadx       # macOS

# 或手动安装
wget https://github.com/skylot/jadx/releases/download/v1.4.7/jadx-1.4.7.zip
unzip jadx-1.4.7.zip -d jadx
sudo mv jadx/bin/jadx /usr/local/bin/
sudo mv jadx/bin/jadx-gui /usr/local/bin/
```

**验证**:
```bash
jadx --version
```

**常用命令**:
```bash
# 反编译APK
jadx -d output_dir app.apk

# 启动GUI
jadx-gui app.apk

# 常用参数
jadx -d output --show-bad-code --deobf app.apk
```

---

## 动态调试工具（可选）

### Frida

**用途**: 动态Hook注入、运行时调试

**版本要求**: >= 16

**安装方式**:
```bash
# Python包
pip install frida frida-tools

# 验证
frida --version
```

**Android设备配置**:
```bash
# 1. 下载对应架构的frida-server
# https://github.com/frida/frida/releases

# 2. 推送到设备
adb push frida-server /data/local/tmp/

# 3. 启动服务
adb shell
su
chmod +x /data/local/tmp/frida-server
/data/local/tmp/frida-server &

# 4. 验证连接
frida-ps -U
```

---

### FART (脱壳工具)

**用途**: APK脱壳

**安装方式**:
```bash
# FART是基于Frida的脱壳脚本
# 下载 https://github.com/hanbinglengyue/FART

# 使用
frida -U -f com.example.app -l fart.js
```

---

## Python依赖

### 必需依赖

```txt
# requirements.txt
frida>=16.0.0
frida-tools>=12.0.0
pycryptodome>=3.19.0
requests>=2.31.0
lxml>=4.9.0
beautifulsoup4>=4.12.0
loguru>=0.7.0
```

**安装**:
```bash
pip install -r requirements.txt
```

### 可选依赖

```txt
androguard>=3.4.0        # APK分析库
apktool-wrapper>=1.0.0   # apktool Python封装
jadx-wrapper>=1.0.0      # jadx Python封装
```

---

## Android SDK工具（可选）

### adb

**用途**: Android设备连接和调试

**安装方式**:
```bash
# Windows (使用scoop)
scoop install adb

# Linux
sudo apt install android-tools-adb

# macOS
brew install android-platform-tools
```

**验证**:
```bash
adb version
adb devices
```

### aapt

**用途**: APK信息提取

**安装方式**:
```bash
# 包含在Android SDK build-tools中
# 或单独安装

# Linux
sudo apt install aapt

# macOS
brew install aapt
```

---

## 工具链总结

| 工具 | 用途 | 必需 | 版本要求 |
|------|------|------|----------|
| Java JDK | 运行环境 | 是 | >= 11 |
| apktool | APK解包 | 是 | >= 2.8 |
| jadx | DEX反编译 | 是 | >= 1.4 |
| Frida | 动态调试 | 否 | >= 16 |
| FART | 脱壳 | 否 | - |
| adb | 设备调试 | 否 | - |
| aapt | APK信息 | 否 | - |

---

## 环境检测

运行环境检测脚本:

```bash
python scripts/check-environment.py
```

自动安装Python依赖:

```bash
python scripts/check-environment.py --auto-install
```