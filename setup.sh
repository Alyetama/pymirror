#!/bin/sh

mkdir -p ~/.pymirror/.addons
cp -R pymirror/data ~/.pymirror
res=$(curl -s https://api.github.com/repos/gorhill/uBlock/releases/latest | grep "firefox.xpi")
URL=$(echo "{$(echo $res)}" | jq --raw-output '.browser_download_url')
curl -sL $URL -o ~/.pymirror/.addons/ublock_latest.xpi
