from sys import version

if version[0] == "2":
    from cStringIO import StringIO

else:
    from io import StringIO

from fabric.contrib.files import append, exists
from nginx_parse_emit import emit, utils
from nginxparser import dumps, loads
from offregister_certificate.ubuntu import self_signed0
from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.ubuntu.systemd import restart_systemd
from offregister_nginx import ubuntu as nginx


def install_deps0(c, *args, **kwargs):
    if not cmd_avail(c, "javac"):
        c.sudo("add-apt-repository -y ppa:webupd8team/java")
        c.sudo(
            "echo debconf shared/accepted-oracle-license-v1-1 select true | \
      sudo debconf-set-selections"
        )
        apt_depends(c, "oracle-java8-set-default")

    srcs_list = "/etc/apt/sources.list.d/gocd.list"
    if not exists(c, runner=c.run, path=srcs_list):
        append(srcs_list, "deb https://download.gocd.org /", use_sudo=True)
        c.sudo("curl https://download.gocd.org/GOCD-GPG-KEY.asc | sudo apt-key add -")


def install_master1(c, *args, **kwargs):
    apt_depends(c, "go-server")


def install_slave2(c, *args, **kwargs):
    apt_depends(c, "go-agent")


def configure_nginx3(c, *args, **kwargs):
    nginx.install_nginx0()
    nginx.setup_nginx_init1()

    if kwargs.get("self_signed"):
        self_signed0(use_sudo=True, **kwargs)

    server_block = utils.merge_into(
        (
            lambda server_block: utils.apply_attributes(
                server_block,
                emit.secure_attr(kwargs["SSL_CERTOUT"], kwargs["SSL_KEYOUT"]),
            )
            if kwargs["LISTEN_PORT"] == 443
            else server_block
        )(
            emit.server_block(
                server_name=kwargs["SERVER_NAME"], listen=kwargs["LISTEN_PORT"]
            )
        ),
        emit.api_proxy_block("/go", "https://localhost:8154"),
    )

    sio = StringIO()
    sio.write(
        dumps(
            loads(emit.redirect_block(server_name=kwargs["SERVER_NAME"], port=80))
            + server_block
            if kwargs["LISTEN_PORT"] == 443
            else server_block
        )
    )

    c.put(
        sio,
        "/etc/nginx/sites-enabled/{server_name}".format(
            server_name=kwargs["SERVER_NAME"]
        ),
        use_sudo=True,
    )

    return restart_systemd("nginx")
