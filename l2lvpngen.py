#!/usr/bin/env python3
# Import OS module to do things like execute commands directly to OS
import os
# Load built-in or APT installed modules
import socket
import sys
import os
import getpass
import pip
import paramiko
# Load netmiko module, to do the magic happens
import netmiko
from netmiko import ConnectHandler

print("L2L configuration generator")
print(" ")
print("Checking if we need install any modules before run. Please wait...")
print(" ")


# Install core modules to run
print("We will need install some python packages/modules, if this is your "
      "first run")
print('ensure your internet connection is working and be patient...')
# Install packages via APT
print('Veryifing module install via APT')
os.system("/usr/bin/apt-get install -y python3 python3-pip python3-paramiko")


# Confirm if we have all python3 modules needed to run this
# If modules are not found, install them via pip
pkgs = ['pprint', 'pyyaml', 'pyserial', 'textfsm', 'netmiko']
for package in pkgs:
    try:
        import package
    except ImportError:
        pip.main(['install', package])


os.system("clear")
print("Welcome to Tabajara L2L configuration generator")
print(" ")
# Just a greeting to user
print("Now we are (hopefuly) with all set to start ")


# Reads the user input to determine which type of configuration we need
# If the ASA is 8.2 or earlier we use isakmp crypto, otherwise we user ike
print(" ")
print("For which version os IOS we are building this config?")
print("The ASA its running 8.2 or earlier?")
print(" ")
asaversion = input("Please enter 8.2 to any version below 8.3 or 8.3 for any"
                   " other version: ")
# Ask the user for SSH port, is none is informed, use the default (22)
print(" ")
remoteport = int(input("Please inform the SSH port to connect to ASA. Just "
                       "press enter if using the default port (22): ") or 22)

# Different actions for different versions
if asaversion == '8.2':
    print(" ")
    print("ASA version 8.2 or earlier, generating configuration in ISAKMP mode")
    print("-------------------------------------------------------------------")
    hostname = input("Please inform the IP or hostname to connect: ")
    ssh_username = input("Please inform the username to be used to connect "
            "(make sure the user has privilege 15): ")
    ssh_password = getpass.getpass("Please inform the password to be used"
            " to connect: ")
    enable_secret = getpass.getpass("ASA in version 8.2 and below uses enable"
            " secret, please inform them now: ")
    print("-------------------------------------------------------------"
            "-----------")
elif asaversion == '8.3':
    print(" ")
    print("ASA version 8.3 or superior, generating configuration in IKE mode")
    print("-----------------------------------------------------------------")
    hostname = input("Please inform the IP or hostname to connect: ")
    ssh_username = input("Please inform the username to be used to connect"
            " (make sure the user has privilege 15): ")
    ssh_password = getpass.getpass("Please inform the password to be used to"
            " connect and enable: ")
    # We dont really need this here, but netmiko refuses to work if dont get 
    # enable superpowers, so, lets use the same variable for enable_secret
    enable_secret = ssh_password
    print("------------------------------------------------------------")
else:
    print(" ")
    print("Invalid input, program will exit now")
    sys.exit()

# Lets confirm the port is opened before do anything further
def isOpen(ip,port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Verifying if host is listening on remote port '
                + str(remoteport) + ' ...')
        s.connect((ip, port))
        s.shutdown(2)
        print(" ")
        print('Host is listening on remote port ' + str(remoteport) + 
                '... proceeding')
        print(" ")
    except socket.error:
        print(" ")
        print('Host its not listening on indicated remote port ' 
                + str(remoteport) + ', program will exit now')
        sys.exit()

# Execute the function to check if host is listening on indicated port
isOpen(hostname,remoteport)

# Lets define a ASA here, to be used be netmiko after
asa_firewall = {
    'device_type': 'cisco_asa',
    'ip':   hostname,
    'username': ssh_username,
    'password': ssh_password,
    'port' : remoteport,    
    'secret': enable_secret,
    'verbose': False,       # optional, defaults to False
}

# Connect to ASA using SSH, and stores the version of the box to be compared 
# We need this to ensure we will not break anything to user
def check_asaversion(): 
    client = ConnectHandler(**asa_firewall)
    # Stores entire 'show version' output into variable showversion
    showversion = client.send_command('show version')
    # Split the showversion variable to get only the major version/release
    showversion_split = str(showversion.split('\n')[1].split(' ')[-2].split('(')[0])
    return showversion_split

# Lets put the ASA version here to compare in next section
version_running = check_asaversion()

# Compare the user input with the version we got from device
if version_running <= '8.2':
    if version_running <= '8.2':
        print(" ")
        print("You informed version " + asaversion + " when program started...") 
        print("Informed version " + asaversion + " and device version " 
                + version_running + " are compatible, proceeding...")
    else:
        print("You informed version " + asaversion + " when program started...") 
        print("Informed version " + asaversion + " and device version "
                + version_running + " are not compatible to configure")
        print("Please check your input and try again")
        print("Exiting now...")
        sys.exit()
elif version_running >= '8.3':
    if version_running >= '8.3':
        print("You informed version " + asaversion + " when program started...") 
        print("Informed version " + asaversion + " and device version " 
                + version_running + " are compatible, proceeding...")
    else:
        print("You informed version " + asaversion + " when program started...") 
        print("Informed version " + asaversion + " and device version " 
                + version_running + " are not compatible to configure")
        print("Please check your input and try again")
        print("Exiting now...")
        sys.exit()

# Lets start to collect information from the user, to build the configuration
# to be applied into ASA further
company01 = input("Enter abbreviated name of the company of this firewall: ")
company02 = input("Enter abbreviated name of partner company where the "
        "connection will be made: ")
print("object-group network " + company01 + "-" + company02, 
        file=open("/tmp/temp_network-companies.txt", "w"))
print("description Hosts/Networks to protect in " + company01 + " side",
        file=open("/tmp/temp_network-companies.txt", "a")) 
print(" ")
print("Please inform the hosts/networks to be added to VPN in " + company01)
print("side, to specify hosts enter 255.255.255.255 as mask")
print(" ")
print("example: 192.168.1.234 255.255.255.255 for a host or")
print("example: 192.168.1.0 255.255.255.0 for the entire")
print("192.168.1 network")
print(" ")
print("Press Ctrl-D to save it.")
protect_company01 = []
while True:
    try:
        line = input()
        linecomplete = "network-object {}".format(line)
        protect_company01.append(linecomplete)
    except EOFError:
        break

arquivo = open('/tmp/temp_network-companies.txt', 'a')
for item in protect_company01:
    arquivo.write("%s\n" % item)

print("object-group network " + company02 + "-" + company01, 
        file=open("/tmp/temp_network-companies.txt", "a"))
print("description Hosts/Networks to protect in " + company02 + " side", 
        file=open("/tmp/temp_network-companies.txt", "a")) 
print(" ")
print("Please inform the hosts/networks to be added to VPN in " + company02)
print("side, to specify hosts enter 255.255.255.255 as mask")
print(" ")
print("example: 192.168.1.234 255.255.255.255 for a host or")
print("example: 192.168.1.0 255.255.255.0 for the entire")
print("192.168.1 network")
print(" ")
print("Press Ctrl-D to save it.")
protect_company02 = []
while True:
    try:
        line = input()
        linecomplete = "network-object {}".format(line)
        protect_company02.append(linecomplete)
    except EOFError:
        break

arquivo = open('/tmp/temp_network-companies.txt', 'a')
for item in protect_company02:
    arquivo.write("%s\n" % item)

# Lets build the default ACLs
print("access-list " + company01 + "-" + company02 + "extended permit ip "
      "any object-group " + company01 + "-" + company02, 
      file=open("/tmp/temp_network-companies.txt", "a")) 

print("access-list " + company01 + "-" + company02 + "extended permit ip "
      "object-group " + company01 + "-" + company02 + "any", 
      file=open("/tmp/temp_network-companies.txt", "a")) 

print("access-list " + company01 + "-" + company02 + "extended permit ip any4"
      " object-group " + company01 + "-" + company02, 
      file=open("/tmp/temp_network-companies.txt", "a")) 

print("access-list " + company01 + "-" + company02 + "extended permit ip"
      " object-group " + company01 + "-" + company02 + "any4",
      file=open("/tmp/temp_network-companies.txt", "a")) 

access-list B2BSSIT-RABK extended permit ip any4 object-group B2BSSIT-RABK 
access-list B2BSSIT-RABK extended permit ip object-group B2BSSIT-RABK any4 

# Define default variables for security association parameters
lifetime_seconds = 28800
lifetime_kilobytes = 4608000

# Define dictionaries to read actual configuration and determine the 
# index of the new configuration
#crypto_map_properties = { 'index': ' ', 'parameter': ' ',
#'property': ' ', 'value': '' }
#crypto_policy = { 'index': ' ', 'authentication': ' ', 'encryption': ' ',
#'hash': ' ', 'group': ' ', 'lifetime': '' } 
#group_policy = { 'name': ' ', 'protocol': ' ', 'peer_ip': '' }
#tunnel_group = { 'peer_ip': ' ', 'group_policy': ' ', 'psk': '' } 

# Start to fill the new configuration
#def cypto-policy-conf { 
#	print 'crypto isakmp policy crypto_policy.index()',
