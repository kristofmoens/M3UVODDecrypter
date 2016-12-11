from urllib import request
import os, sys
import urllib.request
import multiprocessing
from asyncio import coroutine
from aiohttp import request
import urllib
import asyncio
import aiohttp
import pipes
import subprocess
import shlex, shutil
import concurrent.futures

sem = asyncio.Semaphore(40)

# get content and write it to a file
def write_to_file(filename, content):
    with open(filename, 'wb') as f:
        f.write(content)
        
@asyncio.coroutine
def downloadFile(url):
    """Download specified url to disk"""
    with (yield from sem):  
        destinationfile = urltofilename(url)
        try:
            response = yield from aiohttp.request('GET', url)
            print ('Dumping contents of url to file', destinationfile)
            body = yield from response.read()
            write_to_file(destinationfile,body)
        except futures.TimeoutError as err:
            print("Request to {} took too long: {}".format(url, err))
        except requests.RequestException as err:
            print("General request err: {}".format(err))

def readKeyFromUrl(url):
    """Download key file and convert to hex"""
    keyfile = urllib.request.urlopen(url)
    data = keyfile.read()
    return ''.join('{:02x}'.format(x) for x in data)

def urltofilename(url):
    """A simplified url converter to filename"""
    return url[url.rfind('/')+1:]
    
if __name__ == '__main__':
    urls = []
    m3url = sys.argv[1]
    print("Starting extraction of", m3url)
    splitted = m3url.split("/")
    if splitted[-1].startswith("playlist"):
        destinationname = splitted[-2] 
    else:
        destinationname = splitted[-1]
        destinationname = destinationname[0:destinationname.find("?")-1] # removes parameter arguments
        
    destinationname = destinationname[0:destinationname.rfind(".")] # remove file extension
    existingfiles = [x for x in os.listdir(".") if x.startswith(destinationname)]
    destinationname = destinationname + "-" + str(len(existingfiles)) + ".ts"
    
    print("Destination file:", destinationname)
    f = urllib.request.urlopen(m3url)
    line = f.readline().decode("utf-8")

    if not line.startswith("#EXTM3U"):
        print("only extM3U files are supported!")
        sys.exit(0)
        
    while not line.startswith("#EXT-X-KEY"):
        line = f.readline().decode("utf-8") 
        
    line = line.rstrip()
    params=line[line.find(":")+1:].split(",")
    dparam = dict(p.split('=') for p in params)

    print("URL settings:", dparam)

    key = readKeyFromUrl(dparam["URI"][1:-1])
    loop = asyncio.get_event_loop()
    
    for l in f:
        if not l.startswith(b"#"):
            urls.append(l.decode("utf-8").rstrip())
    
    print("Starting the download process")
    loop.run_until_complete(asyncio.wait([downloadFile(x) for x in urls]))
    
    print("Finished downloading segments, starting decryption")
    
    cmdl = "openssl aes-128-cbc -d -K {} -iv {} -nosalt -out {}".format(key, dparam["IV"][2:], destinationname)
    proc = subprocess.Popen(shlex.split(cmdl), stdin=subprocess.PIPE)
    for file in urls:
        with open(urltofilename(file), 'rb') as inp:
            shutil.copyfileobj(inp,proc.stdin)
    print ("Decryption finished")
    