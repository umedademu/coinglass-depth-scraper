# アイコンファイルの準備

EXEファイルにアイコンを設定するには、`icon.ico`ファイルが必要です。

## アイコンファイルの作成方法

### 方法1: オンラインコンバーター使用
1. PNGやJPG画像を用意（推奨: 256x256ピクセル）
2. オンラインICOコンバーターでICOファイルに変換
   - https://convertio.co/ja/png-ico/
   - https://www.icoconverter.com/

### 方法2: 画像編集ソフト使用
- GIMP（無料）でICOファイルとして保存
- Photoshopでプラグインを使用

### 方法3: デフォルトアイコン使用
アイコンファイルがない場合は、`coinglass_scraper.spec`の以下の行を編集：
```python
icon='icon.ico'  # この行を削除またはコメントアウト
```

## 推奨アイコンサイズ
- 16x16, 32x32, 48x48, 256x256 の複数サイズを含むマルチサイズICO

## ファイル配置
作成したアイコンファイルを以下の名前で保存：
```
C:\Users\user\Desktop\depth\icon.ico
```