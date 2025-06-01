# 介绍
使用uv管理python版本和包的类qinglong定时运行面板，目前仅支持运行python代码。
代码需要写成python-script格式或者uv工程（使用uv init初始化）。

# 已支持功能

从url下载文件或者git项目

支持使用cron表达式定时运行文件或者git项目

支持手动更新文件和git项目

长时间任务守护运行！

# 待开发功能

命令传参

查询运行日志

自动更新文件和git项目（定时更新，或者支持webhook更新）

支持api 自动重定向

web面板 使用nicegui实现

通知

# 问题
能否统一通知？有一个库叫什么来着
https://github.com/caronc/apprise

私人模块或者项目如何处理？

多个项目之间如何互相调用？

是否能支持级联触发器？

！！需要一个外部库（sdk），用来统一通知，多项目级联触发，还有传参
