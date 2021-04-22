#!/usr/bin/env python3

#IPK projekt 1
#Adriana Jurkechová, xjurke02@fit.stud.vutbr.cz
#2020/2021


import sys, getopt, os, re, socket

def arguments(argv):
   nameserver = ''
   surl = ''
   try:
      opts, args = getopt.getopt(argv,"hn:f:",["servername=","url="])
   except getopt.GetoptError:
      print ("fileget.py -n NAMESERVER -f SURL")
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print ("fileget.py -n NAMESERVER -f SURL")
         sys.exit()
      elif opt in ("-n", "--servername"):
         nameserver = arg
      elif opt in ("-f", "--url"):
         surl = arg
   return nameserver, surl


def NSP(domenove_jmeno, ipcka, port):
   MESSAGE = "WHEREIS " + domenove_jmeno

   sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

   while True:

      sock.sendto(MESSAGE.encode('utf-8'), (ipcka, int(port)))
      data, address = sock.recvfrom(4096)
      if data.decode('utf-8') == "ERR Not Found":
         print("Súborový server nebol nájdený\n", file=sys.stderr)
         sys.exit(2)
      elif data.decode('utf-8') == "ERR Syntax":
         print("Chybná syntax požiadavky alebo mena suborového serveru\n", file=sys.stderr)
         sys.exit(2)
      elif "OK" in data.decode('utf-8'):
         break
   
   sock.close()
   response = data.decode('utf-8').split(':')
   if not response[1].isnumeric():
      print("Chybná odpoved menneho serveru\n", file=sys.stderr)
      sys.exit(2)
   return response[1]

    
def FSP(domenove_jmeno, nazev_suboru, ipcka, port):
   MESSAGE = "GET " + nazev_suboru + " FSP/1.0\r\nHostname: " + domenove_jmeno + "\r\nAgent: xjurke02\r\n\r\n"

   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.settimeout(30)
   s.connect((ipcka, int(port)))
   s.send(MESSAGE.encode('utf-8'))
   data = s.recv(100000)
   if data.decode('utf-8') == "FSP/1.0 Bad Request":
      print("Chybná syntax požiadavky.\n", file=sys.stderr)
      sys.exit(2)
   elif data.decode('utf-8') == "FSP/1.0 Not Found":
      print("Nepodarilo sa nájsť", nazev_suboru, ".\n", file=sys.stderr)
   elif data.decode('utf-8') == "FSP/1.0 Server Error":
      print("Niečo sa stalo so serverom.\n", file=sys.stderr)
      sys.exit(2) 
   f= open(nazev_suboru,"wb+")
   data = s.recv(100000)
   f.write(data)
   while True:
      data = s.recv(100000)
      f.write(data)
      if not data: break

   s.close()
   f.close()


def GET(splitted_surl, ipcka, new_port):
   #GET ALL
   if "*" == splitted_surl[3]:
      FSP(splitted_surl[2], "index", ipcka, new_port)
      f=open("index", "r")
      if f.mode == 'r':
         #citanie indexu riadok po riadku
         while line := f.readlines():
            for x in range(len(line)):
               line[x]=line[x].rstrip("\n")
               path = line[x]
               #pripad s viacerymi podadresarmi
               if "/" in line [x]:
                  dirs = []
                  parts = line[x].split('/')
                  for x in range(0, len(parts)-1):
                     dirs.append(parts[x])
                  dirs = '/'.join(dirs)
                  if not os.path.isdir(dirs):
                     os.makedirs(dirs)
                  FSP(splitted_surl[2], path, ipcka, new_port)
               else:
                  FSP(splitted_surl[2], line[x], ipcka, new_port)
   #GET
   else:
      FSP(splitted_surl[2], splitted_surl[3], ipcka, new_port)



nameserver, surl = arguments(sys.argv[1:])

#oddelenie ip a portu
splitted_nameserver = nameserver.split(':')
ipcka = splitted_nameserver[0]
port = splitted_nameserver[1] 

#oddelenie surl podla /
splitted_surl = surl.split('/')

#osetrenie nazvu servera
if splitted_surl[0] != "fsp:":
   print("Prosím zadaj fsp protokol.\n", file=sys.stderr)
   sys.exit(2)

#kontrola nazvu menneho suboru
if not bool(re.match('[\w._-]+$', splitted_surl[2], re.IGNORECASE)):
   print("Menny server sa sklada z nepovolenych znakov.\n", file=sys.stderr)
   sys.exit(2)

#spojenie nazvu
if len(splitted_surl) > 4:
   path = []
   dirs = []
   #vytvorenie adresarovej struktury
   for x in range(3, len(splitted_surl)-1):
      dirs.append(splitted_surl[x])
   dirs = '/'.join(dirs)
   if not os.path.isdir(dirs):
      os.makedirs(dirs)
   #spojenie predtym rozdeleneho nazvu do jedneho stringu
   for x in range(3, len(splitted_surl)):
      path.append(splitted_surl[x])
   path = '/'.join(path)
   splitted_surl[3] = path

new_port = NSP(splitted_surl[2], ipcka, port)

GET(splitted_surl, ipcka, new_port)


sys.exit(0)