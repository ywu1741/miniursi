from __future__ import print_function
import gdown
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)

DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

def search(service, folder_id):
    page_token = None
    while True:
        response = service.files().list(q="mimeType='video/avi'",
                                        includeItemsFromAllDrives=True,
                                        supportsAllDrives=True,
                                        corpora='allDrives',
                                        spaces='drive',
                                        fields='nextPageToken, files(id,parents,name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            parents_found = (file.get('parents')),
            print(parents_found),
            if folder_id in (file.get('parents')):
                print ('Found file: %s (%s)' % (file.get('name'), file.get('id')))
                gdown.download(('https://drive.google.com/uc?id=%s' % (file.get('id'))), (file.get('name')))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

def upload(folder_id):
    search(DRIVE, folder_id)

upload('1tr_Laq--VNw5gyVPYQgASNY3iFp9aYyX')
