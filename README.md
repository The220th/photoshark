# photoshark

Помогает удалённо решить проблему на компьютере.

# Зависимости

``` bash
> pip3 install --upgrade pip

> pip3 install pyautogui Pillow hashlib # for photo and shark
> pip3 install pycrypto pycryptodome    # for photo and shark
```

Для `server` и `show` ничего не надо дополнительно устанавливать.

# Использование

Присутствуют 4 сущности:

- `server`: `server` будет связывать 3 сущности ниже.

- `shark`: `shark` будет получать скриншоты от `photo` и посылать сообщение `show`.

- `photo`: `photo` будет скриншотить экран и посылать скриншот `shark`.

- `show`: `show` будет показывать сообщения, полученные от `shark`.

Если `server`, `photo` или `show` упадёт, то произайдёт restart. Всё будет и дальше работать через несколько секунд.

Если `shark` упадёт, то просто произведите переподключение к серверу.

## server

Запуск:

``` bash
> python photoshark.py server {port}
# где {port} - порт, на котором будет работать сервер
```

## shark

Запуск:

``` bash
> python photoshark.py shark {ip} {port} [{cipher_key}]
# где {ip} и {port} - ip и порт сервера
# {cipher_key} - это опциональный аргумент. Если {cipher_key} существует, то скриншоты будут
#        шифроваться ключом {cipher_key}. У photo и shark должны быть одиннаковые {cipher_key}.
```

Использование:

После коннекта к серверу:

- Нажмите `Enter`, чтобы получить скриншот от `photo`.

- Или введите любое сообщение и нажмите `Enter`, чтобы отправить это сообщение `show`.

## photo

Запуск:

``` bash
> python photoshark.py photo {ip} {port} [{cipher_key}]
# где {ip} и {port} - ip и порт сервера
# {cipher_key} - это опциональный аргумент. Если {cipher_key} существует, то скриншоты будут
#        шифроваться ключом {cipher_key}. У photo и shark должны быть одиннаковые {cipher_key}.
```

## show

Запуск:

``` bash
> python photoshark.py show {ip} {port}
# где {ip} и {port} - ip и порт сервера
```











































