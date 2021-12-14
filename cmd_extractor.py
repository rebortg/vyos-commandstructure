from paramiko import SFTPClient, Transport
from collections import OrderedDict
from stat import S_ISDIR, S_ISREG
import json
import logging
import argparse

logger = logging.getLogger('cmd_extractor')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


cfgpath = '/opt/vyatta/share/vyatta-cfg/templates'
oppath = '/opt/vyatta/share/vyatta-op/templates'


def main():

    parser = argparse.ArgumentParser(description='VyOS Command extractor')
    parser.add_argument('-s','--host', help='IP/Hostname of a VyOS Host', required=True)
    parser.add_argument('-u','--user', help='VyOS Username', default="vyos")
    parser.add_argument('-p','--pass', help='VyOS Password', default="vyos")
    args = vars(parser.parse_args())

    vyos_ip = args['host']
    vyos_user = args['user']
    vyos_password = args['pass']

    opcmd = []
    cfgcmd = []

    t = Transport((vyos_ip, 22))
    t.connect(username=vyos_user, password=vyos_password)
    f = SFTPClient.from_transport(t)
    logger.info(f'listdir: {cfgcmd}')
    files = listdir(f, cfgpath)
    for file in files:
        logger.info(f'parse: {file}')
        cfgcmd.append(parse_file(f, file))
    
    logger.info(f'listdir: {oppath}')
    files = listdir(f, oppath)
    for file in files:
        logger.info(f'parse: {file}')
        opcmd.append(parse_file(f, file))
    
    logger.info(f'write output/cfgcmd.txt')
    f = open('output/cfgcmd.txt', 'w')
    for cmd in cfgcmd:
        render_cmd(cmd, f)    
    f.close()

    logger.info(f'write output/opcmd.txt')
    f = open('output/opcmd.txt', 'w')
    for cmd in opcmd:
        render_cmd(cmd, f)    
    f.close()


def listdir(sftp, remotedir, ignore_dir=""):
    absolutefilenames = []
    for entry in sftp.listdir_attr(remotedir):
        absolutepath = f"{remotedir}/{entry.filename}"
        # test if entry is dir or file
        if S_ISDIR(entry.st_mode):
            absolutefilenames.extend(listdir(sftp, absolutepath))
        if S_ISREG(entry.st_mode):
            logger.info(f'got file: {absolutepath}')

            absolutefilenames.append(absolutepath)
    return absolutefilenames


def render_cmd(cmd, f):
    f.write(f' '.join(cmd['cmd']))
    f.write(f'\n')
    f.write(f'    type:     {cmd["type"]}\n')
    f.write(f'    run:      {cmd["run"]}\n')
    f.write(f'    val_help: {cmd["val_help"]}\n')
    f.write(f'    help:     {cmd["help"]}\n\n')


def parse_file(sftp, filepath):
    run = None
    help = None
    cmd = None
    val_help = None
    type = None

    with sftp.open(filepath, "r") as f:
        # get command from path
        filepath = filepath.replace('node.tag', '<text>')
        filepath = filepath.replace('node.def', '<value>')
        cmd = filepath.split("/")[6:]
        for line in f.readlines():
            if "help: " in line:
                help = line[6:].rstrip()
            if "run:" in line:
                run = line[5:].rstrip()
            if "type:" in line:
                type = line[6:].rstrip()
            if "val_help:" in line:
                val_help = line[10:].rstrip()
        
        # without type the command is a leaf node
        if not type:
            cmd = cmd[:-1]
    
    return {"cmd": cmd, "run": run, "help": help, "type": type, "val_help": val_help}





if __name__ == "__main__":
    main()