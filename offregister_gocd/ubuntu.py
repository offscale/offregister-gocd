from fabric.contrib.files import exists, append
from fabric.operations import sudo

from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_nginx import ubuntu as nginx


def install_deps0(*args, **kwargs):
    if not cmd_avail('javac'):
        sudo('add-apt-repository -y ppa:webupd8team/java')
        sudo('echo debconf shared/accepted-oracle-license-v1-1 select true | \
      sudo debconf-set-selections')
        apt_depends('oracle-java8-set-default')

    srcs_list = '/etc/apt/sources.list.d/gocd.list'
    if not exists(srcs_list):
        append(srcs_list, 'deb https://download.gocd.org /', use_sudo=True)
        sudo('curl https://download.gocd.org/GOCD-GPG-KEY.asc | sudo apt-key add -')


def install_master1(*args, **kwargs):
    apt_depends('go-server')


def install_slave2(*args, **kwargs):
    apt_depends('go-agent')


def configure_nginx3(*args, **kwargs):
    nginx.install_nginx0()
