#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  finnet.py
#  
#  Copyright 2018 Jose Carlos <jcr0ch4@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

######################################################################
# Configurar para enviar e-mail com uma lista dos arquivos baixados  #
# se possivel anexar os arquivos baixados no e-mail                  #
###################################################################### 

import os
import paramiko
from datetime import date
import smtplib
import sys
import commands
from email.MIMEText import MIMEText

paramiko.util.log_to_file('/opt/FINNET/log/finnet.log')

global sftp
global download_files

# Remoto FINNET
# Pasta de destino dos arquivos que a Wheaton deve efetuar o Download 
remote_in = "/entrada"

# Pasta de destino dos arquivos que a Wheaton envia para a FINNET processar
remote_out = "/saida"

# Local Wheaton
local_in = "/opt/FINNET/entrada"
local_out = "/opt/FINNET/saida"

# Enviado Wheaton 
local_send = "/opt/FINNET/enviado"

# Transferencia de arquivos para o spirit
transferencia="/documents/fin/finnet/retorno"
backup_folder="/opt/FINNET/backup"
# SFTP FINNET
host ="nome.dominio.com.br"
host_transferencia = "10.0.1.3"

def conecta():
    # Open a transport
    host ="nome.domino.com.br"
    port = 22
    transport = paramiko.Transport((host, port))

    # Auth
    password = "SENHA"
    username = "LOGIN"
    transport.connect(username = username, password = password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return sftp

def conecta_local():
    host_remoto = "10.0.1.3"
    porta_remota = 22
    transporta = paramiko.Transport((host_remoto,porta_remota))
    password_remoto = "SENHA"
    username_remoto = "LOGIN"
    transporta.connect(username = username_remoto, password = password_remoto)
    sftp_remoto = paramiko.SFTPClient.from_transport(transporta)
    return sftp_remoto

def get_files(pasta):
    arquivo_remoto = conecta().listdir(pasta)
    for i in arquivo_remoto:
        print("Download File : "+i)
        conecta().get(pasta+"/"+i,local_in+"/"+i)

def move_files(local,backup):
    try:
        for i in os.listdir(local):
            os.rename(local+"/"+i,backup+"/"+i)
            print("Move : "+local+"/"+i+" -> "+backup+"/"+i)
    except:
        print("Houve um erro ao mover os arquivos")


def transfer_files(remote_folder,local_folder):
    print("---------------------------------------")
    hoje = str(date.today())
    try:
        conecta_local().mkdir(remote_folder+"/"+hoje) 
        conecta_local().close()
    except:
        pass

    try:
        for i in os.listdir(local_folder):
            print("Upload : "+i+" -> "+host_transferencia+remote_folder+"/"+hoje)
            # Envia arquivos para o Spirit
            conecta_local().put(local_folder+"/"+i,remote_folder+"/"+hoje+"/"+i)
            # Configura a permissao no arquivo enviado
            conecta_local().chmod(remote_folder+"/"+hoje+"/"+i,0777)
    except :
        print("Houve um erro para enviar os arquivos para o host:"+host_transferencia)

  
def put_files(remote_folder,local_folder):
    print("---------------------------------------")
    for i in os.listdir(local_folder):
       print("Upload : "+i+" -> "+host+remote_folder)
       conecta().put(local_folder+"/"+i,remote_folder+"/"+i)


def list_remote_files(remote_folder):
    """
        Lista os arquivos remotos e cria um arquivo com esta lista
    """
    log_email=open('/tmp/log_email.txt','w')
    for i in conecta().listdir(remote_folder):
        log_email.write(i+"\n")


def remove_remote_files(caminho):
    """ 
       |  remove(self, path)
       |      Remove the file at the given path.  This only works on files; for
       |      removing folders (directories), use L{rmdir}.
       |      
       |      @param path: path (absolute or relative) of the file to remove
       |      @type path: str
       |      
       |      @raise IOError: if the path refers to a folder (directory)
    """
    # Gerar uma listagem dos arquivos e apagar cada arquivo da lista   
 
    # Apaga os arquivos do diretorio entrada    
    for i in conecta().listdir(caminho):
        conecta().remove(caminho+"/"+i)



def envmail(destinatario,titulo):
    arq_log = commands.getoutput('cat /tmp/log_email.txt')
    mensagem=" Prezados(as).\nSegue abaixo a listagem dos arquivos no SFTP da FINNET.\n =======================================================\n"+arq_log
    msg_conteudo=mensagem
    msg = MIMEText(msg_conteudo)
    msg['To'] = destinatario
    msg['Subject'] = titulo
    msg['From'] = "email.todos@meudominio.com.br"
    from_mail = "email.todos@meudominio.com.br"
    srv = smtplib.SMTP("endereco.smtp-dominio.com.br")
    srv.sendmail(from_mail,destinatario,msg.as_string())
    srv.close

def main(args):
    # Recebendo Arquivos
    get_files(remote_in)   	

    # Enviando Arquivos
    # put_files(remote_out,local_in)

    # Transfere os arquivos para o Spirit
    transfer_files(transferencia,local_in)

    # Movendo os arquivos para a pasta de Backup.
    try:
        move_files(local_in,backup_folder)
    except e:
        print("Erro:"+e+" \n Não foi possivel mover os arquivos.")

    # Gerando lista de arquivos
    list_remote_files(remote_in)
    # Enviando A lista de Arquivos do SFTP da FINNNET
    envmail('financeiro@meudominio.com.br','Arquivos Finnet')

    # Removendo Arquivos do SFTP FINNET
    remove_remote_files('/entrada')
    return 0

    
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
