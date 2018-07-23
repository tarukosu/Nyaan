# このリポジトリについて
Suica を読みこんで、交通費申請を自動化するスクリプトです。

# 動作確認済み環境
- Raspberry Pi 3 (Raspbian 8.0) 
- PaSoRi RC-S380

# 環境構築
## miniconda のインストール
https://repo.continuum.io/miniconda/

ここから、arm 用の miniconda3 をインストール

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
sudo を使わずに読み取れるようにする  
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

sudo を付けなくても読み取れるようにする
```
$ lsusb
Bus 001 Device 005: ID 054c:06c3 Sony Corp.
$ python examples/tagtool.py --device usb:054c:06c3
...
[main] sudo sh -c 'echo SUBSYSTEM==\"usb\", ACTION==\"add\", ATTRS{idVendor}==\"054c\", ATTRS{idProduct}==\"06c3\", GROUP=\"plugdev\" >> /etc/udev/rules.d/nfcdev.rules'
```

表示されるコマンドを実行する
```
sudo sh -c 'echo SUBSYSTEM==\"usb\", ACTION==\"add\", ATTRS{idVendor}==\"054c\", ATTRS{idProduct}==\"06c3\", GROUP=\"plugdev\" >> /etc/udev/rules.d/nfcdev.rules'
```

USB を抜き差しする


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

# 設定ファイル
## google drive, spreadsheet の ID 設定
config_template.ini をコピーして config.ini を作成

## サウンド
タグを認識した際にならす効果音を audio フォルダに sound.mp3 という名前で配置

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
以下のように入力
```
@reboot /bin/bash /home/pi/App/Nyaan/start.sh
```


