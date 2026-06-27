# JMComic Code Wiki

> 版本：v2.7.0  
> 最后更新：2026-06-27

---

## 目录

1. [项目概述](#1-项目概述)
2. [项目整体架构](#2-项目整体架构)
3. [模块依赖关系](#3-模块依赖关系)
4. [主要模块职责](#4-主要模块职责)
5. [核心类详解](#5-核心类详解)
6. [插件系统](#6-插件系统)
7. [Feature 特性机制](#7-feature-特性机制)
8. [异步架构](#8-异步架构)
9. [配置系统](#9-配置系统)
10. [项目运行方式](#10-项目运行方式)
11. [异常处理机制](#11-异常处理机制)
12. [目录结构](#12-目录结构)

---

## 1. 项目概述

**JMComic** 是一个用于访问禁漫天堂（JMComic）的 Python API 库，提供网页端和移动端两套客户端实现，支持本子搜索、下载、收藏夹管理等功能。项目集成了 GitHub Actions 下载器，支持同步和异步两套 API。

### 1.1 核心功能

- **本子下载**：支持整本下载、单章下载、批量下载
- **图片解码**：实现禁漫图片分割算法的解密还原
- **搜索功能**：支持多维度搜索（分类、标签、作者、关键词等）
- **用户系统**：登录、收藏夹管理、评论
- **多客户端**：网页端（HTML解析）和移动端（API接口）
- **插件扩展**：内置丰富插件，支持自定义插件
- **异步支持**：完整的 async/await 异步 API

### 1.2 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.9+ |
| HTTP 请求 | curl_cffi（绕过 Cloudflare） |
| 图片处理 | Pillow |
| 加密解密 | pycryptodome |
| 配置文件 | PyYAML |
| 工具库 | commonx |

---

## 2. 项目整体架构

项目采用**分层架构**设计，自底向上分为以下几层：

```
┌─────────────────────────────────────────────────────┐
│                   API 层 (api.py)                   │
│  download_album / download_photo / create_option    │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│               Downloader 层 (下载调度)               │
│  JmDownloader / JmAsyncDownloader                   │
│  - 调度下载流程                                      │
│  - 多线程/异步并发控制                               │
│  - 回调与钩子管理                                    │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                 Option 层 (配置管理)                 │
│  JmOption / DirRule / CacheRegistry                 │
│  - 统一配置入口                                      │
│  - 插件管理与调用                                    │
│  - 客户端构建                                        │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                Client 层 (网络请求)                  │
│  JmcomicClient / AbstractJmClient                   │
│  - 域名管理与切换                                    │
│  - 请求重试机制                                      │
│  - API 调用与数据解析                                │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                Toolkit 层 (工具集)                   │
│  JmcomicText / JmCryptoTool / JmImageTool           │
│  - 文本解析与正则                                    │
│  - 加解密算法                                        │
│  - 图片处理                                          │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                Entity 层 (数据实体)                  │
│  JmAlbumDetail / JmPhotoDetail / JmImageDetail      │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                 Config 层 (全局配置)                 │
│  JmModuleConfig / JmMagicConstants                  │
└─────────────────────────────────────────────────────┘
```

---

## 3. 模块依赖关系

根据 [\_\_init\_\_.py](file:///workspace/src/jmcomic/__init__.py#L1-L5) 中的注释，模块依赖关系如下：

```
config <--- entity <--- toolkit <--- client <--- option <--- downloader
  │          │           │            │           │             │
  ▼          ▼           ▼            ▼           ▼             ▼
jm_config  jm_entity  jm_toolkit  jm_client_*  jm_option  jm_downloader
                                                         
                    api.py ──────► (使用 downloader + option)
                    jm_plugin ────► (依赖 option)
                    jm_feature ───► (依赖 plugin)
                    cli.py ───────► (使用 api)
```

### 3.1 依赖方向说明

- **config 层**：最底层，无内部依赖，提供全局常量和模块级配置
- **entity 层**：依赖 config，定义数据实体类
- **toolkit 层**：依赖 entity，提供工具函数和业务逻辑工具
- **client 层**：依赖 toolkit，封装网络请求和 API 调用
- **option 层**：依赖 client，管理配置和插件
- **downloader 层**：依赖 option，调度下载流程
- **api 层**：最上层，对外暴露简洁的函数接口

---

## 4. 主要模块职责

### 4.1 jm_config.py — 全局配置模块

**文件路径**：[jm_config.py](file:///workspace/src/jmcomic/jm_config.py)

**核心职责**：
- 定义禁漫相关的常量（搜索参数、分类参数、API密钥等）
- 管理模块级别的全局配置（域名、Header、默认配置等）
- 提供类注册机制（客户端、插件、异常监听器）
- 日志系统配置
- 默认 Option 配置字典

**关键类**：
- `JmMagicConstants`：禁漫 API 相关的魔法常量
- `JmModuleConfig`：模块级别共用配置的核心类
- `PrettyFormatter`：带 ANSI 颜色的日志格式化器

### 4.2 jm_entity.py — 数据实体模块

**文件路径**：[jm_entity.py](file:///workspace/src/jmcomic/jm_entity.py)

**核心职责**：
- 定义所有业务实体类
- 提供实体间的关联关系（album → photo → image）
- 支持索引访问和迭代
- 提供便捷属性（如 `oname`, `authoroname`, `idoname`）

**核心类层次**：
```
JmBaseEntity
├── DetailEntity (IndexedEntity)
│   ├── JmAlbumDetail  — 本子详情
│   └── JmPhotoDetail  — 章节详情
└── JmImageDetail      — 图片详情

Downloadable  (可下载混入类)
├── JmImageDetail
├── JmPhotoDetail
└── JmAlbumDetail
```

### 4.3 jm_toolkit.py — 工具集模块

**文件路径**：[jm_toolkit.py](file:///workspace/src/jmcomic/jm_toolkit.py)

**核心职责**：
- 文本解析（正则匹配、HTML解析、JSON提取）
- 加解密工具（移动端API加解密算法）
- 图片处理（图片分割还原、格式转换）
- 异常工具（统一抛异常、上下文传递）
- API 适配工具
- 分页工具

**关键工具类**：
- `JmcomicText`：文本解析工具集（正则、域名解析、车号解析等）
- `JmCryptoTool`：加解密工具（移动端API token、数据加密）
- `JmImageTool`：图片处理工具（解密、保存、格式转换）
- `ExceptionTool`：异常抛出工具（带上下文）

### 4.4 jm_client_interface.py — 客户端接口模块

**文件路径**：[jm_client_interface.py](file:///workspace/src/jmcomic/jm_client_interface.py)

**核心职责**：
- 定义客户端接口抽象
- 定义响应实体类（JmResp 及其子类）
- 声明同步和异步客户端的接口契约

**接口组成**：
```
JmcomicClient (同步客户端总接口)
├── JmDetailClient      — 详情查询接口
├── JmUserClient        — 用户相关接口
├── JmImageClient       — 图片下载接口
├── JmSearchAlbumClient — 搜索接口
└── JmCategoryClient    — 分类/排行榜接口

AsyncJmcomicClient (异步客户端总接口)
└── ... （对应同步版本）
```

**响应类层次**：
```
JmResp
├── JmImageResp          — 图片响应
├── JmJsonResp           — JSON响应
│   ├── JmApiResp        — API响应（含加解密）
│   └── JmAlbumCommentResp — 评论响应
```

### 4.5 jm_client_impl.py — 客户端实现模块

**文件路径**：[jm_client_impl.py](file:///workspace/src/jmcomic/jm_client_impl.py)

**核心职责**：
- 提供同步客户端的抽象基类实现
- 实现域名管理、自动切换、重试机制
- 实现缓存机制
- 提供网页端（html）和移动端（api）两种具体实现

**核心类**：
- `AbstractJmClient`：抽象基类，实现通用功能
- `JmHtmlClient`：网页端客户端（HTML解析），`client_key = 'html'`
- `JmApiClient`：移动端客户端（API接口），`client_key = 'api'`

### 4.6 jm_option.py — 配置模块

**文件路径**：[jm_option.py](file:///workspace/src/jmcomic/jm_option.py)

**核心职责**：
- 管理下载配置（Option）
- 路径规则解析（DirRule DSL）
- 缓存注册与管理
- 插件管理与调用
- 客户端构建

**核心类**：
- `JmOption`：配置对象，从配置文件或字典构建
- `DirRule`：下载目录规则解析器（DSL 驱动）
- `CacheRegistry`：缓存注册表

### 4.7 jm_downloader.py — 下载器模块

**文件路径**：[jm_downloader.py](file:///workspace/src/jmcomic/jm_downloader.py)

**核心职责**：
- 调度下载流程（album → photo → image）
- 管理下载并发（多线程）
- 回调钩子执行（before/after）
- 下载结果记录（成功/失败）
- Feature 特性调用

**核心类层次**：
```
DownloadCallback (回调接口)
└── BaseDownloader (基类，回调 + 钩子 + Features)
    └── JmDownloader (同步下载调度)
```

### 4.8 jm_plugin.py — 插件模块

**文件路径**：[jm_plugin.py](file:///workspace/src/jmcomic/jm_plugin.py)

**核心职责**：
- 定义插件基类和插件接口
- 提供内置插件实现
- 插件参数校验与异常处理

**插件基类**：`JmOptionPlugin`

### 4.9 jm_feature.py — Feature 特性模块

**文件路径**：[jm_feature.py](file:///workspace/src/jmcomic/jm_feature.py)

**核心职责**：
- 封装高级功能特性（如导出PDF、ZIP、长图）
- 提供简洁的使用方式（无需了解插件细节）
- 支持链式组合（`+` / `|` / `&` 运算符）

**核心类**：
- `Feature`：特性基类
- `PluginFeature`：基于插件的特性实现
- `FeatureChain`：特性链（多个特性组合）

### 4.10 api.py — 对外 API 模块

**文件路径**：[api.py](file:///workspace/src/jmcomic/api.py)

**核心职责**：
- 提供简洁的顶层 API 函数
- 封装 Option 和 Downloader 的创建
- 支持批量下载

**主要函数**：
- `download_album()`：下载本子
- `download_photo()`：下载章节
- `download_batch()`：批量下载
- `create_option_by_file()`：从文件创建配置
- `new_downloader()`：创建下载器

### 4.11 jm_async_client.py — 异步客户端模块

**文件路径**：[jm_async_client.py](file:///workspace/src/jmcomic/jm_async_client.py)

**核心职责**：
- 提供异步版本的移动端 API 客户端
- 基于 `curl_cffi.requests.AsyncSession` 实现
- 支持异步并发控制

**核心类**：`AsyncJmApiClient`，`client_key = 'async_api'`

### 4.12 jm_async_downloader.py — 异步下载器模块

**文件路径**：[jm_async_downloader.py](file:///workspace/src/jmcomic/jm_async_downloader.py)

**核心职责**：
- 全异步流水线下载器
- 下载 IO 与 CPU 解密流水线化
- 通过 `asyncio.Semaphore` 控制并发
- 继承同步下载器的回调体系

**核心类**：`JmAsyncDownloader`

### 4.13 cli.py — 命令行模块

**文件路径**：[cli.py](file:///workspace/src/jmcomic/cli.py)

**核心职责**：
- 提供命令行入口
- 解析命令行参数
- 调用 API 执行下载/查看

**入口类**：
- `JmcomicUI`：下载命令行（`jmcomic`）
- `JmViewUI`：查看命令行（`jmv`）

### 4.14 jm_exception.py — 异常模块

**文件路径**：[jm_exception.py](file:///workspace/src/jmcomic/jm_exception.py)

**核心职责**：
- 定义项目异常类层次
- 提供异常工具类

**异常类层次**：
```
JmcomicException
├── ResponseUnexpectedException  — 响应异常
│   ├── JsonResolveFailException — JSON解析失败
│   └── MissingAlbumPhotoException — 本子/章节不存在
├── RegularNotMatchException     — 正则不匹配
├── RequestRetryAllFailException — 请求全部重试失败
└── PartialDownloadFailedException — 部分下载失败
```

---

## 5. 核心类详解

### 5.1 JmModuleConfig — 模块配置中心

**位置**：[jm_config.py#L110-L576](file:///workspace/src/jmcomic/jm_config.py#L110-L576)

**核心职责**：全局配置管理、组件注册、工厂方法

#### 5.1.1 类注册表机制

项目通过 `JmModuleConfig` 维护三个核心注册表，实现**插件式架构**：

| 注册表 | 作用 | 注册方法 |
|--------|------|----------|
| `REGISTRY_CLIENT` | 同步客户端实现 | `register_client()` |
| `REGISTRY_ASYNC_CLIENT` | 异步客户端实现 | `register_async_client()` |
| `REGISTRY_PLUGIN` | 插件实现 | `register_plugin()` |
| `REGISTRY_EXCEPTION_LISTENER` | 异常监听器 | `register_exception_listener()` |

注册时机：在 [\_\_init\_\_.py](file:///workspace/src/jmcomic/__init__.py#L19-L39) 模块导入时自动扫描并注册。

#### 5.1.2 可重写类配置

支持通过修改类属性来自定义核心类：

| 属性 | 说明 | 获取方法 |
|------|------|----------|
| `CLASS_DOWNLOADER` | 下载器类 | `downloader_class()` |
| `CLASS_OPTION` | 配置类 | `option_class()` |
| `CLASS_ALBUM` | 本子实体类 | `album_class()` |
| `CLASS_PHOTO` | 章节实体类 | `photo_class()` |
| `CLASS_IMAGE` | 图片实体类 | `image_class()` |

#### 5.1.3 域名动态获取

由于禁漫域名频繁变更，项目支持运行时动态获取可用域名：

- `get_html_domain()`：获取网页端可用域名（通过永久网域跳转）
- `get_html_domain_all()`：获取全部网页端域名（通过发布页）
- `get_html_domain_all_via_github()`：通过 GitHub 获取域名

### 5.2 JmAlbumDetail — 本子实体

**位置**：[jm_entity.py#L461-L570](file:///workspace/src/jmcomic/jm_entity.py#L461-L570)

**核心属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `album_id` | str | 本子ID（车号） |
| `name` | str | 完整标题 |
| `scramble_id` | str | 图片分割ID |
| `page_count` | int | 总页数 |
| `authors` | list | 作者列表 |
| `tags` | list | 标签列表 |
| `works` | list | 作品列表 |
| `actors` | list | 登场人物 |
| `pub_date` | str | 发布日期 |
| `update_date` | str | 更新日期 |
| `likes` | str | 点赞数 |
| `views` | str | 观看数 |
| `comment_count` | int | 评论数 |

**便捷属性**：
- `id` → `album_id`
- `title` → `name`
- `author` → 第一个作者
- `oname` → 原始名称（去除汉化组等信息）
- `authoroname` → `【作者】原始名称`
- `idoname` → `[ID] 原始名称`

**索引访问**：
```python
album = client.get_album_detail('123456')
photo = album[0]       # 第一章
photos = album[:5]     # 前五章
len(album)             # 章节数
for photo in album:    # 迭代所有章节
    ...
```

### 5.3 JmPhotoDetail — 章节实体

**位置**：[jm_entity.py#L299-L458](file:///workspace/src/jmcomic/jm_entity.py#L299-L458)

**核心属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `photo_id` | str | 章节ID |
| `name` | str | 章节名称 |
| `scramble_id` | str | 图片分割ID |
| `sort` | int | 排序号 |
| `page_arr` | list | 图片文件名列表 |
| `data_original_domain` | str | 图片CDN域名 |
| `from_album` | JmAlbumDetail | 所属本子 |
| `index` | int | 在本子中的序号（从1开始） |

### 5.4 JmImageDetail — 图片实体

**位置**：[jm_entity.py#L201-L296](file:///workspace/src/jmcomic/jm_entity.py#L201-L296)

**核心属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `aid` | str | 所属章节ID |
| `scramble_id` | str | 分割ID |
| `img_url` | str | 图片URL |
| `img_file_name` | str | 文件名（不含后缀） |
| `img_file_suffix` | str | 文件后缀 |
| `download_url` | str | 完整下载URL（含查询参数） |
| `from_photo` | JmPhotoDetail | 所属章节 |
| `index` | int | 在章节中的序号 |

### 5.5 JmcomicClient — 客户端接口

**位置**：[jm_client_interface.py#L479-L520](file:///workspace/src/jmcomic/jm_client_interface.py#L479-L520)

**主要接口方法**：

#### 详情查询
- `get_album_detail(album_id)` → JmAlbumDetail
- `get_photo_detail(photo_id, fetch_album=True, fetch_scramble_id=True)` → JmPhotoDetail
- `check_photo(photo)` — 补全 photo 的下载相关信息

#### 用户相关
- `login(username, password)` — 登录
- `album_comment(video_id, comment, ...)` — 评论
- `favorite_folder(page, order_by, folder_id, username)` → JmFavoritePage
- `add_favorite_album(album_id, folder_id)` — 加入收藏

#### 图片下载
- `download_image(img_url, img_save_path, scramble_id, decode_image)`
- `download_by_image_detail(image, img_save_path, decode_image)`
- `get_jm_image(img_url)` → JmImageResp

#### 搜索与分类
- `search_album(keyword, page, order_by, time, ...)` → JmSearchPage
- `search_category_album(page, category, sub_category, order_by, time)` → JmCategoryPage

#### 域名管理
- `get_domain_list()` → List[str]
- `set_domain_list(domain_list)`

### 5.6 AbstractJmClient — 抽象客户端基类

**位置**：[jm_client_impl.py#L7-L200](file:///workspace/src/jmcomic/jm_client_impl.py#L7-L200)

**核心机制**：

#### 5.6.1 请求重试与域名切换

`request_with_retry()` 方法实现了完整的容错机制：

```
请求失败
  │
  ├─ 重试次数未满 → 同一域名重试
  │
  └─ 重试次数已满 → 切换下一个域名，重试次数归零
                    │
                    └─ 所有域名均失败 → fallback
```

**关键参数**：
- `retry_times`：每个域名的重试次数
- `domain_list`：域名列表
- `domain_retry_strategy`：自定义重试策略

#### 5.6.2 缓存机制

通过 `CLIENT_CACHE` 字典缓存 API 调用结果，减少重复请求。

### 5.7 JmOption — 配置对象

**位置**：[jm_option.py#L180-L400](file:///workspace/src/jmcomic/jm_option.py#L180-L400)

**创建方式**：

```python
# 1. 默认配置
option = JmOption.default()

# 2. 从文件创建
option = JmOption.from_file('option.yml')

# 3. 从字典构建
option = JmOption.construct({...})
```

**核心配置域**：

| 配置域 | 说明 |
|--------|------|
| `dir_rule` | 下载目录规则 |
| `download` | 下载相关配置（缓存、图片、线程数） |
| `client` | 客户端配置（域名、实现类型、重试） |
| `plugins` | 插件配置 |

#### 5.7.1 DirRule — 目录规则 DSL

**DSL 语法规则**：
- 用 `_` 或 `/` 分隔多级目录
- `Bd` 表示基础目录（Base Directory）
- `Axxx` 表示使用 Album 的 `xxx` 属性
- `Pxxx` 表示使用 Photo 的 `xxx` 属性
- 支持 f-string 格式（包含 `{` 时自动识别）

**示例**：
```
Bd_Pname           →  base_dir/photo_name
Bd_Aauthor_Ptitle  →  base_dir/album_author/photo_title
```

**内置字段示例**：
- `Aid` / `Aname` / `Aauthor` / `Aoname` / `Aidname`
- `Pid` / `Pname` / `Pindex` / `Pindextitle`

### 5.8 JmDownloader — 同步下载器

**位置**：[jm_downloader.py#L243-L350](file:///workspace/src/jmcomic/jm_downloader.py#L243-L350)

**下载流程**：

```
download_album(album_id)
  │
  ├─ get_album_detail(album_id)  # 获取本子详情
  │
  └─ download_by_album_detail(album)
       │
       ├─ before_album(album)   # 钩子：下载前
       │
       ├─ 遍历所有章节（多线程）
       │    │
       │    └─ download_by_photo_detail(photo)
       │         │
       │         ├─ check_photo(photo)      # 补全下载信息
       │         ├─ before_photo(photo)     # 钩子：章节下载前
       │         ├─ 遍历所有图片（多线程）
       │         │    └─ download_image(image)
       │         └─ after_photo(photo)      # 钩子：章节下载后
       │
       └─ after_album(album)     # 钩子：下载后
```

**并发控制**：
- 章节级并发：`download.threading.photo`（默认 CPU 核心数）
- 图片级并发：`download.threading.image`（默认 30）

**下载结果**：
- `download_success_dict`：成功下载记录
- `download_failed_image`：失败的图片列表
- `download_failed_photo`：失败的章节列表
- `all_success`：是否全部成功
- `has_download_failures`：是否有失败

### 5.9 JmAsyncDownloader — 异步下载器

**位置**：[jm_async_downloader.py#L22-L200](file:///workspace/src/jmcomic/jm_async_downloader.py#L22-L200)

**核心设计**：

1. **IO 与 CPU 流水线化**：网络下载（asyncio）与图片解密（ThreadPoolExecutor）并行
2. **Semaphore 并发控制**：使用 `asyncio.Semaphore` 控制并发数
3. **复用回调体系**：继承 BaseDownloader，使用相同的插件和 Feature 机制

**并发配置**：
- `_image_semaphore`：图片并发（默认 30）
- `_photo_semaphore`：章节并发（默认 CPU 核心数）
- `_decode_pool`：解密线程池

---

## 6. 插件系统

### 6.1 插件基类

**位置**：[jm_plugin.py#L15-L140](file:///workspace/src/jmcomic/jm_plugin.py#L15-L140)

**JmOptionPlugin 核心接口**：

| 方法/属性 | 说明 |
|-----------|------|
| `plugin_key` | 插件唯一标识（类属性） |
| `invoke(**kwargs)` | 执行插件功能（子类需实现） |
| `build(option)` | 类方法，创建插件实例 |
| `log(msg, topic)` | 插件日志 |
| `require_param(case, msg)` | 参数校验（抛 PluginValidationException） |
| `execute_deletion(paths)` | 删除原文件（受 delete_original_file 控制） |

### 6.2 插件调用时机

插件通过 Option 在下载钩子中被调用：

| 钩子 | 调用时机 | 参数 |
|------|----------|------|
| `before_album` | 本子下载前 | album, downloader |
| `after_album` | 本子下载后 | album, downloader |
| `before_photo` | 章节下载前 | photo, downloader |
| `after_photo` | 章节下载后 | photo, downloader |
| `before_image` | 图片下载前 | image, downloader |
| `after_image` | 图片下载后 | image, downloader |

### 6.3 内置插件列表

| plugin_key | 插件类 | 功能说明 |
|------------|--------|----------|
| `login` | JmLoginPlugin | 登录禁漫，保存cookies |
| `usage_log` | JmUsageLogPlugin | 使用日志记录 |
| `find_update` | JmFindUpdatePlugin | 只下载新章节 |
| `zip` | JmZipPlugin | 压缩为ZIP文件 |
| `client_proxy` | JmClientProxyPlugin | 客户端代理配置 |
| `image_suffix_filter` | JmImageSuffixFilterPlugin | 图片后缀过滤 |
| `send_qq_email` | JmSendQQEmailPlugin | 发送QQ邮件通知 |
| `log_topic_filter` | JmLogTopicFilterPlugin | 日志主题过滤 |
| `auto_set_browser_cookies` | JmAutoSetBrowserCookiesPlugin | 自动获取浏览器cookies |
| `favorite_folder_export` | JmFavoriteFolderExportPlugin | 导出收藏夹为CSV |
| `img2pdf` | JmImg2PdfPlugin | 合并图片为PDF |
| `long_img` | JmLongImgPlugin | 合并为长图 |
| `jm_server` | JmServerPlugin | JM服务端 |
| `subscribe_album_update` | JmSubscribeAlbumUpdatePlugin | 订阅更新 |
| `skip_photo_with_few_images` | JmSkipPhotoWithFewImagesPlugin | 跳过图片少的章节 |
| `delete_duplicated_files` | JmDeleteDuplicatedFilesPlugin | 删除重复文件 |
| `replace_path_string` | JmReplacePathStringPlugin | 替换路径字符串 |
| `advanced_retry` | JmAdvancedRetryPlugin | 高级重试策略 |
| `download_cover` | JmDownloadCoverPlugin | 下载封面 |

### 6.4 插件配置示例

```yaml
plugins:
  login:
    username: "your_username"
    password: "your_password"
  
  img2pdf:
    delete_original_file: true
  
  zip:
    with_photo_dir: false
```

---

## 7. Feature 特性机制

### 7.1 设计思想

Feature 是对插件的高级封装，用户无需了解插件名称、调用时机、参数细节，只需简单使用即可。

### 7.2 使用方式

```python
from jmcomic import download_album, Feature

# 最简单方式
download_album('123456', extra=Feature.export_pdf)

# 带自定义参数
download_album('123456', extra=Feature.export_pdf(pdf_dir='./output'))

# 多个 Feature（列表形式）
download_album('123456', extra=[Feature.export_pdf, Feature.export_zip])

# 多个 Feature（运算符形式）
download_album('123456', extra=Feature.export_pdf + Feature.export_long_img)
```

### 7.3 内置 Feature

| Feature | 对应插件 | 说明 |
|---------|----------|------|
| `Feature.export_pdf` | img2pdf | 导出为 PDF |
| `Feature.export_zip` | zip | 导出为 ZIP |
| `Feature.export_long_img` | long_img | 导出为长图 |

---

## 8. 异步架构

### 8.1 异步 API

```python
import asyncio
import jmcomic

# 异步下载本子
asyncio.run(jmcomic.download_album_async('123456'))

# 异步下载章节
asyncio.run(jmcomic.download_photo_async('789012'))

# 异步批量下载
asyncio.run(jmcomic.download_batch_async(['123', '456']))
```

### 8.2 异步客户端

`AsyncJmApiClient` 基于 `curl_cffi.requests.AsyncSession` 实现：
- 完整支持移动端 API 的异步调用
- 会话池大小根据下载并发自适应
- 支持异步缓存

### 8.3 异步下载器

`JmAsyncDownloader` 设计特点：
- 继承 `BaseDownloader`，复用回调和插件体系
- 网络 IO 全异步化
- CPU 密集的图片解密卸载到线程池
- 使用 `asyncio.Semaphore` 精细控制并发

---

## 9. 配置系统

### 9.1 默认配置

完整默认配置定义在 [jm_config.py#L475-L506](file:///workspace/src/jmcomic/jm_config.py#L475-L506)：

```python
DEFAULT_OPTION_DICT = {
    'log': None,
    'dir_rule': {
        'rule': 'Bd_Pname',
        'base_dir': None,       # 默认当前工作目录
        'normalize_zh': None,
    },
    'download': {
        'cache': True,
        'image': {
            'decode': True,
            'suffix': None,
        },
        'threading': {
            'image': 30,
            'photo': None,      # 默认 CPU 核心数
        },
    },
    'client': {
        'cache': None,
        'domain': [],
        'postman': {
            'type': 'curl_cffi',
            'meta_data': {
                'impersonate': 'chrome',
                'headers': None,
                'proxies': None,  # 默认系统代理
            }
        },
        'impl': None,            # 默认 'api' (移动端)
        'async_impl': 'async_api',
        'retry_times': 5,
    },
    'plugins': {
        'valid': 'log',
    },
}
```

### 9.2 配置文件格式

支持 YAML 格式（推荐）、JSON 等格式。

```yaml
# option.yml 示例
dir_rule:
  rule: Bd_Aauthoroname_Pindextitle
  base_dir: D:/JMComic
  normalize_zh: zh-cn

download:
  cache: true
  image:
    decode: true
    suffix: .png
  threading:
    image: 30
    photo: 4

client:
  impl: api
  retry_times: 5
  domain:
    - www.example.com

plugins:
  login:
    username: user
    password: pass
  img2pdf:
    delete_original_file: true
```

### 9.3 客户端类型

| impl | 说明 | 特点 |
|------|------|------|
| `api` | 移动端 API 客户端 | 不限 IP 地区，兼容性好 |
| `html` | 网页端 HTML 客户端 | 效率高，但可能限制 IP 地区 |
| `async_api` | 异步移动端客户端 | 高性能异步版本 |

---

## 10. 项目运行方式

### 10.1 安装

```bash
# pip 安装（推荐）
pip install jmcomic -U

# 源码安装
pip install git+https://github.com/hect0x7/JMComic-Crawler-Python
```

### 10.2 Python API 使用

#### 最简方式

```python
import jmcomic

# 下载本子
jmcomic.download_album('123456')

# 下载章节
jmcomic.download_photo('789012')

# 批量下载
jmcomic.download_album(['123', '456', '789'])
```

#### 使用配置文件

```python
import jmcomic

option = jmcomic.create_option_by_file('option.yml')
jmcomic.download_album('123456', option)
```

#### 异步方式

```python
import asyncio
import jmcomic

asyncio.run(jmcomic.download_album_async('123456'))
```

#### 使用 Feature

```python
from jmcomic import download_album, Feature

# 下载并导出 PDF
download_album('123456', extra=Feature.export_pdf)

# 下载并导出 ZIP + 长图
download_album('123456', extra=Feature.export_zip + Feature.export_long_img)
```

### 10.3 命令行使用

#### jmcomic — 下载命令

```bash
# 下载本子
jmcomic 123456

# 下载多个本子
jmcomic 123 456 789

# 下载章节（p 前缀）
jmcomic p123456

# 同时下载本子和章节
jmcomic 123 p456

# 指定配置文件
jmcomic 123 --option="D:/option.yml"

# 通过环境变量指定配置文件
export JM_OPTION_PATH="D:/option.yml"
jmcomic 123
```

#### jmv — 查看命令

```bash
# 查看本子详情
jmv 350234

# 从混合文本中提取车号
jmv "350谁还没看过234"

# 直接退出不等待
jmv 350234 -y
```

### 10.4 GitHub Actions 使用

项目提供了 GitHub Actions 工作流配置，无需本地环境即可下载：

- [download.yml](file:///workspace/.github/workflows/download.yml)：下载工作流
- [export_favorites.yml](file:///workspace/.github/workflows/export_favorites.yml)：导出收藏夹
- [download_longimg.yml](file:///workspace/.github/workflows/download_longimg.yml)：长图下载

### 10.5 开发与测试

```bash
# 克隆项目
git clone <repo-url>
cd JMComic-Crawler-Python

# 安装开发依赖
pip install -r requirements-dev.txt

# 安装项目（可编辑模式）
pip install -e .

# 运行测试
python -m pytest tests/
```

---

## 11. 异常处理机制

### 11.1 异常类层次

```
JmcomicException (基类)
├── ResponseUnexpectedException    — 响应不符合预期
│   ├── JsonResolveFailException   — JSON 解析失败
│   └── MissingAlbumPhotoException — 本子/章节不存在
├── RegularNotMatchException       — 正则匹配失败
├── RequestRetryAllFailException   — 所有请求重试均失败
└── PartialDownloadFailedException — 部分下载失败
```

### 11.2 ExceptionTool 工具

**位置**：[jm_exception.py#L75-L236](file:///workspace/src/jmcomic/jm_exception.py#L75-L236)

提供统一的异常抛出方式，支持上下文传递：

| 方法 | 说明 |
|------|------|
| `raises(msg, context, etype)` | 抛出通用异常 |
| `raises_regex(msg, html, pattern)` | 抛出正则匹配异常 |
| `raises_resp(msg, resp, etype)` | 抛出响应相关异常 |
| `raise_missing(resp, jmid)` | 抛出资源不存在异常 |
| `require_true(case, msg)` | 断言式抛异常 |

### 11.3 异常监听器

通过 `JmModuleConfig.register_exception_listener(etype, listener)` 注册异常监听器，在异常抛出前触发回调。

### 11.4 下载异常处理

下载器会捕获下载过程中的异常并记录：
- `download_failed_image`：失败的图片列表 `[(image, exception), ...]`
- `download_failed_photo`：失败的章节列表 `[(photo, exception), ...]`
- `raise_if_has_exception()`：检查并抛出 `PartialDownloadFailedException`

---

## 12. 目录结构

```
/workspace/
├── .github/                    # GitHub 相关配置
│   ├── ISSUE_TEMPLATE/         # Issue 模板
│   ├── workflows/              # GitHub Actions 工作流
│   ├── CONTRIBUTING.md         # 贡献指南
│   └── release.py / release.yml # 发布脚本
├── assets/
│   ├── docs/                   # 项目文档（mkdocs）
│   │   └── sources/
│   │       ├── api/            # API 文档
│   │       ├── tutorial/       # 教程文档
│   │       └── images/         # 文档图片
│   ├── option/                 # 示例配置文件
│   └── readme/                 # 多语言 README
├── src/
│   └── jmcomic/                # 主模块
│       ├── __init__.py         # 模块入口，组件注册
│       ├── api.py              # 顶层 API
│       ├── cli.py              # 命令行入口
│       ├── cl.py               # （辅助模块）
│       ├── jm_config.py        # 全局配置
│       ├── jm_entity.py        # 数据实体
│       ├── jm_toolkit.py       # 工具集
│       ├── jm_exception.py     # 异常定义
│       ├── jm_client_interface.py  # 客户端接口
│       ├── jm_client_impl.py       # 客户端实现
│       ├── jm_async_client.py      # 异步客户端
│       ├── jm_option.py        # 配置管理
│       ├── jm_downloader.py    # 同步下载器
│       ├── jm_async_downloader.py  # 异步下载器
│       ├── jm_plugin.py        # 插件系统
│       └── jm_feature.py       # Feature 特性
├── tests/                      # 测试用例
│   └── test_jmcomic/
├── usage/                      # 使用示例
│   ├── demo_complete_pipeline.py
│   ├── workflow_download.py
│   ├── workflow_export_favorites.py
│   ├── workflow_longimg.py
│   └── benchmark_async_vs_sync.py
├── README.md                   # 项目说明
├── pyproject.toml              # 项目配置
├── setup.py                    # 安装脚本
├── requirements-dev.txt        # 开发依赖
├── LICENSE                     # 许可证
└── .gitignore
```

---

## 附录：核心调用链路

### 下载本子的完整调用链

```
download_album(album_id, option)
  │
  ├─ new_downloader(option) → JmDownloader
  │
  └─ downloader.download_album(album_id)
       │
       ├─ client = option.build_jm_client()
       │
       ├─ album = client.get_album_detail(album_id)
       │    └─ AbstractJmClient.request_with_retry()
       │         ├─ 域名选择
       │         ├─ HTTP 请求
       │         └─ 响应解析 → JmAlbumDetail
       │
       └─ downloader.download_by_album_detail(album)
            │
            ├─ before_album(album)
            │    ├─ 日志输出
            │    └─ 调用所有插件 before_album
            │
            ├─ 多线程下载每个章节
            │    └─ download_by_photo_detail(photo)
            │         ├─ client.check_photo(photo)
            │         ├─ before_photo(photo)
            │         ├─ 多线程下载每张图片
            │         │    └─ client.download_by_image_detail(image, path)
            │         │         ├─ get_jm_image(img_url) → JmImageResp
            │         │         └─ resp.transfer_to()  # 解密并保存
            │         └─ after_photo(photo)
            │
            └─ after_album(album)
                 ├─ 日志输出
                 ├─ 调用所有插件 after_album
                 └─ 调用匹配的 Features
```

---

*本文档基于 jmcomic v2.7.0 生成*
