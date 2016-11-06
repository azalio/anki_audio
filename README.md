# anki_mp3

anki_mp3 позволяет к экпортируемому с сайта wordsfromtext.com
списку слов для изучения добавить озвучку.

Чтобы запустить программу необходимо:
* Склонировать себе репозиторий:
```bash
git clone git@github.com:azalio/anki_mp3.git
```
* Перейти в папку репозитория
```
cd anki_mp3
```
и установить необходимые модули:
```
pip install -r requirements.txt
```
* Получить ключ [microsoft cognitive services (5000 озвучиваний
в месяц бесплатно)](
https://www.microsoft.com/cognitive-services/en-US/sign-up?ReturnUrl=/cognitive-services/en-us/subscriptions)
Поставить галочку напротив: **Bing Speech - Preview**
* Переместить файл config.json.example в config.json
и отредактировать его:
```
mv config.json.example config.json

vim config.json
```
В нем надо указать оба ключа, которые вы получили шагом ранее.
Так же необходимо указать путь к директории, где Anki [хранит
медиа контент](http://ankisrs.net/docs/manual.html#file-locations).
У меня он, например, находится по пути:
```
/Users/azalio/Documents/Anki/1-й пользователь/
```
* Скачать с сайта [wordsfromtext.com](http://wordsfromtext.com) файл со словами
для изучения (anki с 1 предложением)
* Запустить программу:
```
./anki_mp3 filename
```
где filename файл, который вы скачали на предыдущем шаге.
* Программа будет пытаться скачать озвучку с сайта google и ms.
* Если по каким-то причинам работа программы будет прервана,
просто запустите ее заново.
* В итоге получится файл с названием [название вашего файла].new
Его и надо импортировать в anki


