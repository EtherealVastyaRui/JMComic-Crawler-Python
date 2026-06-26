# jmcomic Code Wiki

> **项目版本**: v2.7.0  
> **项目类型**: Python 库 / 爬虫框架  
> **核心功能**: 禁漫天堂（JMComic）的 Python API，支持本子下载、搜索、登录、收藏夹等功能

---

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [模块依赖关系](#3-模块依赖关系)
4. [核心模块详解](#4-核心模块详解)
5. [关键类与函数](#5-关键类与函数)
6. [实体类体系](#6-实体类体系)
7. [客户端体系](#7-客户端体系)
8. [下载器体系](#8-下载器体系)
9. [配置系统（Option）](#9-配置系统option)
10. [插件系统（Plugin）](#10-插件系统plugin)
11. [特性系统（Feature）](#11-特性系统feature)
12. [异常处理机制](#12-异常处理机制)
13. [命令行接口（CLI）](#13-命令行接口cli)
14. [异步编程支持](#14-异步编程支持)
15. [项目运行方式](#15-项目运行方式)
16. [测试体系](#16-测试体系)
17. [目录结构](#17-目录结构)

---

## 1. 项目概述

### 1.1 项目简介

jmcomic 是一个封装了禁漫天堂（JMComic / 18comic）网站 API 的 Python 库。它提供了完整的本子（Album）和章节（Photo）下载能力，支持网页端和移动端两种客户端实现，并集成了 GitHub Actions 自动化下载方案。

### 1.2 核心功能

- **本子下载**: 支持整本下载、单章节下载、批量下载
- **图片解码**: 实现禁漫图片分割算法的解密还原
- **搜索功能**: 支持站内搜索、作者搜索、标签搜索、角色搜索等
- **分类排行**: 支持分类浏览、月/周/日排行榜
- **用户系统**: 登录、收藏夹管理、评论
- **接口加解密**: 实现移动端 APP 接口的加解密算法
- **高可用**: 自动重试、域名切换、失败容错

### 1.3 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.9+ | 推荐 3.12+ |
| HTTP | curl_cffi | 绕过 Cloudflare 反爬 |
| 图像处理 | Pillow (PIL) | 图片解码与格式转换 |
| 加密 | pycryptodome | APP 接口加解密 |
| 配置 | PyYAML | YAML 配置文件支持 |
| 工具库 | commonx | 通用工具函数 |
| 异步 | asyncio | 异步 I/O 支持 |
| 测试 | unittest | 单元测试框架 |

---

## 2. 整体架构

### 2.1 架构分层

```
┌─────────────────────────────────────────────────┐
│                   外部 API 层                    │
│  api.py  -  download_album / download_photo     │
│  cli.py  -  命令行入口                           │
├─────────────────────────────────────────────────┤
│                  下载调度层                      │
│  jm_downloader.py    - 同步下载器                │
│  jm_async_downloader.py - 异步下载器             │
├─────────────────────────────────────────────────┤
│                   配置层                         │
│  jm_option.py   - 选项配置对象                   │
│  jm_plugin.py   - 插件系统                       │
│  jm_feature.py  - 特性封装                       │
├─────────────────────────────────────────────────┤
│                  客户端层                        │
│  jm_client_interface.py - 客户端接口定义         │
│  jm_client_impl.py      - 客户端抽象基类         │
│  jm_async_client.py     - 异步 API 客户端        │
├─────────────────────────────────────────────────┤
│                  工具层                          │
│  jm_toolkit.py  - 文本/加密/图片工具             │
│  jm_config.py   - 全局配置与常量                 │
│  jm_exception.py - 异常体系                      │
├─────────────────────────────────────────────────┤
│                  实体层                          │
│  jm_entity.py   - Album/Photo/Image 实体         │
└─────────────────────────────────────────────────┘
```

### 2.2 核心设计模式

1. **接口-实现分离**: 客户端通过接口抽象，支持网页端和移动端两种实现
2. **插件机制**: 通过插件扩展下载前后的行为
3. **特性（Feature）封装**: 将复杂插件使用封装为简洁的 Feature 调用
4. **同步+异步双 API**: 同步和异步两套 API 并行，方法签名对齐
5. **重试与容错**: 请求自动重试、域名自动切换、失败收集

---

## 3. 模块依赖关系

### 3.1 依赖层级

根据 [__init__.py](file:///workspace/src/jmcomic/__init__.py#L1-L4) 中的注释，模块依赖关系如下：

```
config <--- entity <--- toolkit <--- client <--- option <--- downloader
```

自底向上解释：
- **config**（[jm_config.py](file:///workspace/src/jmcomic/jm_config.py)）: 全局配置、常量、日志
- **entity**（[jm_entity.py](file:///workspace/src/jmcomic/jm_entity.py)）: 数据实体类
- **toolkit**（[jm_toolkit.py](file:///workspace/src/jmcomic/jm_toolkit.py)）: 工具函数（文本、加密、图片）
- **client**（[jm_client_interface.py](file:///workspace/src/jmcomic/jm_client_interface.py), [jm_client_impl.py](file:///workspace/src/jmcomic/jm_client_impl.py)）: API 客户端
- **option**（[jm_option.py](file:///workspace/src/jmcomic/jm_option.py)）: 配置选项
- **downloader**（[jm_downloader.py](file:///workspace/src/jmcomic/jm_downloader.py)）: 下载调度器

### 3.2 模块导入图

```
api.py
  └── jm_downloader.py
        └── jm_option.py
              └── jm_client_impl.py
                    └── jm_client_interface.py
                          └── jm_toolkit.py
                                └── jm_exception.py
                                      └── jm_entity.py
                                            └── jm_config.py

jm_plugin.py → jm_option.py
jm_feature.py → jm_plugin.py
cli.py → api.py
jm_async_client.py → jm_client_interface.py
jm_async_downloader.py → jm_downloader.py
```

---

## 4. 核心模块详解

### 4.1 api.py - 对外 API 入口

**文件**: [api.py](file:///workspace/src/jmcomic/api.py)

这是用户最常接触的模块，提供了简洁的高层 API。

#### 主要函数

| 函数 | 说明 |
|------|------|
| `download_album(jm_album_id, option, ...)` | 下载单个本子，支持批量（传入可迭代对象） |
| `download_photo(jm_photo_id, option, ...)` | 下载单个章节，支持批量 |
| `download_batch(download_api, jm_id_iter, ...)` | 批量下载底层实现 |
| `new_downloader(option, downloader)` | 创建下载器实例 |
| `create_option_by_file(filepath)` | 从文件创建配置对象 |
| `create_option_by_env(env_name)` | 从环境变量创建配置 |
| `create_option_by_str(text, mode)` | 从字符串创建配置 |
| `download_album_async(...)` | 异步版下载本子 |
| `download_photo_async(...)` | 异步版下载章节 |
| `download_batch_async(...)` | 异步版批量下载 |

#### 关键特性

- 支持单个 ID 和批量迭代（list/set/generator 等）自动识别
- 支持 `extra` 参数注入 Feature（如导出 PDF、ZIP）
- 支持 `callback` 回调函数获取下载结果
- 支持 `check_exception` 控制是否抛出部分下载失败异常

### 4.2 jm_config.py - 全局配置

**文件**: [jm_config.py](file:///workspace/src/jmcomic/jm_config.py)

#### JmMagicConstants 常量类

存放禁漫相关的常量定义：

| 常量组 | 说明 |
|--------|------|
| `ORDER_BY_*` | 排序方式（最新、观看、图片、点赞、评分、评论） |
| `TIME_*` | 时间范围（今日、本周、本月、全部） |
| `CATEGORY_*` | 分类（全部、同人、单本、短篇、其他、韩漫、美漫等） |
| `SUB_*` | 副分类（汉化、日语等） |
| `SCRAMBLE_*` | 图片分割算法版本号 |
| `APP_TOKEN_SECRET` 等 | APP 接口加密密钥 |

#### JmModuleConfig 模块配置类

模块级别的共用配置，包括：

- **域名配置**: API 域名、图片 CDN 域名、永久重定向地址
- **Headers 模板**: 网页端/移动端请求头
- **分页大小**: 搜索 80 条/页，收藏夹 20 条/页
- **类注册表**: 
  - `REGISTRY_CLIENT` - 同步客户端注册
  - `REGISTRY_ASYNC_CLIENT` - 异步客户端注册
  - `REGISTRY_PLUGIN` - 插件注册
  - `REGISTRY_EXCEPTION_LISTENER` - 异常监听器
- **字段自定义函数**: `AFIELD_ADVICE` / `PFIELD_ADVICE`（自定义 Album/Photo 字段）

### 4.3 jm_toolkit.py - 工具集

**文件**: [jm_toolkit.py](file:///workspace/src/jmcomic/jm_toolkit.py)

#### JmcomicText - 文本处理工具

核心功能：
- `parse_to_jm_id(text)`: 从任意文本解析禁漫车号
- `analyse_jm_album_html(html)`: 从 HTML 解析本子详情
- `analyse_jm_photo_html(html)`: 从 HTML 解析章节详情
- `reflect_new_instance(html, prefix, clazz)`: 反射式实体构建（正则 + 类属性映射）
- `parse_orig_album_name(title)`: 提取本子原始名称
- `to_zh(text, normalize)`: 繁简体转换

#### JmCryptoTool - 加密工具

- 移动端 APP 接口的请求/响应数据加解密
- 基于 `pycryptodome` 实现

#### JmImageTool - 图片处理工具

- `decode_and_save(scramble_id, image, path)`: 图片分割解密并保存
- `get_num_by_url(scramble_id, img_url)`: 根据 URL 计算图片序号
- `save_resp_img(resp, path, need_convert)`: 保存响应图片（支持格式转换）

---

## 5. 关键类与函数

### 5.1 顶层 API 函数

| 函数签名 | 所在文件 | 说明 |
|----------|----------|------|
| `download_album(jm_album_id, option=None, ...)` | [api.py:51](file:///workspace/src/jmcomic/api.py#L51-L84) | 下载本子 |
| `download_photo(jm_photo_id, option=None, ...)` | [api.py:87](file:///workspace/src/jmcomic/api.py#L87-L109) | 下载章节 |
| `create_option_by_file(filepath)` | [api.py:122](file:///workspace/src/jmcomic/api.py#L122-L123) | 从文件创建配置 |
| `new_downloader(option, downloader)` | [api.py:112](file:///workspace/src/jmcomic/api.py#L112-L119) | 创建下载器 |

### 5.2 JmOption 类核心方法

| 方法 | 说明 |
|------|------|
| `default()` | 创建默认配置 |
| `from_file(filepath)` | 从配置文件创建 |
| `construct(data)` | 从字典构造 |
| `new_client()` | 创建客户端实例 |
| `call_all_plugin(hook, **kwargs)` | 调用所有插件的指定钩子 |
| `invoke_plugin(pclass, kwargs, extra, pinfo)` | 调用单个插件 |
| `register_plugin(plugin_class)` | 注册插件类（类方法） |

### 5.3 JmDownloader 类核心方法

| 方法 | 说明 |
|------|------|
| `download_album(album_id)` | 下载整个本子 |
| `download_photo(photo_id)` | 下载单个章节 |
| `download_by_album_detail(album)` | 根据已获取的本子详情下载 |
| `download_by_photo_detail(photo)` | 根据已获取的章节详情下载 |
| `do_filter(detail)` | 过滤钩子，子类可重写 |
| `raise_if_has_exception()` | 如果有下载失败则抛出异常 |
| `add_features(features, feature_from)` | 注册 Feature |

---

## 6. 实体类体系

### 6.1 实体类继承关系

```
JmBaseEntity
  ├── DetailEntity ( + IndexedEntity)
  │     ├── JmAlbumDetail  - 本子详情
  │     └── JmPhotoDetail  - 章节详情
  ├── JmImageDetail ( + Downloadable)  - 图片详情
  ├── JmSearchPage      - 搜索结果页
  ├── JmCategoryPage    - 分类结果页
  └── JmFavoritePage    - 收藏夹页
```

### 6.2 JmAlbumDetail - 本子详情

**文件**: [jm_entity.py](file:///workspace/src/jmcomic/jm_entity.py)

| 属性 | 类型 | 说明 |
|------|------|------|
| `album_id` | str | 本子 ID |
| `name` | str | 标题 |
| `author` | str | 作者 |
| `tags` | List[str] | 标签列表 |
| `page_count` | int | 总页数 |
| `pub_date` | str | 发布日期 |
| `update_date` | str | 更新日期 |
| `likes` / `views` / `comment_count` | str | 点赞/观看/评论数 |
| `scramble_id` | str | 图片分割算法 ID |

| 属性/方法 | 说明 |
|-----------|------|
| `oname` | 提取原始名称（去掉汉化组等信息） |
| `authoroname` | `【作者】原始名称` 格式 |
| `idoname` | `[id] 原始名称` 格式 |
| `is_album()` | 判断是否为 Album 类 |
| `[index]` / `len()` | 按索引访问章节 / 章节数 |
| `__iter__` | 迭代章节 |

### 6.3 JmPhotoDetail - 章节详情

| 属性 | 类型 | 说明 |
|------|------|------|
| `photo_id` | str | 章节 ID |
| `name` | str | 章节名称 |
| `scramble_id` | str | 图片分割算法 ID |
| `series_id` | int | 所属本子 ID（单章为 0） |
| `sort` | int | 排序号 |
| `page_arr` | List[str] | 图片文件名数组 |
| `data_original_domain` | str | 图片 CDN 域名 |
| `from_album` | JmAlbumDetail | 所属本子引用 |

| 属性/方法 | 说明 |
|-----------|------|
| `album_id` | 所属本子 ID |
| `album_index` | 在本子中的序号（从 1 开始） |
| `is_single_album` | 是否为单章本子 |
| `indextitle` | `第N話 标题` 格式 |
| `create_image_detail(index)` | 创建指定索引的图片实体 |
| `is_photo()` | 判断是否为 Photo 类 |

### 6.4 JmImageDetail - 图片详情

| 属性 | 类型 | 说明 |
|------|------|------|
| `aid` | str | 所属章节 ID |
| `scramble_id` | str | 分割算法 ID |
| `img_url` | str | 图片 URL |
| `img_file_name` | str | 文件名（不含后缀） |
| `img_file_suffix` | str | 文件后缀 |
| `download_url` | str | 完整下载 URL（含 query 参数） |
| `from_photo` | JmPhotoDetail | 所属章节引用 |
| `index` | int | 图片序号（从 1 开始） |

| 属性/方法 | 说明 |
|-----------|------|
| `filename` | 完整文件名 |
| `is_gif` | 是否为 GIF（GIF 不需要解密） |
| `tag` | 日志用标签（`章节/文件名 [序号/总数]`） |
| `is_image()` | 判断是否为 Image 类 |
| `of(photo_id, scramble_id, data_original, ...)` | 工厂方法，从 URL 创建实例 |

---

## 7. 客户端体系

### 7.1 客户端接口分层

```
JmcomicClient (聚合接口)
  ├── JmImageClient        - 图片下载
  ├── JmDetailClient       - 本子/章节详情
  ├── JmUserClient         - 用户相关（登录、收藏、评论）
  ├── JmSearchAlbumClient  - 搜索
  └── JmCategoryClient     - 分类/排行
```

### 7.2 接口职责详解

#### JmDetailClient - 详情接口

**文件**: [jm_client_interface.py:158](file:///workspace/src/jmcomic/jm_client_interface.py#L158-L191)

| 方法 | 说明 |
|------|------|
| `get_album_detail(album_id)` | 获取本子详情 |
| `get_photo_detail(photo_id, fetch_album, fetch_scramble_id)` | 获取章节详情 |
| `check_photo(photo)` | 检查并补全 photo 的缺失信息 |

#### JmImageClient - 图片接口

**文件**: [jm_client_interface.py:249](file:///workspace/src/jmcomic/jm_client_interface.py#L249-L309)

| 方法 | 说明 |
|------|------|
| `download_image(img_url, img_save_path, scramble_id, decode_image)` | 下载并保存图片 |
| `download_by_image_detail(image, img_save_path, decode_image)` | 根据图片详情下载 |
| `get_jm_image(img_url)` | 获取图片响应（JmImageResp） |
| `download_album_cover(album_id, save_path, size)` | 下载本子封面 |

#### JmUserClient - 用户接口

**文件**: [jm_client_interface.py:193](file:///workspace/src/jmcomic/jm_client_interface.py#L193-L246)

| 方法 | 说明 |
|------|------|
| `login(username, password)` | 登录 |
| `album_comment(video_id, comment, ...)` | 发表评论/回复 |
| `favorite_folder(page, order_by, folder_id, username)` | 获取收藏夹 |
| `add_favorite_album(album_id, folder_id)` | 添加收藏 |

#### JmSearchAlbumClient - 搜索接口

**文件**: [jm_client_interface.py:312](file:///workspace/src/jmcomic/jm_client_interface.py#L312-L408)

| 方法 | 说明 |
|------|------|
| `search(search_query, page, main_tag, order_by, time, category, sub_category)` | 通用搜索 |
| `search_site(...)` | 站内搜索（main_tag=0） |
| `search_work(...)` | 作品搜索（main_tag=1） |
| `search_author(...)` | 作者搜索（main_tag=2） |
| `search_tag(...)` | 标签搜索（main_tag=3） |
| `search_actor(...)` | 角色搜索（main_tag=4） |
| `search_gen(...)` | 搜索生成器（支持 send 动态改参数） |

#### JmCategoryClient - 分类接口

**文件**: [jm_client_interface.py:411](file:///workspace/src/jmcomic/jm_client_interface.py#L411-L475)

| 方法 | 说明 |
|------|------|
| `categories_filter(page, time, category, order_by, sub_category)` | 分类筛选 |
| `month_ranking(page, category)` | 月排行 |
| `week_ranking(page, category)` | 周排行 |
| `day_ranking(page, category)` | 日排行 |

### 7.3 AbstractJmClient - 抽象基类

**文件**: [jm_client_impl.py](file:///workspace/src/jmcomic/jm_client_impl.py)

实现了通用能力：
- **域名管理**: `domain_list` 配置，自动切换
- **重试机制**: `request_with_retry()` 支持重试和域名切换
- **缓存机制**: `enable_cache()` 为指定方法加上结果缓存
- **请求封装**: `get()` / `post()` 统一走重试逻辑

### 7.4 响应类体系

```
JmResp - HTTP 响应基类
  ├── JmImageResp    - 图片响应（含图片解密保存）
  ├── JmJsonResp     - JSON 响应
  │     ├── JmApiResp - API 响应（含数据解密）
  │     └── JmAlbumCommentResp - 评论响应
```

---

## 8. 下载器体系

### 8.1 下载器类结构

```
DownloadCallback - 回调基类（日志输出）
  └── BaseDownloader - 公共基类（回调、插件、Feature）
        ├── JmDownloader (同步) - 多线程下载调度
        └── JmAsyncDownloader (异步) - asyncio 异步下载调度
```

### 8.2 下载回调钩子

下载流程中的回调钩子（同时触发插件和 Feature）：

| 钩子 | 触发时机 |
|------|----------|
| `before_album(album)` | 本子下载前 |
| `after_album(album)` | 本子下载后 |
| `before_photo(photo)` | 章节下载前 |
| `after_photo(photo)` | 章节下载后 |
| `before_image(image, img_save_path)` | 图片下载前 |
| `after_image(image, img_save_path)` | 图片下载后 |

### 8.3 同步下载器 JmDownloader

**文件**: [jm_downloader.py](file:///workspace/src/jmcomic/jm_downloader.py)

核心特性：
- 基于多线程的并发下载
- 图片级和章节级并发控制
- 失败图片/章节收集（`download_failed_image`, `download_failed_photo`）
- 成功记录字典（`download_success_dict`）
- `all_success` 属性判断是否全部下载成功

### 8.4 异步下载器 JmAsyncDownloader

**文件**: [jm_async_downloader.py](file:///workspace/src/jmcomic/jm_async_downloader.py)

核心特性：
- 基于 `asyncio.Semaphore` 的并发控制
- 下载 IO 与 CPU 解密流水线化
- `ThreadPoolExecutor` 处理图片解密（CPU 密集型）
- 继承 `BaseDownloader` 复用回调和插件体系
- 支持异步上下文管理器（`async with`）

---

## 9. 配置系统（Option）

### 9.1 JmOption 配置对象

**文件**: [jm_option.py](file:///workspace/src/jmcomic/jm_option.py)

配置项结构：

```
JmOption
  ├── dir_rule: DirRule       - 下载路径规则
  ├── download: AdvancedDict  - 下载配置（并发数、图片后缀等）
  ├── client: AdvancedDict    - 客户端配置（域名、重试、实现类等）
  └── plugins: AdvancedDict   - 插件配置
```

### 9.2 DirRule - 路径规则 DSL

支持通过 DSL 配置下载目录结构：

| 规则前缀 | 含义 | 示例 |
|----------|------|------|
| `Bd` | 基础目录（Base dir） | `Bd` |
| `Axxx` | Album 字段 | `Aid`, `Atitle`, `Aauthor` |
| `Pxxx` | Photo 字段 | `Pid`, `Ptitle` |
| `{xxx}` | F-string 格式 | `[JM{Aid}]{Atitle}` |

默认规则：`Bd/Atitle` → `基础目录/本子标题/`

### 9.3 主要配置项

#### download 配置

```yaml
download:
  image:
    suffix: .png          # 图片格式转换
  threading:
    image: 30             # 图片并发数
    photo: 3              # 章节并发数
  decode_image: true      # 是否解密图片
  cache: true             # 是否使用磁盘缓存
```

#### client 配置

```yaml
client:
  impl: api               # 客户端实现: api (移动端) / html (网页端)
  retry_times: 5          # 重试次数
  domain:                 # 域名配置
    api:
      - domain1.com
      - domain2.com
  proxies: {}             # 代理配置
  cookies: {}             # Cookies 配置
```

---

## 10. 插件系统（Plugin）

### 10.1 插件基类 JmOptionPlugin

**文件**: [jm_plugin.py](file:///workspace/src/jmcomic/jm_plugin.py)

| 属性/方法 | 说明 |
|-----------|------|
| `plugin_key` | 插件标识（类属性） |
| `option` | 所属 JmOption 对象 |
| `invoke(**kwargs)` | 插件执行入口，子类实现 |
| `build(option)` | 工厂方法，创建插件实例 |
| `log(msg, topic)` | 插件日志 |
| `require_param(case, msg)` | 参数校验 |
| `execute_deletion(paths)` | 执行文件删除（受 delete_original_file 控制） |

### 10.2 插件生命周期

插件通过钩子（hook）机制在下载流程中被调用：

```
下载流程: before_album → before_photo → before_image 
          → after_image → after_photo → after_album
                ↓            ↓            ↓
          调用所有插件的对应钩子方法
```

### 10.3 内置插件

根据 [README.md](file:///workspace/README.md#L243-L246)，核心内置插件包括：

| 插件 | 功能 |
|------|------|
| `login` | 登录插件 |
| 只下载新章插件 | 增量下载 |
| 导出收藏夹 CSV | 收藏夹导出 |
| `img2pdf` | 合并为 PDF |
| `long_img` | 合并为长图 |
| `zip` | 压缩为 ZIP |
| 自动获取浏览器 cookies | Cookie 获取 |
| 订阅更新插件 | 更新订阅 |

---

## 11. 特性系统（Feature）

### 11.1 Feature 设计思想

**文件**: [jm_feature.py](file:///workspace/src/jmcomic/jm_feature.py)

Feature 是对插件的高级封装，解决用户需要知道插件名、调用时机、参数配置的问题。

使用对比：
```python
# 传统插件方式（需配置 option，调用时机自行把握）
option = create_option_by_file('option.yml')  # 里面配置了 img2pdf 插件
download_album(id, option)

# Feature 方式（一行代码搞定）
download_album(id, extra=Feature.export_pdf)
```

### 11.2 Feature 类层次

```
Feature - 特性基类
  └── PluginFeature - 插件特性（封装插件调用）

FeatureChain - 多个 Feature 的组合
```

### 11.3 使用方式

```python
from jmcomic import download_album, Feature

# 单个 Feature
download_album(id, extra=Feature.export_pdf)

# 带参数
download_album(id, extra=Feature.export_pdf(pdf_dir='./output'))

# 多个 Feature
download_album(id, extra=[Feature.export_pdf, Feature.export_zip])
download_album(id, extra=Feature.export_pdf + Feature.export_zip)
```

### 11.4 内置 Feature

| Feature | 对应插件 | 触发时机 |
|---------|----------|----------|
| `Feature.export_pdf` | `img2pdf` | `after_album` / `after_photo` |
| `Feature.export_zip` | `zip` | `after_album` / `after_photo` |
| `Feature.export_long_img` | `long_img` | `after_album` / `after_photo` |

---

## 12. 异常处理机制

### 12.1 异常类体系

**文件**: [jm_exception.py](file:///workspace/src/jmcomic/jm_exception.py)

```
JmcomicException - 基类
  ├── ResponseUnexpectedException - 响应不符合预期
  │     ├── JsonResolveFailException - JSON 解析失败
  │     └── MissingAlbumPhotoException - 本子/章节不存在
  ├── RegularNotMatchException - 正则不匹配
  ├── RequestRetryAllFailException - 请求全部重试失败
  └── PartialDownloadFailedException - 部分下载失败
```

### 12.2 ExceptionTool - 异常工具

| 方法 | 说明 |
|------|------|
| `raises(msg, context, etype)` | 抛出异常 |
| `raises_regex(msg, html, pattern)` | 抛出正则不匹配异常 |
| `raises_resp(msg, resp, etype)` | 抛出响应异常 |
| `raise_missing(resp, jmid)` | 抛出资源不存在异常 |
| `require_true(case, msg)` | 断言式抛出 |
| `notify_all_listeners(e)` | 通知所有异常监听器 |

### 12.3 异常监听器机制

通过 `JmModuleConfig.REGISTRY_EXCEPTION_LISTENER` 注册异常监听器，实现自定义异常处理。

---

## 13. 命令行接口（CLI）

### 13.1 jmcomic - 下载命令

**文件**: [cli.py](file:///workspace/src/jmcomic/cli.py)

**入口函数**: `main()` → [cli.py:125](file:///workspace/src/jmcomic/cli.py#L125-L126)

**用法**:
```bash
# 下载本子
jmcomic 123

# 下载多个本子
jmcomic 123 456 789

# 下载章节（p 前缀）
jmcomic p321

# 同时下载本子和章节
jmcomic 123 p456

# 指定配置文件
jmcomic 123 --option="D:/option.yml"
```

**环境变量**:
- `JM_OPTION_PATH`: option 文件路径

### 13.2 jmv - 查看命令

**入口函数**: `view_main()`

**用法**:
```bash
# 查看本子详情
jmv 350234

# 从混合文本中提取数字
jmv 350谁还没看过234

# 指定配置
jmv 350234 --option="D:/a.yml"

# 执行完毕自动退出
jmv 350234 -y
```

输出包含：标题、ID、链接、作者、发布/更新日期、页数、观看/点赞/评论数、标签、人物、作品、章节列表。

---

## 14. 异步编程支持

### 14.1 异步客户端 AsyncJmApiClient

**文件**: [jm_async_client.py](file:///workspace/src/jmcomic/jm_async_client.py)

- 基于 `curl_cffi.requests.AsyncSession` 实现
- 移动端 API 的异步访问
- 支持异步上下文管理器（`async with`）
- 方法签名与同步版对齐

### 14.2 异步下载器 JmAsyncDownloader

**文件**: [jm_async_downloader.py](file:///workspace/src/jmcomic/jm_async_downloader.py)

核心设计：
- **IO 异步化**: 图片下载使用 asyncio 异步 I/O
- **CPU 卸载**: 图片解密（PIL 操作）放到 ThreadPoolExecutor
- **流水线**: 下载与解密并行，提升吞吐量
- **信号量控制**: `asyncio.Semaphore` 控制并发数

### 14.3 异步 API 使用示例

```python
import asyncio
import jmcomic

async def main():
    # 下载单个本子
    album, downloader = await jmcomic.download_album_async('123')
    
    # 批量下载
    results = await jmcomic.download_album_async(['123', '456', '789'])

asyncio.run(main())
```

---

## 15. 项目运行方式

### 15.1 环境要求

- Python >= 3.9（推荐 3.12+）
- pip 包管理器

### 15.2 安装方式

```bash
# 方式一：pip 安装（推荐）
pip install jmcomic -U

# 方式二：源码安装
pip install git+https://github.com/hect0x7/JMComic-Crawler-Python
```

### 15.3 快速上手

#### Python API 方式

```python
import jmcomic

# 最简单的下载
jmcomic.download_album('123')

# 使用配置文件
option = jmcomic.create_option_by_file('option.yml')
jmcomic.download_album('123', option)
```

#### 命令行方式

```bash
jmcomic 123
```

#### GitHub Actions 方式

参考 [1_github_actions.md](file:///workspace/assets/docs/sources/tutorial/1_github_actions.md) 教程。

### 15.4 配置文件示例

创建 `option.yml`：

```yaml
download:
  image:
    suffix: .png
  threading:
    image: 30
    photo: 3

client:
  impl: api
  retry_times: 5

plugins:
  login:
    username: your_username
    password: your_password
```

### 15.5 运行测试

```bash
# 运行全部测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_jmcomic/test_jm_api.py
```

---

## 16. 测试体系

### 16.1 测试文件结构

**目录**: [tests/test_jmcomic](file:///workspace/tests/test_jmcomic)

| 测试文件 | 测试内容 |
|----------|----------|
| [test_jm_api.py](file:///workspace/tests/test_jmcomic/test_jm_api.py) | 顶层 API 测试 |
| [test_jm_client.py](file:///workspace/tests/test_jmcomic/test_jm_client.py) | 客户端测试 |
| [test_jm_plugin.py](file:///workspace/tests/test_jmcomic/test_jm_plugin.py) | 插件测试 |
| [test_jm_feature.py](file:///workspace/tests/test_jmcomic/test_jm_feature.py) | Feature 测试 |
| [test_jm_custom.py](file:///workspace/tests/test_jmcomic/test_jm_custom.py) | 自定义扩展测试 |
| [test_jm_cli.py](file:///workspace/tests/test_jmcomic/test_jm_cli.py) | CLI 测试 |
| [test_jm_async_api.py](file:///workspace/tests/test_jmcomic/test_jm_async_api.py) | 异步 API 测试 |
| [test_jm_async_client.py](file:///workspace/tests/test_jmcomic/test_jm_async_client.py) | 异步客户端测试 |
| [test_jm_async_plugin.py](file:///workspace/tests/test_jmcomic/test_jm_async_plugin.py) | 异步插件测试 |
| [test_jm_async_feature.py](file:///workspace/tests/test_jmcomic/test_jm_async_feature.py) | 异步 Feature 测试 |
| [test_jm_async_custom.py](file:///workspace/tests/test_jmcomic/test_jm_async_custom.py) | 异步自定义测试 |

### 16.2 测试框架

- 使用 `unittest` 测试框架
- 测试基类 `JmTestConfigurable` 提供公共配置和客户端

### 16.3 示例代码

**目录**: [usage](file:///workspace/usage)

| 文件 | 说明 |
|------|------|
| [workflow_download.py](file:///workspace/usage/workflow_download.py) | 下载工作流示例 |
| [workflow_export_favorites.py](file:///workspace/usage/workflow_export_favorites.py) | 收藏夹导出示例 |
| [benchmark_async_vs_sync.py](file:///workspace/usage/benchmark_async_vs_sync.py) | 异步 vs 同步性能基准测试 |

---

## 17. 目录结构

```
/workspace/
├── .github/                    # GitHub 相关
│   ├── ISSUE_TEMPLATE/         # Issue 模板
│   ├── workflows/              # GitHub Actions 工作流
│   ├── CONTRIBUTING.md         # 贡献指南
│   ├── release.py              # 发布脚本
│   └── release.yml             # 发布配置
├── assets/                     # 资源文件
│   ├── docs/                   # 文档（mkdocs）
│   │   └── sources/
│   │       ├── api/            # API 文档
│   │       ├── tutorial/       # 教程文档
│   │       ├── images/         # 文档图片
│   │       └── index.md        # 文档首页
│   ├── option/                 # 示例配置文件
│   └── readme/                 # 多语言 README
├── src/
│   └── jmcomic/                # 核心源码
│       ├── __init__.py         # 模块初始化，组件注册
│       ├── api.py              # 对外 API
│       ├── cli.py              # 命令行入口
│       ├── cl.py               # 查看命令
│       ├── jm_config.py        # 全局配置与常量
│       ├── jm_entity.py        # 实体类
│       ├── jm_exception.py     # 异常体系
│       ├── jm_toolkit.py       # 工具集
│       ├── jm_client_interface.py  # 客户端接口
│       ├── jm_client_impl.py       # 客户端实现基类
│       ├── jm_async_client.py      # 异步客户端
│       ├── jm_option.py        # 配置选项
│       ├── jm_plugin.py        # 插件系统
│       ├── jm_feature.py       # Feature 系统
│       ├── jm_downloader.py    # 同步下载器
│       └── jm_async_downloader.py  # 异步下载器
├── tests/
│   └── test_jmcomic/           # 测试代码
├── usage/                      # 使用示例
├── README.md                   # 项目说明
├── pyproject.toml              # 项目配置
├── setup.py                    # 安装脚本
├── requirements-dev.txt        # 开发依赖
├── LICENSE                     # 许可证
└── .gitignore                  # Git 忽略
```

---

## 附录：扩展开发指南

### 自定义插件

```python
from jmcomic import JmOptionPlugin

class MyPlugin(JmOptionPlugin):
    plugin_key = 'my_plugin'
    
    def invoke(self, **kwargs):
        # 插件逻辑
        pass

# 注册插件
JmModuleConfig.register_plugin(MyPlugin)
```

### 自定义客户端

```python
from jmcomic import JmcomicClient

class MyClient(JmcomicClient):
    client_key = 'my_client'
    
    def get_album_detail(self, album_id):
        # 实现
        pass

# 注册客户端
JmModuleConfig.register_client(MyClient)
```

### 自定义下载器

```python
from jmcomic import JmDownloader

class MyDownloader(JmDownloader):
    def do_filter(self, detail):
        # 自定义过滤逻辑
        return detail
```

---

*本文档基于 jmcomic v2.7.0 生成*
