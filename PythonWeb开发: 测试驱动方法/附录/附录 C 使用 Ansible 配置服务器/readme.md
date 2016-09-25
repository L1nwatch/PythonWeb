## 附录 C 使用 Ansible 配置服务器

用 Fabric 自动把新版代码部署到服务器上，但配置新服务器的过程以及更新 Nginx 和 Gunicron 配置文件的操作，都还是手动完成。

这类操作越来越多地交给 “配置管理” 或 “持续部署” 工具完成。其中，Chef 和 Puppet 最受欢迎，而在 Python 领域则是 Salt 和 Ansible。

在这些工具中，Ansible 最容易上手，只需两个文件就可以使用：

`pip install ansible # 可能只能用 Python 2`

清单文件 `deploy_tools/inventory.ansible` 定义可以在哪些服务器中运行：

```python
# deploy_tools/inventory.ansible
[live]
watch0.top

[staging]
watch0-staging.top

[local]
localhost ansible_ssh_port=6666 ansible_host=127.0.0.1
```

### C.1 安装系统包和 Nginx

另一个文件是“脚本”（playbook），定义在服务器中做什么。这个文件的内容使用 YAML 句法编写：

```yaml
# deploy_tools/provision.ansible.yaml
---

- hosts: all
  sudo: yes
  vars: host:$inventory_hostname
  tasks:
  	- name: make sure required packages are installed
      apt: pkg=nginx, git, python3, python3-pip, state=present
    - name: make sure virtual is installed
      shell: pip3 install virtualenv
      
    - name: allow long hostnames in nginx
      lineinfile:
        dest=/etc/nginx/nginx.conf
        regexp='(\s+)#? ?server_names_hash_bucket_size'
        backrefs=yes
        line='\1server_names_hash_bucket_size 64;'
        
    - name: add nginx config to sites-available
      template: src=./nginx.conf.j2
                dest=/etc/nginx/sites-available/{{ host }}
                
      notify:
      	- restart nginx
    
    - name: add symlink in nginx sites-enabled
      file: src=/etc/nginx/sites-available/{{ host }}
            dest=/etc/nginx/sites-enabled/{{ host }} state=link
      notify:
		- restart nginx
```

为了方便，在 "vars" 部分定义了一个变量 "host"。这个变量可以在不同的文件名中使用，也可以传给配置文件。变量的值是 `$inventory_hostname`，即当前所在服务器的域名。

在 "tasks" 部分，使用 apt 安装所需的软件，再使用正则表达式替换 Nginx 配置，允许使用长域名，然后使用模板创建 Nginx 配置文件。这个模板是由 `deploy_tools/nginx.template.conf` 中的模板文件修改而来，不过现在指定使用一种模板引擎——Jinja2，和 Django 的模板句法很像：

```jinja2
deploy_tools/nginx.conf.j2

server {
  listen 80;
  server_name {{ host }};
  
  location /static {
    alias /home/harry/sites/{{ host }}/static;
  }
  
  location / {
    proxy_set_header Host $host;
    proxy_pass http://unix:/tmp/{{ host }}.socket;
  }
}
```

### C.2 配置 Gunicron，使用处理程序重启服务

脚本剩余的内容如下：

```yaml
# deploy_tools/provision.ansible.yaml
- name: write gunicron init script
  template: src=./gunicron-upstart.conf.j2
  			dest=/etc/init/gunicorn-{{ host }}.conf
  notify:
  	- restart gunicorn
  
  - name: make sure nginx is running
    service: name=nginx state=running
  - name: make sure gunicorn is running
  	service: name=gunicorn-{{ host }} state=running
  	
handlers:
	- name: restart nginx
	  service: name=nginx state=restarted
	
	- name: restart gunicorn
	  service: name=gunicorn-{{ host }} state=restarted
```

创建 Gunicorn 配置文件还要使用模板：

```jinja2
# deploy_tools/gunicorn.upstart.conf.j2
description "Gunicorn server for {{ host }}"

start on net-device-up
stop on shutdown

respawn

chdir /home/harry/sites/{{ host }}/source
exec ../virtualenv/bin/gunicorn --bind unix:/tmp/{{ host }}.socket --access-logfile ../access.log --error-logfile ../error.log superlists.wsgi:application
```

然后定义两个处理程序，重启 Nginx 和 Gunicorn。Ansible 很智能，如果多个步骤都调用同一个处理程序，它会等前一个执行完再调用下一个。

这样就行了！执行配置操作的命令如下：

`ansible-playbook -i ansible.inventory provision.ansible.yaml --limit=staging`。

### C.3 接下来做什么

#### C.3.1 把 Fabric 执行的部署操作交给 Ansible

可以看到 Ansible 可以帮助完成配置过程中的某些操作，其实它可以完成几乎所有部署操作。

#### C.3.2 使用 Vagrant 搭建本地虚拟主机

在过渡网站中运行测试能让我们相信网站上线后也能正常运行。不过也可以在本地设备中使用虚拟主机完成这项操作。

下载 Vagrant 和 Virtualbox，看你能否使用 Vagrant 在自己的电脑中搭建一个开发服务器，以及使用 Ansible 脚本把代码部署到这个服务器中。设置功能测试运行程序，让功能测试能在本地虚拟主机中运行。

编写一个 Vagrant 配置脚本特别有用，因为它能帮助新加入的开发者搭建和你们使用一模一样的服务器。