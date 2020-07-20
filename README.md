## HotEvents
#### 说明 
该项目是热点事件分析展示平台，针对目前的冠状肺炎进行疫情预测分析和数据展示。未来可根据实时热点事件增加新的分许和预测功能。
#### 环境配置及启动
1. python版本 
- `python3.6`
2. 安装依赖  
```shell script
pip install -r requirements.txt
``` 
3. 启动  
- 开发环境(端口8080):
```
sh dev.sh 或者 export FLASK_CONFIG=development & python manage.py runserver
```
- 生产环境(端口19542):
```
sh pro.sh 或者 export FLASK_CONFIG=production & python manage.py run
```
*也可用docker建立docker镜像开启容器启动*
#### 启动、查看、开启、停止、重载任务命令
- 线上环境部署在`192.168.6.199`机器上的`/home/innov/`目录里, 登录线上服务器
- 服务名是`Hotevents`
```shell script
cd supervisor
# 启动supervisor，没有意外这个一直都是启动状态
supervisord -c supervisor.conf         
# 查看Hotevents服务状态   
supervisorctl -c supervisor.conf status 
# 启动服务 
supervisorctl -c supervisor.conf start Hotevents
# 关闭服务 
supervisorctl -c /home/supervisor.conf stop Hotevents  
# 若更新supervisor配置，执行此命令进行更新
supervisorctl -c /home/supervisor.conf update  
```
#### API文档
查看api文档详情，请点击[api文档](/docs/api.md)