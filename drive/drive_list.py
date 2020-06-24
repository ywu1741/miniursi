from __future__ import print_function
import gdown
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_id.json', SCOPES)
    creds = tools.run_flow(flow, store)
DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

def search(service, folder_id):
    page_token = None
    while True:
        response = service.files().list(q=('%s' % folder_id) in service.parents().get(),
                                        mimeType='video/avi',
                                        includeItemsFromAllDrives=True,
                                        supportsAllDrives=True,
                                        corpora='user',
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            print ('Found file: %s (%s)' % (file.get('name'), file.get('id')))
            gdown.download(('https://drive.google.com/uc?id=%s' % (file.get('id'))), (file.get('name')))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

search(DRIVE, '1K2WlRkFGEPk88GzaKjJQs_2uU8fXr8B-')
