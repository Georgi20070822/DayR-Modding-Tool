# DayR Modding Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DayR Modding Tool** is a graphical program for modding the game **Day R Survival** (version 1.694 and below). It automates all the main stages of mod creation: unpacking the game archive `resource.car`, decompiling scripts, compiling modified files, assembling the modified archive, **code error checking** via Luacheck, working with bytecode (assembler/disassembler), decoding UTF-8, and also provides a profile system and a command console.

---

## 📥 Download the finished program

**The latest stable version can be downloaded in the [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases) section.**  
All previous versions are also available there.

---

## 🆕 What’s new in version 0.0.4

- ✅ **A full‑fledged profile system** – create, edit, select, and delete project profiles. Profiles are stored in `%USERPROFILE%\DayR_MB\profiles.json`.
- ✅ **Assembler and disassembler in Python** – working with Lua bytecode (disassembling `.lu` → `.asm` and reverse assembling `.asm` → `.lu`). No more external `.exe` files needed!
- ✅ **UTF-8 decoder** – automatic correction of script encoding (conversion of numeric escape sequences into readable text).
- ✅ **Command console** – control the program via text commands: `help`, `clear`, `lua`, and commands from plugins.
- ✅ **Selection dialog during re‑decompilation** – intelligent mode selection: replace everything, add missing, or try another tool.
- ✅ **Icons for top panel buttons** – Profiles, settings, and help are now available with icons and tooltips.
- ✅ **All settings in one place** – font, profiles, interface configuration are stored in `%USERPROFILE%\DayR_MB\`. The settings are saved even when moving the EXE file.
- ✅ **Updated documentation** – instructions and notes are provided for version 0.0.4.
- **A multitude of improvements and fixes** – stability, performance, localization.

### Previous versions

**Version 0.0.3:**
- Integration of Luacheck for static code analysis.
- Buttons “Check one .lua” and “Check all .lua”.
- “Check” button in the file manager.

**Version 0.0.2:**
- Project profile management (creation, selection, export/import).
- Built-in Lua editor with syntax highlighting.
- Lua console for executing code.
- “Hash” button in the file manager.
- Administrator rights check at startup.

**Version 0.0.1 (first release):**
- Basic functionality: unpacking/packing resource.car, decompiling/compiling, file manager, font settings.
- Support for Russian and English languages.

For a complete list of changes, see the [Changelog section](#-changelog).

---

## ⚙️ System requirements

- **OS**: Windows 7/8/10/11 (32 or 64 bit)
- **RAM**: 512 MB or more
- **Free space: ~100 MB for the program + ~2 GB for game files (when unpacking)
- **Write permissions** in the working folder
- **Java Runtime Environment (JRE)** – required only for the alternative decompiler `unluac.jar` (optional)

---

## 🚀 Quick start

1. Download `DayR_Modding_Tool.exe` from the [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases) section.
2. Run the program.
3. Select the project folder.
4. Specify the path to `resource.car` from the game.
5. Click “Unpack resource.car” → “Decompile all .lu → .lua”.
6. Edit the required `.lua` files in the `mod_scripts` folder..
7. **Check the code** using Luacheck (the “Check one .lua” or “Check all .lua” button)..
8. Compile the modified files using the file manager (the “Build” button)..
9. Click “Pack resource.car (mod)” and save the new archive..
10. Copy the resulting `resource.car` to the game folder.

**Additional:**  
- Use **profiles** to quickly switch between projects.  
- When re‑decompiling, select the required mode in the dialog.  
- Use the **disassembler/assembler** (row 5) to work with bytecode.  
- Fix the script encoding using the **UTF‑8 decoder** (row 5).  
- Control the program via the **command console** (row 4).

Detailed instructions can be found in the **"Help"** section inside the program (the "?" button).

---

## , Source code build

If you want to build the program yourself from the source code (for development or modification):

1. Make sure that you have installed **Python 3.10+** and **pip**.
2. Clone the repository:
   ```bash
   git clone https://github.com/Georgi20070822/DayR-Modding-Tool.git
   cd DayR-Modding-Tool

   # DayR Modding Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DayR Modding Tool** — графическая программа для моддинга игры **Day R Survival** (версия 1.694 и ниже). Она автоматизирует все основные этапы создания модов: распаковку игрового архива `resource.car`, декомпиляцию скриптов, компиляцию изменённых файлов, сборку модифицированного архива, **проверку кода на ошибки** через Luacheck, работу с байт-кодом (ассемблер/дизассемблер), декодирование UTF-8, а также предоставляет систему профилей и командную консоль.

---

## 📥 Скачать готовую программу

**Последнюю стабильную версию можно скачать в разделе [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases).**  
Там же доступны все предыдущие версии.

---

## 🆕 Что нового в версии 0.0.4

- ✅ **Полноценная система профилей** – создавайте, редактируйте, выбирайте и удаляйте профили проектов. Профили хранятся в `%USERPROFILE%\DayR_MB\profiles.json`.
- ✅ **Ассемблер и дизассемблер на Python** – работа с байт-кодом Lua (дизассемблирование `.lu` → `.asm` и обратное ассемблирование `.asm` → `.lu`). Больше не нужны внешние `.exe` файлы!
- ✅ **UTF-8 декодер** – автоматическое исправление кодировки скриптов (преобразование числовых escape-последовательностей в читаемый текст).
- ✅ **Командная консоль** – управляйте программой через текстовые команды: `help`, `clear`, `lua` и команды от плагинов.
- ✅ **Диалог выбора при повторной декомпиляции** – интеллектуальный выбор режима: заменить все, добавить недостающие или попробовать другой инструмент.
- ✅ **Иконки для кнопок верхней панели** – профили, настройки и помощь теперь с иконками и всплывающими подсказками.
- ✅ **Все настройки в одном месте** – шрифт, профили, конфигурация интерфейса хранятся в `%USERPROFILE%\DayR_MB\`. Настройки сохраняются даже при перемещении EXE-файла.
- ✅ **Обновлена документация** – инструкция и памятки приведены к версии 0.0.4.
- ✅ **Множество улучшений и исправлений** – стабильность, производительность, локализация.

### Предыдущие версии

**Версия 0.0.3:**
- Интеграция Luacheck для статического анализа кода.
- Кнопки «Проверить один .lua» и «Проверить все .lua».
- Кнопка «Проверить» в менеджере файлов.

**Версия 0.0.2:**
- Управление профилями проектов (создание, выбор, экспорт/импорт).
- Встроенный редактор Lua с подсветкой синтаксиса.
- Lua-консоль для выполнения кода.
- Кнопка «Хеш» в менеджере файлов.
- Проверка прав администратора при запуске.

**Версия 0.0.1 (первый релиз):**
- Базовая функциональность: распаковка/упаковка resource.car, декомпиляция/компиляция, менеджер файлов, настройки шрифтов.
- Поддержка русского и английского языков.

Полный список изменений см. в разделе [История изменений](#-история-изменений-changelog).

---

## ⚙️ Системные требования

- **ОС**: Windows 7/8/10/11 (32 или 64 бит)
- **ОЗУ**: от 512 МБ
- **Свободное место**: ~100 МБ для программы + ~2 ГБ для файлов игры (при распаковке)
- **Права на запись** в рабочей папке
- **Java Runtime Environment (JRE)** – требуется только для альтернативного декомпилятора `unluac.jar` (опционально)

---

## 🚀 Быстрый старт

1. Скачайте `DayR_Modding_Tool.exe` из раздела [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases).
2. Запустите программу.
3. Выберите папку проекта.
4. Укажите путь к `resource.car` из игры.
5. Нажмите «Распаковать resource.car» → «Декомпилировать все .lu → .lua».
6. Отредактируйте нужные `.lua` файлы в папке `mod_scripts`.
7. **Проверьте код** через Luacheck (кнопка «Проверить один .lua» или «Проверить все .lua»).
8. Скомпилируйте изменённые файлы через менеджер файлов (кнопка «Собрать»).
9. Нажмите «Упаковать resource.car (мод)» и сохраните новый архив.
10. Скопируйте полученный `resource.car` в папку с игрой.

**Дополнительно:**  
- Используйте **профили**, чтобы быстро переключаться между проектами.  
- При повторной декомпиляции выбирайте нужный режим в диалоге.  
- Для работы с байт-кодом используйте **дизассемблер/ассемблер** (ряд 5).  
- Исправляйте кодировку скриптов через **UTF-8 декодер** (ряд 5).  
- Управляйте программой через **командную консоль** (ряд 4).

Подробная инструкция — в разделе **«Помощь»** внутри программы (кнопка «?»).

---

## 🛠️ Сборка из исходников

Если вы хотите собрать программу самостоятельно из исходного кода (для разработки или внесения изменений):

1. Убедитесь, что у вас установлен **Python 3.10+** и **pip**.
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Georgi20070822/DayR-Modding-Tool.git
   cd DayR-Modding-Tool
