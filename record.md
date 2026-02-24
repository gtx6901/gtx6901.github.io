# RakuHan`s Heya 搭建记录

## 一、在做什么？

> 一个静态网站工程项目  

本质：

```
Markdown 内容
        ↓
Hexo 渲染
        ↓
生成 HTML 文件
        ↓
浏览器访问
```

使用Hexo, 将`/posts /notes /photography /projects /about`等渲染为完整网站  

## 二、准备开发环境

### 安装Node.js

用 NodeSource 安装最新版 LTS：

``` Bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

### 安装 Hexo CLI

``` Bash
sudo npm install -g hexo-cli
hexo -v
```

## 三、创建与自定义HP

### 初始化工程

```bash
hexo init
npm install
```

现在的目录大概如下所示，这是完整工程的骨架:

```Bash
.
├── _config.landscape.yml
├── _config.yml
├── node_modules
├── package.json
├── package-lock.json
├── scaffolds
├── source
└── themes
```

### 启动本地服务器

```Bash
hexo server
```

然后在浏览器中打开:

```URL
http://localhost:4000
```

如果看到默认博客页面，则搭建成功

### 更换主题

本Site使用Shoka主题，在site文件夹下执行：

```Bash
git clone https://github.com/amehime/hexo-theme-shoka.git themes/shoka
```

随后，在`_config.yaml`中找到`theme`一栏，改成`shoka`，然后重新生成：

```Bash
hexo clean
hexo generate
hexo server
```

### 建立版块结构

在`source`文件夹下新建对应的文件夹即可

### 创建示例文章

```Bash
cd ..
hexo new page about
hexo new page photography
hexo new "第一篇日常"
```

### 自定义图片

在使用 Hexo + Shoka 主题时，图片有多种来源：主题自带图片、站点静态图片、以及文章/页面的封面。推荐使用不会修改主题源码的覆盖方法。

1. 覆盖主题自带图片（推荐）

- 原理：Shoka 主题在 `themes/shoka/source/images/` 和 `themes/shoka/_images.yml` 中包含默认图片。不要直接修改主题目录（会在主题更新时丢失）。推荐在站点源码下放置同名文件以覆盖主题默认图片。
- 操作：在项目的 `site/` 子目录下创建覆盖目录并放入同名图片：

- 说明：构建/部署时，生成脚本会优先使用 `site/source/_data/images/` 中的文件，从而在不改主题的前提下替换图片。

2. 为文章或页面设置封面/图片

- 推荐把文章用到的图片放在 `site/source/images/`：

- 在 Markdown 的 front-matter 中添加 `cover:`（Shoka 示例中使用 `cover` 字段）：

- 在正文中也可以直接用 Markdown 引用：

```markdown
![示例图片](/images/inline-image.jpg)
```

3. 全局首页或索引封面（主题配置覆盖）


- 有些封面由主题配置读取（比如 `index.cover`）。优先在站点根目录的 `site/_config.yml` 中设置：
        `cover: /images/index-cover.jpg`


- 也可以在 `site/source/_data/images/` 放对应图片来覆盖主题默认资源。

4. 生成、预览与清理缓存

- 常用命令（在 `site/` 目录下执行）：

```
# 本地预览（开发用）
npx hexo server
```

5. 注意事项

- 不要直接编辑 `site/public/`：这是 Hexo 的输出目录，会被生成命令覆盖。
- 对于小幅替换，优先使用 `site/source/_data/images/` 覆盖主题图片；如果要深度自定义并长期维护，考虑 fork 主题并修改 `themes/shoka/`。

### 自定义首页风格

推荐使用 `site/_config.shoka.yml` 来安全地覆盖主题配置（主题更新不会覆盖）。

**修改首页背景图**

1. 准备背景图片放到 `site/source/images/`：

   ```bash
   site/source/images/my-bg.jpg
   ```

2. 在 `site/_config.shoka.yml` 底部添加：

   ```yaml
   index:
     cover: /images/my-bg.jpg
   ```

   或使用渐变色：

   ```yaml
   index:
     cover: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
   ```

3. 重新生成：

   ```bash
   cd site
   npx hexo clean && npx hexo generate
   npx hexo server
   ```

**常用配置示例**

在 `site/_config.shoka.yml` 中修改以下项：

```yaml
# 菜单
menu:
  home: / || home
  about: /about/ || user

# 侧边栏头像
sidebar:
  avatar: avatar.jpg

# 部件开关
widgets:
  random_posts: true
  recent_comments: false

# 页脚配置
footer:
  since: 2010
  icon:
    color: "#ffc0cb"
```

修改后运行 `npx hexo clean && npx hexo generate` 生效。
