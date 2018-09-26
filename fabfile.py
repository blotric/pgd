from __future__ import with_statement
from fabric.api import *
from fabric.colors import *
from fabric.utils import puts

import os
import requests
import json

base_path = os.path.abspath(os.path.dirname(__file__))

POLLVORTEX_HOST = '192.165.67.201:22'
PRODUCTION_HOST = '159.69.83.198:22'

env.forward_agent = True
env.user = 'ubuntu'
env.key_filename = os.path.join(base_path, 'keys/pgd_rsa')


@task
def staging():
    env.host_string = POLLVORTEX_HOST
    env.branch = 'dev'
    env.build_command = 'build_staging'
    env.django_settings = 'cargoxapi.settings.dev'
    env.nginx_config = 'pgdstaging'
    env.uwsgi_config = 'pgdstaging.ini'
    env.supervisor_config = 'pgdstaging.conf'
    env.rabbitmq_vhost = 'pgdstaging'

@task
def production():
    env.host_string = PRODUCTION_HOST
    env.branch = 'master'
    env.build_command = 'build'
    env.django_settings = 'pgd.settings.production'
    env.nginx_config = 'pgd'
    env.uwsgi_config = 'pgd.ini'
    env.supervisor_config = 'pgd.conf'
    env.rabbitmq_vhost = 'pgd'


@task
def install_rabbitmq():
    try:
        sudo('apt-get install -y rabbitmq-server')
        sudo('rabbitmqctl delete_vhost /')
        sudo('rabbitmqctl delete_user guest')
        sudo('rabbitmqctl add_user pgd lordofallfiremen!')
        sudo('rabbitmqctl add_vhost ' + env.rabbitmq_vhost)
        sudo('rabbitmqctl set_permissions -p ' + env.rabbitmq_vhost + ' pgd ".*" ".*" ".*"')
    except:
        pass


@task
def setup_repo(use_host_repo=False):
    try:
        with settings(warn_only=True):
            with settings(hide('stdout')):
                run('ssh -o StrictHostKeyChecking=no git@github.com')
        run("git clone git@github.com:blotric/pgd /home/ubuntu/pgd")
    except:
        pass
    with cd('/home/ubuntu/pgd/'):
        puts(magenta("[Pulling changes]"))
        run('git fetch')
        run('git checkout '+env.branch)
        run('git pull origin '+env.branch)


@task
def install_dependencies():
    puts(green('[Updating]'))
    sudo('apt update')
    puts(yellow('[Installing dependencies]'))
    sudo('apt install -y nginx python3-pip python-pip build-essential python3-dev git memcached libssl-dev '
         'openssl build-essential python3-dev shared-mime-info')


@task
def install_virtualenv():
    sudo('pip install virtualenvwrapper')
    with prefix('source /usr/local/bin/virtualenvwrapper.sh'):
        run('mkvirtualenv -p python3 pgd')
    with(prefix('source /home/ubuntu/.virtualenvs/pgd/bin/activate')):
        with cd('/home/ubuntu/pgd'):
            run('pip install --upgrade pip')
            run('pip install -r requirements.txt')


@task
def install_uwsgi():
    try:
        with(prefix('source /home/ubuntu/.virtualenvs/pgd/bin/activate')):
            run('pip install uwsgi')
        sudo('mkdir -p /etc/uwsgi/sites')
        sudo('chown ubuntu:root /etc/uwsgi/sites')
        sudo('ln -s /home/ubuntu/pgd/conf/uwsgi/' + env.uwsgi_config + ' /etc/uwsgi/sites')
        put('./conf/uwsgi.service', '/etc/systemd/system', use_sudo=True)
        sudo('systemctl enable uwsgi.service')
        sudo('service uwsgi start')
    except:
        pass


@task
def setup_nginx():
    try:
        sudo('ln -s /home/ubuntu/pgd/conf/nginx/' + env.nginx_config + ' /etc/nginx/sites-enabled')
        # sudo('ln -s /home/ubuntu/pgd/conf/nginx/htpasswd /etc/nginx')
        sudo('service nginx reload')
    except:
        pass


@task
def setup_supervisor():
    try:
        sudo('apt-get install -y supervisor')
        sudo('ln -s /home/ubuntu/cargox-dapp/conf/supervisor/' + env.supervisor_config + ' /etc/supervisor/conf.d')
        sudo('supervisorctl reload')
        sudo('supervisorctl reread')
        sudo('supervisorctl update')
    except:
        pass


@task
def setup_postgres_dependencies():
    sudo('apt install -y libpq-dev postgresql-client')


@task
def setup_fstab():
    # This mounts the data volume.
    try:
        sudo('echo "/dev/xvdf	/mnt/data	ext4	defaults,nofail	0 0" >> /etc/fstab')
        sudo('mkdir /mnt/data')
        sudo('chown ubuntu:ubuntu /mnt/data')
        sudo('mount -a')
    except:
        pass


@task
def provision():
    install_dependencies()
    setup_fstab()
    setup_repo()
    install_virtualenv()
    install_uwsgi()
    install_rabbitmq()
    setup_postgres_dependencies()
    setup_supervisor()
    setup_nginx()
    deploy()


@task
def pull():
    with cd('/home/ubuntu/pgd/'):
        puts(magenta("[Pulling changes]"))
        run('git fetch')
        run('git checkout '+env.branch)
        run('git pull origin '+env.branch)


@task
def management_command(command):
    with cd('/home/ubuntu/pgd/'):
        with prefix('source /home/ubuntu/.virtualenvs/pgd/bin/activate'):
            with shell_env(DJANGO_SETTINGS_MODULE=env.django_settings):
                with cd('/home/ubuntu/pgd/'):
                    puts(magenta("[Running command]"))
                    run('python manage.py ' + command)


@task
def deploy():
    with cd('/home/ubuntu/pgd/'):
        puts(magenta("[Pulling changes]"))
        run('git fetch')
        run('git checkout '+env.branch)
        run('git pull origin '+env.branch)

        with prefix('source /home/ubuntu/.virtualenvs/pgd/bin/activate'):
            with shell_env(DJANGO_SETTINGS_MODULE=env.django_settings):
                with cd('/home/ubuntu/pgd'):
                    puts(magenta("[Installing packages]"))
                    run('pip install -r requirements.txt')

                with cd('/home/ubuntu/pgd/'):
                    puts(magenta("[Migrating apps]"))
                    run('python manage.py migrate')

                    # puts(magenta("[Compiling translation messages]"))
                    # run('python manage.py compilemessages')

                    puts(magenta("[Collecting static files]"))
                    run('python manage.py collectstatic --noinput')

                    puts(magenta("[Touching uwsgi ini file]"))
                    run('touch /home/ubuntu/pgd/conf/uwsgi/' + env.uwsgi_config)

                    puts(magenta("[Touching uwsgi ini file]"))
                    if env.branch == 'dev':
                        run('touch /etc/uwsgi/sites_python3/' + env.uwsgi_config)
                    else:
                        run('touch /etc/uwsgi/sites/' + env.uwsgi_config)

                    puts(magenta("[Reloading nginx]"))
                    sudo('service nginx reload')

    # puts(magenta("[Reloading supervisor]"))
    # sudo('supervisorctl reread')
    # sudo('supervisorctl update')
	#
    # puts(magenta("[Restarting worker supervisor]"))
    # sudo('supervisorctl restart dappworker')
    # sudo('supervisorctl restart dappbeat')
