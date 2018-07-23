#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import time
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import argparse

from suica_read import *

class User:
    def __init__(self, row_id, name, tag_id, folder_id, latest_record_id, exclude_holiday="TRUE"):
        self.row_id = row_id
        self.name = name
        self.tag_id = tag_id
        self.folder_id = folder_id
        self.latest_record_id = int(latest_record_id)
        self.exclude_holiday = exclude_holiday == "TRUE"

    def __str__(self):
        return "%s (tag: %s)" % (self.name, self.tag_id)


class GoogleSheets:
    def __init__(self, folder_id, master_sheet_id, template_sheet_id):
        self.folder_id = folder_id
        self.master_sheet_id = master_sheet_id
        self.template_sheet_id = template_sheet_id

        while True:
            time.sleep(5)
            try:
                credentials_folder = '../credentials/'

                # Setup the Sheets API
                SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
                store = file.Storage(credentials_folder + 'credentials.json')
                creds = store.get()

                if not creds or creds.invalid:
                    flow = client.flow_from_clientsecrets(credentials_folder + 'client_secret.json', SCOPES)
                    parser = argparse.ArgumentParser(add_help=False)
                    parser.add_argument('--logging_level', default='ERROR')
                    parser.add_argument('--noauth_local_webserver', action='store_true',
                                default=True, help='Do not run a local web server.')
                    args = parser.parse_args([])
                    creds = tools.run_flow(flow, store, args)

                self.service = build('sheets', 'v4', http=creds.authorize(Http()))

                # Setup the Drive API
                SCOPES = 'https://www.googleapis.com/auth/drive'
                store = file.Storage(credentials_folder + 'credentials_drive.json')
                creds = store.get()

                if not creds or creds.invalid:
                    flow = client.flow_from_clientsecrets(credentials_folder + 'client_secret_drive.json', SCOPES)
                    parser = argparse.ArgumentParser(add_help=False)
                    parser.add_argument('--logging_level', default='ERROR')
                    parser.add_argument('--noauth_local_webserver', action='store_true',
                                                            default=True, help='Do not run a local web server.')
                    args = parser.parse_args([])

                    creds = tools.run_flow(flow, store,args)
                self.drive_service = build('drive', 'v3', http=creds.authorize(Http()))
                break
            except:
                print("initialization error")

    def createUser(self, name, tag_id, exclude_holiday):
        results = self.drive_service.files().list(
            q="parents in '" + self.folder_id + "' and mimeType = 'application/vnd.google-apps.folder'",
            pageSize=100, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        user_folder_id = ""
        for item in items:
            if item['name'] == name:
                user_folder_id = item['id']
                break

        # フォルダがない場合は作成
        if user_folder_id == "":
            file_metadata = {
            'name': name,
            'parents' : [self.folder_id],
            'mimeType': 'application/vnd.google-apps.folder'
            }
            # TODO This code does not work for Team Drive
            value = self.drive_service.files().create(body=file_metadata, fields='id').execute()
            user_folder_id = value["id"]

        body = {
            'values': [[name, tag_id, user_folder_id, 0, exclude_holiday]]
        }
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.master_sheet_id, range="A1",
            valueInputOption='USER_ENTERED',body=body).execute()

    def updateCell(self, sheet_id, cell, value):
        body = {
            'values': [[value]]
        }
        result = self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=cell,
            valueInputOption='USER_ENTERED', body=body).execute()

    def updateUser(self, user, latest_record_id):
        body = {
            'values': [[latest_record_id]]
        }
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.master_sheet_id, range="D" + str(user.row_id),
            valueInputOption='USER_ENTERED', body=body).execute()


    def findUserByTagId(self, target_tag_id):
        max_tag_num = 100

        result = self.service.spreadsheets().values().get(
        spreadsheetId=self.master_sheet_id, range='A1:E' + str(max_tag_num)).execute()

        rows = result['values']
        for index, master_data in enumerate(rows):
            tag_id = master_data[1]
            if tag_id == target_tag_id:
                return User(index+1, *master_data)

        return None

    def getSheetInfo(self, sheet_id):
        result = self.service.spreadsheets().get(spreadsheetId=sheet_id).execute()

    def getSheets(self, folder_id):
        results = self.drive_service.files().list(
            q="parents in '" + folder_id + "' and mimeType != 'application/vnd.google-apps.folder'",
            pageSize=100, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        return items

    def getSheetIdByName(self, folder_id, name):
        results = self.drive_service.files().list(
            q="parents in '{0}' and mimeType != 'application/vnd.google-apps.folder' and name = '{1}'".format(folder_id, name),
            pageSize=1, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if len(items) == 0:
            return ""
        return items[0].get("id", "")

    def copyTemplateSheet(self, name, folder_id):
        return self.copySheet(name, folder_id, self.template_sheet_id)

    def copySheet(self, name, folder_id, template_id):
        body = {
            "parents" : [folder_id],
            "name": name
        }

        results = self.drive_service.files().copy(fileId=template_id,
                                                  body=body).execute()
        return results.get("id", "")

    def addSheet(self, sheet_id, sheet_name):
        result = self.service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body = {
                "requests" : [
                    {"addSheet": {
                        "properties": {
                            "title": sheet_name,
                        }
                    }
                    }
                ]
            }
        ).execute()

    def addRecord(self, sheet_id, record):
        ValueInputOption = 'USER_ENTERED'
        date = "%d/%d/%d" % (record.year, record.month, record.day)

        body = {
            'values': [[date, record.in_station.station_value, record.out_station.station_value, record.cost, "片道", record.cost]]
        }
        result = self.service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range="A4",
            valueInputOption='USER_ENTERED', body=body).execute()

    def addRecords(self, sheet_id, records):
        ValueInputOption = 'USER_ENTERED'

        values = []
        for record in records:
            date = "%d/%d/%d" % (record.year, record.month, record.day)
            values.append([date, record.in_station.station_value, record.out_station.station_value, record.cost, "片道", record.cost])
            

        body = {
            'values': values
        }
        result = self.service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range="A4",
            valueInputOption='USER_ENTERED', body=body).execute()



if __name__ == "__main__":
    gs = GoogleSheets()

    # create user
    # gs.createUser("hoge", "ABC")

    # find user
    # user = gs.findUserByTagId("ABC")
    # print(user)

    # sheet_name = "{0}-{1:02}_交通費精算_{2}".format(2018, 6, user.name)

    # find or create sheet
    # sheet_id = gs.getSheetIdByName(user.folder_id, sheet_name)
    # if sheet_id == "":
    #     sheet_id = gs.copyTemplateSheet(sheet_name, user.folder_id)

    # add record
    # record = HistoryRecord(bytes("aaaaaaaaaaaaaaaa", encoding="ascii"))
    # record.in_station.station_value = "乗車駅"
    # record.out_station.station_value = "降車駅"
    # record.cost = 240
    # gs.addRecord(sheet_id, record)
    # gs.updateUser(user, user.latest_record_id + 1)
