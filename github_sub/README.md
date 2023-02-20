# github订阅(真寻适配版)

用来推送github用户动态或仓库动态

### 使用

添加github ['用户'/'仓库'] [用户名/{owner/repo}]
删除github [用户名/{owner/repo}]
查看github
示例：添加github订阅用户 HibiKier
示例：添加gb订阅仓库 HibiKier/zhenxun_bot
示例：添加github用户 yajiwa
示例：删除gb订阅 yajiwa

## 更新

**2022/5/22**

1. 适配真寻最新版

**2022/5/11**[v0.4]

1. 修改删除逻辑

**2022/4/10**[v0.3]

1. 新增推送release
2. 添加设置GITHUB_ISSUE，是否不推送Issue，默认为是

**2022/4/9**[v0.2]

1. 数据库新增etag字段，更新后不设置github token也可推送
2. 之前已部署0.1版本需对真寻发送```exec ALTER TABLE "github_sub" ADD COLUMN "etag" varchar;```

**2022/4/8**[v0.1]

1. 基于真寻beta2开发

