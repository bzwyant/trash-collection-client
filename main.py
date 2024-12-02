#
# Client-side python app for photoapp, this time working with
# web service, which in turn uses AWS S3 and RDS to implement
# a simple photo application for photo storage and viewing.
#
# Authors:
#
#   Ben Wyant
#
#   Starter code: Prof. Joe Hummel
#   Northwestern University
#

import requests  # calling web service
import jsons  # relational-object mapping

import uuid
import pathlib
import logging
import sys
import os
import base64
import time
from datetime import datetime

from configparser import ConfigParser

from face_blur import blur_faces


class Higi:
    higiid: int  # these must match columns from DB table
    higiloc: str
    bucketfolder: str


class Image:
    imageid: int  # these must match columns from DB table
    userid: int
    assetname: str
    bucketkey: str


def web_service_get(url):
    """
    Submits a GET request to a web service at most 3 times, since
    web services can fail to respond e.g. to heavy user or internet
    traffic. If the web service responds with status code 200, 400
    or 500, we consider this a valid response and return the response.
    Otherwise we try again, at most 3 times. After 3 attempts the
    function returns with the last response.

    Parameters
    ----------
    url: url for calling the web service

    Returns
    -------
    response received from web service
    """

    try:
        retries = 0

        while True:
            response = requests.get(url)

            if response.status_code in [200, 400, 500]:
                break

            retries = retries + 1
            if retries < 3:
                # try at most 3 times
                time.sleep(retries)
                continue

            break

        return response

    except Exception as e:
        print("**ERROR**")
        logging.error("web_service_get() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return None


def web_service_req(url, data, req):
    """
    Submits a PUT request to a web service at most 3 times, since
    web services can fail to respond e.g. to heavy user or internet
    traffic. If the web service responds with status code 200, 400
    or 500, we consider this a valid response and return the response.
    Otherwise we try again, at most 3 times. After 3 attempts the
    function returns with the last response.

    Args
        url: url for calling the web service

    Returns
        response received from web service
    """

    try:
        retries = 0

        while True:
            response = req(url, json=data)

            if response.status_code in [200, 400, 500]:
                break

            retries = retries + 1
            if retries < 3:
                time.sleep(retries)
                continue
            break

        return response

    except Exception as e:
        print("**ERROR**")
        logging.error("web_service_put() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return None


###################################################################
#
# prompt
#
def prompt():
    """
    Prompts the user and returns the command number

    Parameters
    ----------
    None

    Returns
    -------
    Command number entered by user (0, 1, 2, ...)
    """

    try:
        print()
        print(">> Enter a command:")
        print("   0 => end")
        print("   1 => stats")
        print("   2 => higis")
        print("   3 => images")
        print("   4 => download")
        print("   5 => add higi")
        print("   6 => upload")

        cmd = int(input())
        return cmd

    except Exception as e:
        print("ERROR")
        print("ERROR: invalid input")
        print("ERROR")
        return -1


###################################################################
#
# stats
#
def stats(baseurl):
    """
    Prints out S3 and RDS info: bucket status, # of users and
    assets in the database

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        api = "/stats"
        url = baseurl + api

        res = web_service_get(url)

        if res.status_code != 200:
            # failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  # we'll have an error message
                body = res.json()
                print("Error message:", body["message"])
            
            return

        # deserialize and extract stats:
        body = res.json()
      
        print("bucket status:", body["message"])
        print("# of higis:", body["db_numHigis"])
        print("# of images:", body["db_numImages"])

    except Exception as e:
        logging.error("stats() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


def higis(baseurl):
    """
    Prints out all the users in the database

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        api = "/higis"
        url = baseurl + api

        # res = requests.get(url)
        res = web_service_get(url)

        if res.status_code != 200:
            # failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  # we'll have an error message
                body = res.json()
                print("Error message:", body["message"])

            return

        # deserialize and extract users:
        body = res.json()

        higis = []
        for row in body["data"]:
            higi = jsons.load(row, Higi)
            higis.append(higi)

        for higi in higis:
            print(higi.higiid)
            print(" ", higi.higiloc)
            print(" ", higi.bucketfolder)

    except Exception as e:
        logging.error("users() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


###################################################################
#
# assets
#
def images(baseurl):
    """
    Prints out all the assets in the database

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        api = "/images"
        url = baseurl + api

        res = web_service_get(url)

        if res.status_code != 200:
            # failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  # we'll have an error message
                body = res.json()
                print("Error message:", body["message"])

            return

        # deserialize and extract assets:
        body = res.json()
        images = []
        for row in body["data"]:
            image = jsons.load(row, Image)
            images.append(image)

        for image in images:
            print(image.imageid)
            print(" ", image.timetaken)
            print(" ", image.bucketkey)

    except Exception as e:
        logging.error("assets() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


###################################################################
#
# add_user
#
def add_higi(baseurl):
    """
    Prompts the user for the new user's email,
    last name, and first name, and then inserts
    this user into the database. But if the user's
    email already exists in the database, then we
    update the user's info instead of inserting
    a new user.

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        print("Enter the location>")
        higiloc = input()

        # generate unique folder name:
        folder = str(uuid.uuid4())

        #
        # build the data packet:
        data = {"higiloc": higiloc, "bucketfolder": folder}

        api = "/higi"
        url = baseurl + api

        res = web_service_req(url, data, requests.put)

        if res.status_code != 200:
            # failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  # we'll have an error message
                body = res.json()
                print("Error message:", body["message"])

            return

        # success, extract userid:
        body = res.json()

        higiid = body["higiid"]
        message = body["message"]

        print("Higi", higiid, "successfully", message)

    except Exception as e:
        logging.error("add_higi() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


###################################################################
#
# download
#
def download(baseurl, display=False):
    """
    Prompts the user for an asset id, and downloads
    that asset (image) from the bucket. Displays the
    image after download if display param is True.

    Parameters
    ----------
    baseurl: baseurl for web service,
    display: optional param controlling display of image

    Returns
    -------
    nothing
    """

    try:
        print("Enter image id>")
        imageid = input()

        api = "/image"
        url = baseurl + api + "/" + imageid

        res = web_service_get(url)

        if res.status_code != 200:
            # failed:
            if res.status_code in [400, 500]:  # we'll have an error message
                body = res.json()
                print(body["message"])

            return

        # deserialize and extract image:
        body = res.json()

        higiid = body["higi_id"]
        timeTaken = body["time_taken"]
        bucketkey = body["bucket_key"]
        bytes = base64.b64decode(body["data"])

        print("higi id:", higiid)
        print("photo time taken:", timeTaken)
        print("bucket key:", bucketkey)

        #
        # write the binary data to a file (as a
        # binary file, not a text file):
        #
        image_name = f"image_{imageid}.jpg"
        with open(image_name, "wb") as outfile:
            outfile.write(bytes)

        print("Downloaded from S3 and saved as '", image_name, "'")

    except Exception as e:
        logging.error("download() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


###################################################################
#
# upload
#
def upload(baseurl):
    """
    Prompts the user for a local filename and user id,
    and uploads that asset (image) to the user's folder
    in the bucket. The asset is given a random, unique
    name. The database is also updated to record the
    existence of this new asset in S3.

    Args
        baseurl: baseurl for web service
    """

    try:
        print("Enter local filename>")
        local_filename = input()

        if not pathlib.Path(local_filename).is_file():
            print("Local file '", local_filename, "' does not exist...")
            return

        print("Enter higi id>")
        higiid = input()

        # build the data packet:
        with open(local_filename, "rb") as infile:
            bytes = infile.read()

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        datastr = base64.b64encode(bytes).decode()
        blurred_image_str = blur_faces(datastr)

        data = {"data": blurred_image_str, "timetaken": current_datetime}

        #
        # call the web service:
        #
        api = "/image"
        url = baseurl + api + "/" + higiid

        res = web_service_req(url, data, requests.post)

        #
        # let's look at what we got back:
        #
        if res.status_code != 200:
            # failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  # we'll have an error message
                body = res.json()
                print("Error message:", body["message"])
            #
            return

        # success, extract userid:
        body = res.json()

        imageid = body["imageid"]

        print("Image uploaded, image id =", imageid)

    except Exception as e:
        logging.error("upload() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


def test_image_blur(baseurl):
    """
    Prompts the user for a local filename and user id,
    and uploads that asset (image) to the user's folder
    in the bucket. The asset is given a random, unique
    name. The database is also updated to record the
    existence of this new asset in S3.

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        print("Enter local filename>")
        local_filename = input()

        if not pathlib.Path(local_filename).is_file():
            print("Local file '", local_filename, "' does not exist...")
            return

        # build the data packet:
        with open(local_filename, "rb") as infile:
            bytes = infile.read()

        #
        # now encode the image as base64. Note b64encode returns
        # a bytes object, not a string. So then we have to convert
        # (decode) the bytes -> string, and then we can serialize
        # the string as JSON for upload to server:
        #
        data = base64.b64encode(bytes)
        datastr = data.decode()

        data = {"data": datastr}

        #
        # call the web service:
        #
        api = "/test"
        url = baseurl + api

        res = web_service_req(url, data, requests.post)

        #
        # let's look at what we got back:
        #
        if res.status_code != 200:
            # failed:
            print("Failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code in [400, 500]:  # we'll have an error message
                body = res.json()
                print("Error message:", body["message"])
            #
            return

        # success, extract userid:
        body = res.json()

        imageid = body["imageid"]

        print("Image uploaded, image id =", imageid)

    except Exception as e:
        logging.error("upload() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


#########################################################################
# main
#
print("** Welcome to Sensify Client **")
print()

# eliminate traceback so we just get error message:
sys.tracebacklimit = 0

#
# what config file should we use for this session?
#
config_file = "sensify-client-config.ini"

print("What config file to use for this session?")
print("Press ENTER to use default (sensify-client-config.ini),")
print("otherwise enter name of config file>")
s = input()

if s == "":  # use default
    pass  # already set
else:
    config_file = s

#
# does config file exist?
#
if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)

#
# setup base URL to web service:
#
configur = ConfigParser()
configur.read(config_file)
baseurl = configur.get("client", "webservice")

#
# make sure baseurl does not end with /, if so remove:
#
if len(baseurl) < 16:
    print("**ERROR**")
    print(
        "**ERROR: baseurl '",
        baseurl,
        "' in .ini file is empty or not nearly long enough, please fix",
    )
    sys.exit(0)

if baseurl.startswith("https"):
    print("**ERROR**")
    print(
        "**ERROR: baseurl '",
        baseurl,
        "' in .ini file starts with https, which is not supported (use http)",
    )
    sys.exit(0)

lastchar = baseurl[len(baseurl) - 1]
if lastchar == "/":
    baseurl = baseurl[:-1]

#
# main processing loop:
#
cmd = prompt()

while cmd != 0:
    #
    if cmd == 1:
        stats(baseurl)
    elif cmd == 2:
        higis(baseurl)
    elif cmd == 3:
        images(baseurl)
    elif cmd == 4:
        download(baseurl)
    elif cmd == 5:
        add_higi(baseurl)
    elif cmd == 6:
        upload(baseurl)
    elif cmd == 7:
        test_image_blur(baseurl)
    else:
        print("** Unknown command, try again...")
    #
    cmd = prompt()

#
# done
#
print()
print("** done **")
