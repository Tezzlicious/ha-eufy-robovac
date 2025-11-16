#!/bin/bash

echo "=== Eufy RoboVac S1 Pro - GitHubリポジトリ登録手順 ==="
echo ""
echo "1. まず、アイコンPNGファイルを生成します（オプション）："
echo "   rsvg-convert -w 256 -h 256 custom_components/eufy_robovac/icon.svg > custom_components/eufy_robovac/icon.png"
echo ""
echo "2. Gitリポジトリの初期化と設定："
echo ""
cd /Users/Takao/Documents/Personal-Project/ha-eufy-robovac-s1-pro

# Gitリポジトリの初期化
git init

# リモートリポジトリの追加
git remote add origin https://github.com/tkoba1974/ha-eufy-robovac-s1-pro.git

# ブランチ名をmainに設定
git branch -M main

# すべてのファイルをステージング
git add .

# 初回コミット
git commit -m "Initial commit: Eufy RoboVac S1 Pro Home Assistant Integration"

# GitHubへプッシュ
git push -u origin main

echo ""
echo "=== 完了 ==="
echo ""
echo "次のステップ："
echo "1. GitHubで https://github.com/tkoba1974/ha-eufy-robovac-s1-pro にアクセス"
echo "2. リポジトリが正しくアップロードされたことを確認"
echo "3. Settings → Aboutでトピックに 'hacs', 'home-assistant', 'eufy' を追加"
echo "4. HACSでカスタムリポジトリとして追加可能になります"
