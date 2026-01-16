import shutil
import hashlib
import datetime
import subprocess
from pathlib import Path
from win11toast import toast
from random import choice
import sys
import winsound
import threading
from plyer import notification as plyer_notify

APP_NAME = "KeпоЧкА от _BaDRiVeR_"
SCRIPT_DIR = Path(__file__).parent
STEAM_DIR_FILE = SCRIPT_DIR / "steam_dir.txt"
OI_SOUND = SCRIPT_DIR / "Cache/Sounds/oi.wav"
OK_SOUND = SCRIPT_DIR / "Cache/Sounds/ok.wav"
LOG_FILE = SCRIPT_DIR / f"Logs/log-{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.txt"

# Картинки
ERROR_IMAGE = {'src': str(SCRIPT_DIR / "Cache/Images/error.png")}
SUCCESS_IMAGE = {'src': str(SCRIPT_DIR / "Cache/Images/success.png")}

ALLOWED_EXT = {".exe", ".dll", ".json", ".cfg"}
IGNORED_FILES = {
    "UserData/MelonPreferences.cfg",
    "MelonLoader/Latest.log"
}


def log(msg, is_error=False):
    prefix = "[ОШИБКА]" if is_error else "[INFO]"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {prefix} {msg}\n")
        print(f"{timestamp} {prefix} {msg}")

def play_sound(path):
    try:
        # Без SND_ASYNC — играем синхронно, чтобы звук не обрывался
        winsound.PlaySound(str(path), winsound.SND_FILENAME)
    except Exception as e:
        log(f"[notify] Ошибка при воспроизведении звука: {e}", True)

def notify(title, message, isValid=False):
    icon = SUCCESS_IMAGE if isValid else ERROR_IMAGE
    sound_path = OK_SOUND if isValid else OI_SOUND

    try:
        log(f"[notify] Использую win11toast: {title} — {message}")
        thread = threading.Thread(target=play_sound, args=(sound_path,))
        thread.start()
        toast(title, message, icon=icon)
        # Если хочешь, чтобы звук гарантированно доиграл, подожди немного
        # thread.join(timeout=5)
    except Exception as e:
        log(f"[notify] Ошибка win11toast: {e}", True)
        try:
            thread = threading.Thread(target=play_sound, args=(sound_path,))
            thread.start()

            plyer_notify.notify(
                title=title,
                message=message,
                app_name="Updater",
                app_icon=icon['src'] if Path(icon['src']).exists() else None,
                timeout=5
            )
            # thread.join(timeout=5)
            log(f"[notify] Уведомление через plyer отправлено.")
        except Exception as inner_e:
            log(f"[notify] Ошибка plyer: {inner_e}", True)


def get_file_metadata_map(base_dir):
    result = {}
    base_len = len(str(base_dir)) + 1
    for file_path in base_dir.rglob("*"):
        if file_path.is_file():
            rel = str(file_path)[base_len:].replace("\\", "/")
            ext = file_path.suffix.lower()
            if ext in ALLOWED_EXT and rel not in IGNORED_FILES:
                result[rel] = {
                    "size": file_path.stat().st_size,
                    "mtime": file_path.stat().st_mtime,
                    "path": file_path
                }
    log(f"Файлов в {base_dir}: {len(result)}")
    return result

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def is_different(backup_map, current_map):
    if len(backup_map) != len(current_map):
        log(f"Разное количество файлов: {len(backup_map)} vs {len(current_map)}")
        return True
    for rel, b_meta in backup_map.items():
        c_meta = current_map.get(rel)
        if not c_meta:
            log(f"Отсутствует в steam: {rel}")
            return True
        if b_meta["size"] != c_meta["size"] or b_meta["mtime"] != c_meta["mtime"]:
            try:
                if file_hash(b_meta["path"]) != file_hash(c_meta["path"]):
                    log(f"Несовпадение хэша: {rel}")
                    return True
            except Exception as e:
                log(f"Ошибка хэша {rel}: {e}", True)
                return True
    return False

# === START ===

if not STEAM_DIR_FILE.exists():
    notify(APP_NAME, "Файл steam_dir.txt не найден!", False)
    log("Файл steam_dir.txt не найден!", True)
    sys.exit()

steam_base = STEAM_DIR_FILE.read_text(encoding="utf-8").splitlines()[0].rstrip()
steamDM_folder = Path(STEAM_DIR_FILE.read_text(encoding="utf-8").splitlines()[1].rstrip()) / "steamapps/common/Desktop Mate"
backup_folder = SCRIPT_DIR / "Cache/Desktop Mate"

if not steamDM_folder.exists():
    notify("KeПоЧкА", "Папка Desktop Mate не найдена! Проверь steam_dir.txt!", False)
    log(f"Папка Desktop Mate не найдена: {steamDM_folder}", True)
    sys.exit()

log("Проверка дат и хэшей...")
hash_backup = get_file_metadata_map(backup_folder)
hash_steam = get_file_metadata_map(steamDM_folder)

updated = False
update_error = False

if is_different(hash_backup, hash_steam):
    try:
        log("Обнаружено обновление. Заменяю...")
        shutil.rmtree(steamDM_folder)
        shutil.copytree(backup_folder, steamDM_folder)
        log("Обновление выполнено")
        updated = True

        cfg_path = steamDM_folder / "UserData/MelonPreferences.cfg"
        model_path = steamDM_folder / "Models/kepochka.vrm"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        if cfg_path.exists():
            with cfg_path.open(encoding="utf-8") as f:
                lines = [line for line in f if not line.strip().startswith("vrmPath")]
        else:
            lines = [
                "[settings]",
                "disable_log_readonly = false"
            ]

        lines = [line.rstrip() for line in lines if line.strip()]
        lines.append(f'vrmPath = "{str(model_path).replace("\\", "\\\\")}"')

        with cfg_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        log(f"Путь к модели прописан: {model_path}")
        notify(APP_NAME, "НЕ-Е-Е-Е-Т! Злая Мита убила меня!!! Перезапуск версии...", False)
    except Exception as e:
        notify("KeпоЧкА", "Ошибка при обновлении!", False)
        log(f"Ошибка при обновлении: {e}", True)
        update_error = True

if not update_error:
    quotes = [
        "С возвращением, игрок! Ю-ху-у-у-у!!!",
        "Зададим им року в этой дыре!",
        "Привет! Я — Мита Кепочка (=UwU=)",
        "Сыграем в кнопку? Ой..."
    ]

    notify(APP_NAME, f"Я загрузилась! {choice(quotes)}", True)
    log("Запуск Desktop Mate...")
    steam_exe = Path(steam_base) / "steam.exe"

    subprocess.Popen([
        str(steam_exe),
        "-silent",
        "-applaunch", "3301060"
    ])

else:
    log("Запуск отменён из-за ошибки.", True)

# === END ===