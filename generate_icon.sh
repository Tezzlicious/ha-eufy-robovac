#!/bin/bash

# SVGからPNGへの変換スクリプト
# このスクリプトを実行してPNGアイコンを生成します

# ImageMagickまたはrsvg-convertがインストールされている場合
# rsvg-convert -w 256 -h 256 icon.svg > icon.png
# または
# convert -background transparent -resize 256x256 icon.svg icon.png

echo "PNGアイコンを生成するには、以下のコマンドのいずれかを実行してください："
echo ""
echo "1. rsvg-convertを使用する場合（推奨）:"
echo "   brew install librsvg  # macOSの場合"
echo "   rsvg-convert -w 256 -h 256 custom_components/eufy_robovac/icon.svg > custom_components/eufy_robovac/icon.png"
echo ""
echo "2. ImageMagickを使用する場合:"
echo "   brew install imagemagick  # macOSの場合"
echo "   convert -background transparent -resize 256x256 custom_components/eufy_robovac/icon.svg custom_components/eufy_robovac/icon.png"
echo ""
echo "3. オンラインツールを使用:"
echo "   https://cloudconvert.com/svg-to-png"
echo "   上記のサイトでicon.svgをアップロードし、256x256のPNGとしてダウンロード"
