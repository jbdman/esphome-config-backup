#!/bin/bash
temppath=$(dirname "$0")
python $temppath/Python/decode.py --encryption xor --key mysecretkey $temppath/../example-config-xor-mysecretkey 
python $temppath/Python/decode.py --encryption aes256 --key mysecretkey $temppath/../example-config-aes256-mysecretkey