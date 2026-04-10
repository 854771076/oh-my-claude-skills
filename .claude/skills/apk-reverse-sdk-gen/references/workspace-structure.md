# 工作目录结构

## 目录概览

```
apk-projects/
└── {package_name}/              # 以APK包名命名的工作目录
    ├── project-config.json      # 项目配置文件
    ├── README.md                # 项目说明文档
    ├── unpacked/                # APK解包目录
    │   ├── AndroidManifest.xml  # 清单文件
    │   ├── smali/               # smali代码目录
    │   ├── res/                 # 资源文件
    │   ├── assets/              # assets资源
    │   ├── lib/                 # Native库
    │   └── original/            # 原始文件(可能包含加密DEX)
    ├── decompiled/              # jadx反编译目录
    │   ├── sources/             # Java源码
    │   │   └── {package}/       # 按包名组织的源码
    │   └── resources/           # 资源文件
    ├── unpacked-dex/            # 脱壳后DEX目录
    ├── analysis/                # 分析结果目录
    │   ├── apk-info.json        # APK基本信息
    │   ├── packer-detection.json # 加壳检测结果
    │   ├── crypto-analysis.json # 加密参数分析
    │   ├── api-list.json        # API接口清单
    │   └── obfuscation-report.json # 混淆分析报告
    ├── hook-output/             # Frida Hook输出目录
    │   └── intercept/           # 拦截数据
    ├── output/                  # 最终输出目录
    │   ├── sdk/                 # SDK代码
    │   │   ├── python/          # Python SDK
    │   │   ├── java/            # Java SDK
    │   │   └── js/              # JavaScript SDK
    │   ├── analysis-report.md   # 分析报告
    │   ├── sdk-document.md      # SDK文档
    │   └── README.md            # 使用说明
    ├── scripts/                 # 分析脚本(从skill复制)
    ├── hooks/                   # Frida Hook脚本(从skill复制)
    └── assets/                  # SDK模板(从skill复制)
```

## 配置文件说明

### project-config.json

```json
{
  "apk_info": {
    "apk_path": "/path/to/app.apk",
    "file_name": "app.apk",
    "file_size": 12345678,
    "package_name": "com.example.app",
    "version": "1.0.0"
  },
  "workspace_path": "/path/to/apk-projects/com_example_app",
  "created_at": "2025-01-01T00:00:00",
  "sdk_languages": ["python", "java", "js"],
  "workflow_config": {
    "unpacking": true,
    "decompilation": true,
    "unpacking_detection": true,
    "encryption_analysis": true,
    "api_extraction": true,
    "obfuscation_analysis": true,
    "sdk_generation": true
  },
  "tools_config": {
    "apktool": { "enabled": true },
    "jadx": { "enabled": true },
    "frida": { "enabled": false },
    "fart": { "enabled": false }
  }
}
```

## 各阶段输出说明

### Phase 1: APK解包

**输出目录**: `unpacked/`

包含:
- `AndroidManifest.xml` - 解码后的清单文件
- `smali/` - smali字节码
- `res/` - 解码后的资源文件
- `assets/` - 原始assets资源
- `lib/` - Native库(.so文件)
- `original/` - META-INF等原始文件

### Phase 2: DEX反编译

**输出目录**: `decompiled/`

包含:
- `sources/` - 反编译的Java源码
- `resources/` - 资源文件
- `errors/` - 反编译错误日志

### Phase 3: 分析结果

**输出目录**: `analysis/`

文件说明:

| 文件名 | 说明 |
|--------|------|
| `apk-info.json` | APK基本信息（包名、版本、权限、组件） |
| `packer-detection.json` | 加壳检测结果 |
| `crypto-analysis.json` | 加密算法分析结果 |
| `api-list.json` | 提取的API接口清单 |
| `obfuscation-report.json` | 代码混淆分析报告 |

### Phase 4: Hook输出

**输出目录**: `hook-output/`

包含:
- `intercept/` - Frida拦截的数据
- `analysis.json` - Hook数据分析结果

### Phase 5: SDK输出

**输出目录**: `output/`

包含:
- `sdk/python/` - Python SDK代码
- `sdk/java/` - Java SDK代码
- `sdk/js/` - JavaScript SDK代码
- `analysis-report.md` - 完整分析报告
- `sdk-document.md` - SDK使用文档
- `README.md` - 项目使用说明