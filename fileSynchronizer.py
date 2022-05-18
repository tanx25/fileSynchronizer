#!/usr/bin/python3
# ==============================================================================
# description     :This is a skeleton code for programming assignment
# usage           :python Skeleton.py trackerIP trackerPort
# python_version  :3.5
# Authors         :Yongyong Wei, Rong Zheng
# ==============================================================================
import math
import socket, sys, threading, json, time, os, ssl
import os.path
import glob
import json
import optparse



def validate_ip(s):
    """
    Arguments:
    s -- dot decimal IP address in string
    Returns:
    True if valid; False otherwise
    """

    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True

def validate_port(x):
    """
    Arguments:
    x -- port number
    Returns:
    True if valid; False, otherwise
    """

    if not x.isdigit():
        return False
    i = int(x)
    if i < 0 or i > 65535:
            return False
    return True

def get_file_info():
    """ Get file info in the local directory (subdirectories are ignored)
    Return: a JSON array of {'name':file,'mtime':mtime}
    i.e, [{'name':file,'mtime':mtime},{'name':file,'mtime':mtime},...]
    Hint: a. you can ignore subfolders, *.so, *.py, *.dll
          b. use os.path.getmtime to get mtime, and round down to integer
    """
    file_arr = []
    local_Files = []
    for f in os.listdir('.'):
        if os.path.isfile(f):
            local_Files.append(f)

    for file in local_Files:
        if not (file.endswith('.so') or file.endswith('.py') or file.endswith('.dll')):
             file_arr += [{'name': file, 'mtime': os.path.getmtime(file)}]
    return file_arr


def check_port_available(check_port):
    """Check if a port is available
    Arguments:
    check_port -- port number
    Returns:
    True if valid; False otherwise
    """
    if str(check_port) in os.popen("netstat -na").read():
        return False
    return True


def get_next_available_port(initial_port):
    """Get the next available port by searching from initial_port to 2^16 - 1
       Hint: You can call the check_port_avaliable() function
             Return the port if found an available port
             Otherwise consider next port number
    Arguments:
    initial_port -- the first port to check

    Return:
    port found to be available; False if no port is available.
    """
    for port in range(initial_port, 65536):
        if check_port_available(port):
            return port
    return False


class FileSynchronizer(threading.Thread):
    def __init__(self, trackerhost,trackerport, port, host='0.0.0.0'):

        threading.Thread.__init__(self)
        #Port for serving file requests
        self.port = port #YOUR CODE
        self.host = host #YOUR CODE

        #Tracker IP/hostname and port
        self.trackerhost = trackerhost #YOUR CODE
        self.trackerport = trackerport #YOUR CODE

        self.BUFFER_SIZE = 8192

        #Create a TCP socket to communicate with tracker
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #YOUR CODE
        self.client.settimeout(180)

        #Store the message to be sent to tracker. Initialize to Init message
        #that contains port number and local file info.
        self.msg = json.dumps({'port': self.port, 'files': get_file_info()}) #YOUR CODE
        #Create a TCP socket to serve file requests
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #YOUR CODE

        try:
            self.server.bind((self.host, self.port))
        except socket.error:
            print('Bind failed %s' % (socket.error))
            sys.exit()
        self.server.listen(10)

    # Not currently used. Ensure sockets are closed on disconnect
    def exit(self):
        self.server.close()

    #Handle file request from a peer
    def process_message(self, conn, addr):
        '''
        Arguments:
        self -- self object
        conn -- socket object for an accepted connection from a peer
        addr -- address bound to the socket of the accepted connection
        '''
        #YOUR CODE
        #Step 1. read the file name contained in the request through conn
        #Step 2. read content of that file(assumming binary file <4MB), you can open with 'rb'
        #Step 3. send the content back to the requester through conn
        #Step 4. close conn when you are done.

        print("reading filename")
        filename = conn.recv(self.BUFFER_SIZE)
        with open(filename, 'rb') as f:
            content = f.read()
        print("sent")
        conn.send(content)
        conn.close()



    def run(self):
        self.client.connect((self.trackerhost,self.trackerport))
        t = threading.Timer(2, self.sync)
        t.start()
        print('Waiting for connections on port %s' % (self.port))
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.process_message, args=(conn,addr)).start()

    #Send Init or KeepAlive message to tracker, handle directory response message
    #and call self.syncfile() to request files from peers
    def sync(self):
        print(('connect to:'+self.trackerhost,self.trackerport))
        #Step 1. send Init msg to tracker
        #YOUR CODE
        self.client.sendall(self.msg.encode())
        #msg_str = json.dumps(self.msg)
        #self.client.send(bytes(msg_str, 'utf-8'))
        #Step 2. receive a directory response message from tracker
        # directory_response_message = ''
        # YOUR CODE
        directory_response_message = self.client.recv(self.BUFFER_SIZE)
        
        print('received from tracker:', directory_response_message)

        # Step 3. parse the directory response message. If it contains new or
        # more up-to-date files, request the files from the respective peers.
        # NOTE: compare the modified time of the files in the message and
        # that of local files of the same name.
        # Hint: a. use json.loads to parse the message from the tracker
        #      b. read all local files, use os.path.getmtime to get the mtime
        #         (also note round down to int)
        #      c. for new or more up-to-date file, you need to create a socket,
        #         connect to the peer that contains that file, send the file name, and
        #         receive the file content from that peer
        #      d. finally, write the file content to disk with the file name, use os.utime
        #         to set the mtime
        # YOUR CODE
        if (directory_response_message != ''): # if the msg is not empty
            directory_response_message_json = json.loads(directory_response_message)

            for files in directory_response_message_json.keys():

                file_ip = directory_response_message_json[files]['ip']
                file_port = directory_response_message_json[files]['port']
                file_mtime = directory_response_message_json[files]['mtime']

                if files not in os.listdir(".") or (os.path.getmtime(files) < file_mtime):
                    # file not exists
                    transfer_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    transfer_file.connect((file_ip, file_port))
                    transfer_file.send(files.encode())
                    new_content = transfer_file.recv(self.BUFFER_SIZE).decode('utf-8')
                    transfer_file.close()
                    with open(files, 'w') as File:
                        File.write(new_content)
                    os.utime(files, (file_mtime, file_mtime))
                    print(files+" "+"received")

        #Step 4. construct the KeepAlive message
        self.msg = json.dumps({'port': self.port}) #YOUR CODE

        #Step 5. start a timer
        t = threading.Timer(5, self.sync)
        t.start()
    
if __name__ == '__main__':
    #parse commmand line arguments
    parser = optparse.OptionParser(usage="%prog ServerIP ServerPort")
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error("No ServerIP and ServerPort")
    elif len(args) < 2:
        parser.error("No ServerIP or ServerPort")
    else:
        if validate_ip(args[0]) and validate_port(args[1]):
            tracker_ip = args[0]
            tracker_port = int(args[1])

        else:
            parser.error("Invalid ServerIP or ServerPort")

    #get free port
    synchronizer_port = get_next_available_port(8000)
    synchronizer_thread = FileSynchronizer(tracker_ip,tracker_port,synchronizer_port)
    synchronizer_thread.start()
