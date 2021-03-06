from __future__ import print_function
import gdown
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
import io
from googleapiclient.http import MediaIoBaseDownload

SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('/work/miniscopepipeline/miniursi/drive/credentials.json', SCOPES)
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

## The commands below use language from the Google API rather than gdown, however it runs into errors because
## Hopper is not an interactive interface. This is close to working but I am unsure if it will work with the format.
# request = service.files().get_media(fileId=file.get('id'))
                # fh = io.BytesIO()
                # downloader = MediaIoBaseDownload(fh, request)
                # done = False
                # while done is False:
                    # status, done = downloader.next_chunk()
           
            
def upload(folder_id):
    search(DRIVE, folder_id)
