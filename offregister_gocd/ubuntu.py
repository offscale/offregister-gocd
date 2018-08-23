from cStringIO import StringIO

from fabric.contrib.files import exists, append
from fabric.operations import sudo, put
from nginx_parse_emit import emit, utils
from nginxparser import dumps, loads
from offregister_certificate.ubuntu import self_signed0
from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.ubuntu.systemd import restart_systemd
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
    nginx.setup_nginx_init1()

    if kwargs.get('self_signed'):
        self_signed0(use_sudo=True, **kwargs)

    server_block = utils.merge_into(
        (lambda server_block: utils.apply_attributes(server_block,
                                                     emit.secure_attr(kwargs['SSL_CERTOUT'],
                                                                      kwargs['SSL_KEYOUT'])
                                                     ) if kwargs['LISTEN_PORT'] == 443 else server_block)(
            emit.server_block(server_name=kwargs['SERVER_NAME'],
                              listen=kwargs['LISTEN_PORT'])
        ),
        emit.api_proxy_block('/go', 'https://localhost:8154')
    )

    sio = StringIO()
    sio.write(dumps(
        loads(emit.redirect_block(server_name=kwargs['SERVER_NAME'], port=80)) + server_block
        if kwargs['LISTEN_PORT'] == 443 else server_block
    ))

    put(sio,
        '/etc/nginx/sites-enabled/{server_name}'.format(server_name=kwargs['SERVER_NAME']),
        use_sudo=True, )

    return restart_systemd('nginx')
