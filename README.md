# Wexium Installer

## Описание

Этот установщик позволяет выбрать и установить одну из следующих графических сред для Arch Linux:
- KDE Plasma
- BSPWM
- Hyprland

Конфигурационные файлы для выбранной среды будут скопированы из `/etc/wexium/`.

## Установка

1. Убедитесь, что у вас установлен Python и необходимые библиотеки:

```sh
sudo pacman -S python python-pip
pip install PyQt6