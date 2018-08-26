#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from suica_read import *
from gsheets import *
import nfc
import argparse
import os
import subprocess
from subprocess import Popen
import time

import requests
import ConfigParser


def playSound():
    soundfile = os.path.dirname(os.path.abspath(__file__)) + "/../audio/sound.mp3"
    cmd = "mpg321 " + soundfile
    devnull = open('/dev/null', 'w')
    proc = Popen(cmd, shell=True, stdout = devnull, stderr = devnull)
    
def connected(tag):
    num_blocks = 20
    service_code = 0x090f
    show_all_history = False
    show_travel_costs_history = True

    if hasattr(nfc.tag, "tt3") and isinstance(tag, nfc.tag.tt3.Type3Tag):
        try:
            playSound()
            sc = nfc.tag.tt3.ServiceCode(service_code >> 6, service_code & 0x3f)
            
            history_array = []
            for i in range(num_blocks):
                bc = nfc.tag.tt3.BlockCode(i, service=0)
                data = tag.read_without_encryption([sc], [bc])
                history = HistoryRecord(data)
                history_array.insert(0, history)

                if show_all_history:
                    print("=== %02d ===" % i)
                    print("連番: %d" % history.sequence_id)
                    print("端末種: %s" % history.console)
                    print("処理: %s" % history.process)
                    print("日付: %02d-%02d-%02d" % (history.year, history.month, history.day))
                    print("入線区: %s-%s" % (history.in_station.company_value, history.in_station.line_value))
                    print("入駅順: %s" % history.in_station.station_value)
                    print("出線区: %s-%s" % (history.out_station.company_value, history.out_station.line_value))
                    print("出駅順: %s" % history.out_station.station_value)
                    print("残高: %d" % history.balance)
                    print("BIN: ")
                    print( "".join(['%02x ' % s for s in data]))

            tag_id = tag.identifier.encode("hex").upper()
            user = gs.findUserByTagId(tag_id)
            if user is None:
                print("This tag is not registered")
                return

            print(user.latest_record_id)

            registration_array = []
            
            for history, prev_history in zip(history_array[1:], history_array):
                if history.sequence_id <= user.latest_record_id:
                    continue

                # 休日を判定
                if user.exclude_holiday:
                    holiday_check_url = "http://s-proj.com/utils/checkHoliday.php?date=20%02d%02d%02d" % (history.year, history.month, history.day)
                    r = requests.get(holiday_check_url)
                    if r.text == "holiday":
                        continue
                
                history.cost = prev_history.balance - history.balance
                if history.process == "バス":
                    history.in_station.station_value = "バス"
                    history.out_station.station_value = "バス"
                    
                if history.process == "運賃支払" or history.process == "バス":
                    if len(registration_array) == 0 or not registration_array[-1][0].same_month(history):
                        registration_array.append([history])
                    else:
                        registration_array[-1].append(history)
                    # print(registration_array)
                    
                    if show_travel_costs_history:
                        print("連番: %d" % history.sequence_id)
                        print("交通費: %d" % history.cost)
                        print("出発: %s" % history.in_station.station_value)
                        print("到着: %s" % history.out_station.station_value)

                        
            # スプレッドシートに登録
            for histories in registration_array:
                sheet_name = (u"20%02d-%02d_交通費精算_%s" % (histories[0].year, histories[0].month, user.name)).encode('utf-8')
                sheet_id = gs.getSheetIdByName(user.folder_id, sheet_name)
                if sheet_id == "":
                    sheet_id = gs.copyTemplateSheet(sheet_name, user.folder_id)
                    gs.updateCell(sheet_id, "B2", user.name)

                gs.addRecords(sheet_id, histories)
                gs.updateUser(user, histories[-1].sequence_id)
                
        except Exception as e:
            print("error: %s" % e)
    else:
        print("error: tag isn't Type3Tag")

def register(tag):
    print("start registration")
    print("username: " + username)
    print("exclude holiday: " + str(exclude_holiday))
    if hasattr(nfc.tag, "tt3") and isinstance(tag, nfc.tag.tt3.Type3Tag):
        try:
            playSound()
            tag_id = tag.identifier.encode("hex").upper()
            print("tag id: " + tag_id)
            user = gs.findUserByTagId(tag_id)
            if user is not None:
                print("This card is already registered")
                return
            gs.createUser(username, tag_id, exclude_holiday)
            print("Registration completed successfully")

        except Exception as e:
            print("error: %s" % e)
    else:
        print("error: tag isn't Type3Tag")


if __name__ == "__main__":
    inifile = ConfigParser.SafeConfigParser()
    configfile = os.path.dirname(os.path.abspath(__file__)) + "/../config.ini"
    inifile.read(configfile)
    folder_id = inifile.get("google", "folder_id")
    master_sheet_id = inifile.get("google", "master_sheet_id")
    template_sheet_id = inifile.get("google", "template_sheet_id")

    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--register',
                        action='store',
                        const=None,
                        default=None,
                        metavar="username"
                        )

    parser.add_argument('-i', '--include-holiday',
                        action='store_true',
                        default=False
                        )


    args = parser.parse_args()
    if args.register is not None:
        username = args.register
        exclude_holiday = not args.include_holiday

    
    clf = nfc.ContactlessFrontend('usb')
    
    credentials_folder = os.path.dirname(os.path.abspath(__file__)) + "/../credentials"
    gs = GoogleSheets(folder_id, master_sheet_id, template_sheet_id, credentials_folder)

    rdwr_options = {
        "targets" : ['212F', '424F']
    }
    
    if args.register is None:
        while True:
            rdwr_options['on-connect'] = connected
            clf.connect(rdwr=rdwr_options)
            time.sleep(2)
                
    else:
        rdwr_options['on-connect'] = register
        clf.connect(rdwr=rdwr_options)
