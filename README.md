# 「にゃーん」について
Suica などの交通系 IC カードを読みこみ、Google スプレッドシートに交通費を記入するスクリプトです。

# 動作確認済み環境
- Raspberry Pi 3 (Raspbian 8.0) 
- PaSoRi RC-S380

# 環境構築
## miniconda のインストール
https://repo.continuum.io/miniconda/

ここから、arm 用の miniconda3 をインストールします。

```
$ wget https://repo.continuum.io/miniconda/Miniconda3-3.16.0-Linux-armv7l.sh
$ bash Miniconda3-3.16.0-Linux-armv7l.sh
```

## conda の環境構築
```
$ conda create -n nyaan python=2.7
$ source activate nyaan
```

## nfcpy のインストール
```
$ source activate nyaan
$ pip install nfcpy
```

## nfc リーダーの設定
sudo を使わずに読み取れるようにします。  
[参考記事: Raspberry PiでFelicaのIDmを表示する](https://qiita.com/ihgs/items/34eefd8d01c570e92984#nfcpyをインストール)

```
$ git clone https://github.com/nfcpy/nfcpy
$ cd nfcpy
```

テスト（実行後、Suica をかざす）
```
$ sudo su
# source /home/pi/.bashrc
# source activate nyaan
# python examples/tagtool.py show
```

sudo を付けなくても読み取れるようにします。
```
$ lsusb
Bus 001 Device 005: ID 054c:06c3 Sony Corp.
$ python examples/tagtool.py --device usb:054c:06c3
...
[main] sudo sh -c 'echo SUBSYSTEM==\"usb\", ACTION==\"add\", ATTRS{idVendor}==\"054c\", ATTRS{idProduct}==\"06c3\", GROUP=\"plugdev\" >> /etc/udev/rules.d/nfcdev.rules'
```

表示されるコマンドを実行します。
```
sudo sh -c 'echo SUBSYSTEM==\"usb\", ACTION==\"add\", ATTRS{idVendor}==\"054c\", ATTRS{idProduct}==\"06c3\", GROUP=\"plugdev\" >> /etc/udev/rules.d/nfcdev.rules'
```

USB を抜き差しします。


## google api ライブラリのインストール
```
$ pip install --upgrade google-api-python-client
$ pip install --upgrade oauth2client
```

## その他ライブラリのインストール

### requests
```
$ pip install requests
```

### mpg321
```
$ sudo apt-get install mpg321
```

# Google スプレッドシートの準備とシークレットキーの取得
## ドライブとシートの準備
交通費申請シートを保存するためのフォルダを作成します。
（Team Drive は使えません）

また、管理用シートと交通費申請シートのテンプレートを下記から自身の Google Drive にコピーしてください。

- https://docs.google.com/spreadsheets/d/1dStx3uWP2UkjDQgnr_VODASaIt8e_q7VLA-OcdxXlxY/edit?usp=sharing
- https://docs.google.com/spreadsheets/d/1n9buB-A3SHqDjfHcShS1whdwOIb6v6B8tg2rjZ00TgU/edit?usp=sharing

## シークレットキーの取得
https://dev.classmethod.jp/etc/google-spreadsheet-append-csv-from-command-line/#toc-oauth

上記ページを参考にして、以下のリンクから Sheets API を有効にし、ダウンロードしたファイルを client_secret.json という名前で credentials フォルダに配置します。  
https://console.developers.google.com/start/api?id=sheets.googleapis.com

同様に、以下のリンクから Drive API を有効にし、ダウンロードしたファイルを client_secret_drive.json という名前で credentials フォルダに配置します。  
https://console.developers.google.com/start/api?id=drive.googleapis.com

# 設定ファイル
## Google ドライブ, スプレッドシートの ID 設定
config_template.ini をコピーして config.ini を作成します。  
フォルダの ID と 2つのシートの ID を config.ini に記入してください。

ID はフォルダやシートをブラウザで開いた際に、url の末尾に表示されている英数字です。（以下の xxx の部分です）
```
https://drive.google.com/drive/u/0/folders/xxxxxxxxxxxxxxxxxxxxxxx
```


## サウンド
タグを認識した際にならす効果音を audio フォルダに sound.mp3 という名前で配置してください。

私は下記ページの「猫がニャーン１a」を利用させていただいています。  
http://taira-komori.jpn.org/animals01.html

# 実行
## ユーザーの登録
```
$ source activate nyaan
$ python scripts/nyaan.py -r <ユーザー名>
```

## 実行
```
$ source activate nyaan
$ python scripts/nyaan.py
```

## 自動起動設定
```
$ crontab -e
```
以下のように入力します。
```
@reboot /bin/bash /path/to/Nyaan/start.sh
```


