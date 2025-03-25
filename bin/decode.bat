python "%~dp0Python\decode.py" --encryption none "%~dp0..\example-config-none-mysecretkey"
python "%~dp0Python\decode.py" --encryption xor --key mysecretkey "%~dp0..\example-config-xor-mysecretkey"
python "%~dp0Python\decode.py" --encryption aes256 --key mysecretkey "%~dp0..\example-config-aes256-mysecretkey"