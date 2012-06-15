自动发布工具
============

Features:
------------ 
 * 项目版本发布, 支持svn/git
 * 服务器信息管理

How To Use: 
------------
 * show all tasks it support

`$ fab --list`

 * query host/ip information and save to db

`$ fab -H host1,host2,... hostinfo`

 * the "proj" task: this task is responsible for loading project environment variables into myenv, the most important var is myenv.hosts, so you can use the following command to query hostinfo of all servers related to the "dummy" project

`$ fab proj:dummy hostinfo`

 * setup some project named "dummy-project"

`$ fab proj:dummy setup`

or you can combine setup and deploy together

`$ fab proj:dummy setup:v1.0`

 * deploy

`$ fab proj:dummy deploy:v1.1`

 * ideploy: only deploy the difference

`$ fab proj:dummy ideploy:v1.2`

 * check version/revision consistency

`$ fab proj:dummy check`


Required:
------------
* Python 2.6+
* Django 1.3.1+
* Fabric 1.3.3+

Platforms it had been tested on: 
------------
* FreeBSD8.2
* FreeBSD9.0