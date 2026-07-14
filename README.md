# RDP Pilot Plugin

## Overview
РDP Pilot — это плагин для SSH Pilot, который добавляет поддержку протокола Remote Desktop Protocol (RDP) с использованием библиотеки FreeRDP.

## Особенности
- Подключение к удаленным RD-серверам через FreeRDP
- Интеграция с SSH Pilot в виде отдельного протокола
- Безопасное хранение паролей через системную связку ключей
- Автоматический выбор клиента FreeRDP (wlfreerdp для Wayland, xfreerdp для X11)
- Поддержка Flatpak-окружения
- Полноэкранный режим и пользовательское разрешение экрана

## Требования
- FreeRDP установлен на системе (доступны команды `wlfreerdp` или `xfreerdp`)
- Связка ключей (libsecret или эквивалент) для безопасного хранения паролей

## Установка
1. Скопируйте плагин RDP Pilot в каталог плагинов пользователя:
   - Для Flatpak: `~/.var/app/io.github.mfat.sshpilot/data/sshpilot/plugins/rdp/`
   - Для операционной системы: `~/.local/share/sshpilot/plugins/rdp/`

2. Запустите SSH Pilot и откройте **Настройки > Плагины**

3. Включите плагин RDP и перезапустите SSH Pilot

## Использование
После включения плагина RDP в выпадающем списке выбора протоколов (вместе с SSH) появится новая опция:

- **Название протокола:** RDP (FreeRDP)

При создании нового подключения появятся специальные поля:
- IP / HOSTNAME - Адрес RDP-сервера
- USERNAME - Имя пользователя для аутентификации
- PORT (Default 3389) - Порт RDP (по умолчанию 3389)
- RESOLUTION - Разрешение экрана (формат: 1920x1080 или 'f' для полноэкранного режима)

Пароли будут автоматически сохраняться в связке ключей по уникальному ключу, основанному на нике подключения для безопасности.

## Технические детали
### Архитектура интеграции (ProtocolBackend)
Плагин использует механизм расширения протоколов SDK (ProtocolBackend) из SSH Pilot для регистрации нового протокола RDP:
- **Поля подключения**: Определяет параметры конфигурации RDP (хост, порт, имя пользователя, разрешение, дополнительные ключи FreeRDP)
- **Безопасное хранение паролей (ctx.secrets)**: Пароли и конфиденциальные данные не хранятся в открытом виде в конфигурационных файлах. Плагин сохраняет и извлекает их через системную связку ключей (keyring) с помощью ctx.secrets.get()
- **Запуск процесса (build_spawn)**: Метод возвращает SpawnSpec с массивом аргументов запуска бинарного файла FreeRDP (например, wlfreerdp или xfreerdp)

### Отображение и интерактивность во вкладке (Ограничения GTK4)
Существуют важные технические нюансы, связанные с отображением графического интерфейса RDP внутри вкладки приложения:
- **Терминальный контекст вкладок**: Стандартные вкладки подключений в SSH Pilot ориентированы на текстовые терминалы (используют виджет эмулятора терминала Vte.Terminal). Графический вывод FreeRDP (X11/Wayland-клиент) по умолчанию не может транслироваться внутрь стандартного текстового терминала.
- **Ограничения GTK4 и Wayland (Embedding)**: SSH Pilot построен на базе GTK4. В GTK4 виджеты Gtk.Socket и Gtk.Plug были полностью удалены, так как современный дисплейный сервер Wayland из соображений безопасности не поддерживает прямое встраивание графических контекстов сторонних процессов (XEMBED).
- **Реальное поведение и управление жизненным циклом**: При запуске RDP через ProtocolBackend SSH Pilot запустит нативный процесс wlfreerdp / xfreerdp. Сессия откроется в отдельном нативном графическом окне:
  - Обеспечивает максимальную производительность (прямое аппаратное ускорение графики, минимальный инпут-лаг)
  - FreeRDP сможет корректно захватывать клавиатурный фокус и системные сочетания клавиш (например, Alt+Tab, Win), что часто ломается при глубоком встраивании окон
  - Связь с интерфейсом сохраняется: SSH Pilot полностью контролирует процесс. Двойной клик на подключении в боковой панели запускает сессию, а закрытие графического окна FreeRDP корректно завершает сессию и очищает состояние внутри вкладки SSH Pilot

## Пример плагина
```python
class FreeRdpBackend(ProtocolBackend):
    protocol_id = "rdp"
    display_name = "RDP (FreeRDP)"
    
    def connection_fields(self):
        return [
            FieldSpec(key="host", label="IP / HOSTNAME", required=True),
            FieldSpec(key="username", label="USERNAME", required=True),
            FieldSpec(key="port", label="PORT (Default 3389)", required=False),
            FieldSpec(key="resolution", label="RESOLUTION (e.g. 1920x1080 or f for fullscreen)", required=False)
        ]
        
    def build_spawn(self, connection, ctx):
        data = connection.data or {}
        host = data.get("host")
        username = data.get("username")
        port = data.get("port") or "3389"
        resolution = data.get("resolution") or "1280x720"
        
        secret_key = f"rdp_password_{connection.nickname}"
        password = ctx.secrets.get(secret_key)
        
        rdp_bin = "wlfreerdp" if os.environ.get("WAYLAND_DISPLAY") else "xfreerdp"
        
        argv = [
            rdp_bin,
            f"/v:{host}:{port}",
            f"/u:{username}",
            "/dynamic-resolution",
            "/cert:tofu"
        ]
        
        if password:
            argv.append(f"/p:{password}")
        
        if resolution.lower() == "f":
            argv.append("/f")
        else:
            argv.append(f"/size:{resolution}")
            
        if os.path.exists("/.flatpak-info"):
            argv = ["flatpak-spawn", "--host"] + argv
            
        return SpawnSpec(argv=argv, env=dict(os.environ))
```

## Литература
1. [sshPilot Plugin SDK](https://github.com/mfat/sshpilot/blob/main/PLUGIN_SDK.md)
2. [Протокол FreeRDP](https://github.com/FreeRDP/FreeRDP)
3. [Спецификация встраивания протоколов SSH Pilot](https://github.com/mfat/sshpilot/blob/main/PLUGIN_SDK.md#protocolbackends)

## Лицензия
Этот плагин распространяется по лицензии MIT.

