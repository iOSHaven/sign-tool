import os
import boto3
import plistlib
import urllib
import pathlib
import subprocess
import glob
from dotenv import load_dotenv
load_dotenv()

REGION = os.getenv("DO_REGION", "nyc3")
ENDPOINT = os.getenv("DO_ENDPOINT", "https://" + REGION + ".digitaloceanspaces.com")
KEY = os.getenv("DO_KEY")
SECRET = os.getenv("DO_SECRET")
BUCKET = os.getenv("DO_BUCKET")
FOLDER = os.getenv("DO_FOLDER", "uploads")
DOMAIN = os.getenv("DO_DOMAIN")
VERSION = os.getenv("BUNDLE_VERSION", "1.0")
PREFIX = os.getenv("BUNDLE_PREFIX", "com." + BUCKET)
P12 = os.getenv("P12_PATH")
PASSWORD = os.getenv("P12_PASSWORD")
PROVISION = os.getenv("PROVISION_PATH")

session = boto3.session.Session()
client = session.client('s3',
                        region_name=REGION,
                        endpoint_url=ENDPOINT,
                        aws_access_key_id=KEY,
                        aws_secret_access_key=SECRET)

def upload(path):
    abspath = os.path.abspath(path)
    basename = os.path.basename(abspath)
    uploadpath = FOLDER + "/" + basename
    client.upload_file(abspath, BUCKET, uploadpath)
    client.put_object_acl( ACL='public-read', Bucket=BUCKET, Key=uploadpath )
    return DOMAIN + urllib.parse.quote('/' + uploadpath)

def generatePlist(ipaPath):
    name = pathlib.Path(ipaPath).stem
    pl = dict(
        items=[
            dict(
                assets=[
                    dict(
                        kind="software-package",
                        url=upload(ipaPath)
                    )
                ],
                metadata={
                    "bundle-identifier": PREFIX + "." + name,
                    "bundle-version": VERSION,
                    "kind": "software",
                    "title": "<![CDATA[" + name + "]]>"
                }
            )
        ]
    )
    plistpath = "plists/" + name + ".plist"
    if not os.path.exists("plists/"):
         os.mkdir("plists")

    with open(plistpath, 'wb') as fp:
        output = plistlib.dumps(pl).decode()
        output = output.replace("&lt;", "<")
        output = output.replace("&gt;", ">")
        fp.write(output.encode('utf-8'))

    plisturl = upload(plistpath)
    print(name + "\nitms-services://?action=download-manifest&url=" + plisturl + "\n\n")


def sign(ipa):
    #zsign -k *.p12 -m *.mobileprovision -o "Youtube Bat.ipa" -p 1 *.ipa
    subprocess.run(['zsign', 
                '-k', P12, 
                '-m', PROVISION, 
                '-o', ipa, 
                '-p', PASSWORD,
                ipa])
    generatePlist(ipa)


def signAllIpas():
    for ipa in list(glob.glob("*.ipa")):
        sign(ipa)

signAllIpas()