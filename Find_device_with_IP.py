#Import modules needed and set up ssh connection parameters
import paramiko
import datetime
import getpass
import os
import time

port = 22
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


#Define variables
time_now  = datetime.datetime.now().strftime('%m_%d_%Y_%H_%M_%S')
switchLocation = input('Which site are these switches located? (ex. USEP)')
switchLocation = switchLocation.upper()
searchTerm = 'Internet'
global_var_macadd = "blank"

#Text formatting defenitions. These are used to make the console text a different color.
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prRed(skk): print("\033[91m {}\033[00m" .format(skk))

def switchConnect():
    
    prGreen('Please enter the credentials for the switch: \n')
    userName = input('Username: ')
    userPass = getpass.getpass()
    ipaddr = input('What is the IP of the core switch? ')
    clientIP = input('What is the IP of the device that you are looking for? ')
    showARP = 'sh ip arp ' + clientIP

    try:
        ssh.connect(hostname=ipaddr, username=userName, password=userPass, port=port)
        _stdin, _stdout, _stderr = ssh.exec_command(showARP)
        list = _stdout.readlines()
        searchList = [list.index(i) for i in list if searchTerm in i]
    
    except paramiko.ssh_exception.AuthenticationException:
        prRed('Failed to connect to switch. Check credentials.\n')
        switchConnect()

    try:
        #split list at line containing "hostname" to get hostname.
        indexValue = searchList[0]
        splitList = list[indexValue]
        macAdd = splitList.rsplit(' ',6)[1].rstrip()
        prGreen ('The MAC address found for this IP is: ' + macAdd)
        addTable = 'sh mac address-table address ' + macAdd
   

        #Find the connecting port
        ssh.connect(hostname=ipaddr, username=userName, password=userPass, port=port)
        _stdin, _stdout, _stderr = ssh.exec_command(addTable)
        list = _stdout.readlines()
        searchList = [list.index(i) for i in list if macAdd in i]

        #split list at line containing "hostname" to get hostname.
        indexValue = searchList[0]
        splitList = list[indexValue]
        switchPort = splitList.rsplit(' ',2)[2].rstrip()
        prGreen ('The switch port is connected to: ' + switchPort + '\n\n')

        ssh.close

    except IndexError:
        prRed('No IP was found.\n\n')

    
    global global_var_macadd 
    global_var_macadd = macAdd


    menu()
    


def nextSwitch():
    
    prGreen('Please enter the credentials for the switch: \n')
    userName = input('Username: ')
    userPass = getpass.getpass()
    ipaddr = input('What is the IP of the current switch? ')
    clientIP = input('What is the IP of the device that you are looking for? ')
    
    try:
     
        addTable = 'sh mac address-table address ' + global_var_macadd
   

        #Find the connecting port
        ssh.connect(hostname=ipaddr, username=userName, password=userPass, port=port)
        _stdin, _stdout, _stderr = ssh.exec_command(addTable)
        list = _stdout.readlines()
        searchList = [list.index(i) for i in list if global_var_macadd in i]

        #split list at line containing "hostname" to get hostname.
        indexValue = searchList[0]
        splitList = list[indexValue]
        switchPort = splitList.rsplit(' ',2)[2].rstrip()
        prGreen ('The switch port is connected to: ' + switchPort + '\n\n')


    except paramiko.ssh_exception.AuthenticationException:
        prRed('Failed to connect to switch. Check credentials.\n')
        switchConnect()
        
        ssh.close

    except IndexError:
        prRed('No IP was found.\n\n')


    menu()

def findSwitch():

    prGreen('Please enter the credentials for the switch: \n')
    userName = input('Username: ')
    userPass = getpass.getpass()
    ipaddr = input('What is the IP of the core switch? ')
    switchPort = input('What is the switch port? (Change port from Te1/1/2 to Ten 1/1/2) ')
    showSwitch = ('sh cdp neighbors')
    try:    
        #Run CDP Neighbors
        ssh.connect(hostname=ipaddr, username=userName, password=userPass, port=port)
        _stdin, _stdout, _stderr = ssh.exec_command(showSwitch)
        list = _stdout.readlines()
        searchList = [list.index(i) for i in list if switchPort in i]
        ssh.close

    except paramiko.ssh_exception.AuthenticationException:
        prRed('Failed to connect to switch. Check credentials.\n')
        findSwitch()


    #split list at line containing "SwitchPort" to get hostname.
    try:
        indexValue = searchList[0]
        splitList = list[indexValue]
        switchPort = splitList.rsplit(' ',27)[0].rstrip().strip()
        
        for i, line in enumerate(list):
            if switchPort in line:
                switchName = list[i-1]
                break
        
        #Run command to get CDP neighbor details
        ssh.connect(hostname=ipaddr, username=userName, password=userPass, port=port)
        _stdin, _stdout, _stderr = ssh.exec_command('sh cdp n ' + switchPort + ' detail')
        listDetail = _stdout.readlines()

        #Iterate through CDP Neighbors detail to find switch IP
        for i, line in enumerate(listDetail):
            if switchName in line:
                switchIP = listDetail[i+2]
                break
        
        #Print Results of search    
        prGreen('The switch you are looking for is ' + switchName)
        prGreen("The switch's" + switchIP)

    except IndexError:
        prRed('No port was found.')
    
    
    menu()


def poPortDiscover():

    prGreen('Please enter the credentials for the switch: \n')
    userName = input('Username: ')
    userPass = getpass.getpass()
    ipaddr = input('What is the IP of the switch that contains the Po port? ')
    poPort = input('What is the Po port? ')
    
    try:    
        ssh.connect(hostname=ipaddr, username=userName, password=userPass, port=port)
        _stdin, _stdout, _stderr = ssh.exec_command('sh int ' + poPort)
        list = _stdout.readlines()
        searchList = [list.index(i) for i in list if 'Members in this channel:' in i]

    except paramiko.ssh_exception.AuthenticationException:
        prRed('Failed to connect to switch. Check credentials.\n')
        poPortDiscover()

    try:
        #split list at line containing "hostname" to get hostname.
        indexValue = searchList[0]
        splitList = list[indexValue]
        poPortMembers = splitList.split(' ',6)[6].strip()
        prGreen ('The Po port members are: ' + poPortMembers + '\n\n')

        ssh.close

    except IndexError:
        prRed('That Po port was not found.\n\n')

    menu()


def menu():
    prLightPurple("[1] Find the MAC address of a device from its IP and which port it is connected to.")
    prLightPurple("[2] Find the next switch from its connected port.")
    prLightPurple("[3] Search for the device on the next switch.")
    prLightPurple("[4] Find the members of a Po port.")
    prLightPurple("[0] Exit the program.")
    userChoice = int(input("Choose your desired task to run: "))

    while userChoice != 10:
        if userChoice == 1:
            switchConnect()
        elif userChoice == 2:
            findSwitch()
        elif userChoice == 3:
            nextSwitch()
        elif userChoice == 4:
            poPortDiscover()
        elif userChoice == 0:
            print('Closing program.')
            quit()
        else:
            prRed('Invalid choice')
            menu()

#Call Functions
def main():
    menu()


main()