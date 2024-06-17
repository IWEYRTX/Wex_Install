import os
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QComboBox, QPushButton, QLineEdit, QMessageBox

class Installer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Wexium Installer")
        self.setGeometry(100, 100, 400, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.disk_label = QLabel("Выберите диск для установки:")
        self.layout.addWidget(self.disk_label)

        self.disk_combo = QComboBox()
        self.disk_combo.addItems(self.get_disks())
        self.layout.addWidget(self.disk_combo)

        self.partition_label = QLabel("Выберите схему разметки диска:")
        self.layout.addWidget(self.partition_label)

        self.partition_combo = QComboBox()
        self.partition_combo.addItems(["Автоматическая разметка (весь диск)", "Ручная разметка", "Установить рядом с Windows"])
        self.layout.addWidget(self.partition_combo)

        self.wm_label = QLabel("Выберите графическую среду:")
        self.layout.addWidget(self.wm_label)

        self.wm_combo = QComboBox()
        self.wm_combo.addItems(["KDE Plasma", "BSPWM", "Hyprland"])
        self.layout.addWidget(self.wm_combo)

        self.user_label = QLabel("Введите имя пользователя:")
        self.layout.addWidget(self.user_label)

        self.user_input = QLineEdit()
        self.layout.addWidget(self.user_input)

        self.password_label = QLabel("Введите пароль:")
        self.layout.addWidget(self.password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_input)

        self.install_button = QPushButton("Установить")
        self.install_button.clicked.connect(self.install)
        self.layout.addWidget(self.install_button)

    def run_command(self, command):
        subprocess.run(command, shell=True, check=True)

    def get_disks(self):
        result = subprocess.run(['lsblk', '-d', '-n', '-o', 'NAME,SIZE'], stdout=subprocess.PIPE)
        disks = result.stdout.decode().splitlines()
        disk_info = []
        for disk in disks:
            name, size = disk.split()
            if 'G' in size:
                size_numeric = float(size.rstrip('G').replace(',', '.'))
                size_gb = size_numeric
                disk_info.append(f"{name} - {size_gb:.2f} ГБ")
            else:
                disk_info.append(f"{name} - {size} (Неизвестный формат)")
        return disk_info

    def partition_disk(self, disk, scheme):
        disk = disk.split()[0]
        if scheme == 'Автоматическая разметка (весь диск)':
            self.run_command(f"parted /dev/{disk} mklabel gpt")
            self.run_command(f"parted /dev/{disk} mkpart primary ext4 1MiB 100%")
            self.run_command(f"mkfs.ext4 /dev/{disk}1")
            self.run_command(f"mount /dev/{disk}1 /mnt")
        elif scheme == 'Ручная разметка':
            QMessageBox.information(self, "Информация", "Запустите утилиту для разметки диска (например, cfdisk или fdisk) и создайте разделы.")
            self.run_command(f"cfdisk /dev/{disk}")
            root_partition = input("Введите имя корневого раздела (например, /dev/sda1): ")
            self.run_command(f"mkfs.ext4 {root_partition}")
            self.run_command(f"mount {root_partition} /mnt")
            home_partition = input("Введите имя раздела /home (если есть, иначе оставьте пустым): ")
            if home_partition:
                self.run_command(f"mkfs.ext4 {home_partition}")
                self.run_command(f"mkdir -p /mnt/home")
                self.run_command(f"mount {home_partition} /mnt/home")
        elif scheme == 'Установить рядом с Windows':
            QMessageBox.information(self, "Информация", "Запустите утилиту для разметки диска (например, cfdisk или fdisk) и создайте разделы для Linux.")
            self.run_command(f"cfdisk /dev/{disk}")
            root_partition = input("Введите имя корневого раздела (например, /dev/sda1): ")
            self.run_command(f"mkfs.ext4 {root_partition}")
            self.run_command(f"mount {root_partition} /mnt")
            home_partition = input("Введите имя раздела /home (если есть, иначе оставьте пустым): ")
            if home_partition:
                self.run_command(f"mkfs.ext4 {home_partition}")
                self.run_command(f"mkdir -p /mnt/home")
                self.run_command(f"mount {home_partition} /mnt/home")

    def install_base_system(self):
        self.run_command("pacstrap /mnt base base-devel linux linux-firmware")
        self.run_command("genfstab -U /mnt >> /mnt/etc/fstab")
        self.run_command("arch-chroot /mnt ln -sf /usr/share/zoneinfo/Region/City /etc/localtime")
        self.run_command("arch-chroot /mnt hwclock --systohc")
        self.run_command("arch-chroot /mnt pacman -S nano vim sudo os-prober grub --noconfirm")
        self.run_command("arch-chroot /mnt grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB")
        self.run_command("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")

    def create_user(self, username, password):
        self.run_command(f"arch-chroot /mnt useradd -m -G wheel -s /bin/bash {username}")
        self.run_command(f"arch-chroot /mnt bash -c 'echo \"{username}:{password}\" | chpasswd'")
        self.run_command("arch-chroot /mnt sed -i 's/# %wheel ALL=(ALL) ALL/%wheel ALL=(ALL) ALL/' /etc/sudoers")

    def install_packages(self, packages):
        self.run_command(f"arch-chroot /mnt pacman -S {' '.join(packages)} --noconfirm")

    def copy_configs(self, wm, username):
        config_path = f"/etc/wexium/{wm}"
        home_config_path = f"/mnt/home/{username}/.config/{wm}"
        if not os.path.exists(home_config_path):
            os.makedirs(home_config_path)
        for file in os.listdir(config_path):
            full_file_path = os.path.join(config_path, file)
            if os.path.isfile(full_file_path):
                self.run_command(f"cp {full_file_path} {home_config_path}")

    def install(self):
        disk = self.disk_combo.currentText()
        partition_scheme = self.partition_combo.currentText()
        wm = self.wm_combo.currentText()
        username = self.user_input.text()
        password = self.password_input.text()

        if not username:
            QMessageBox.critical(self, "Ошибка", "Имя пользователя не может быть пустым!")
            return
        if not password:
            QMessageBox.critical(self, "Ошибка", "Пароль не может быть пустым!")
            return

        self.partition_disk(disk, partition_scheme)
        self.install_base_system()
        self.create_user(username, password)

        if wm == 'KDE Plasma':
            self.install_packages(['plasma', 'plasma-meta', 'sddm'])
            self.run_command("arch-chroot /mnt systemctl enable sddm")
            self.copy_configs('kde', username)
        elif wm == 'BSPWM':
            self.install_packages(['bspwm', 'sxhkd', 'lightdm', 'lightdm-gtk-greeter'])
            self.run_command("arch-chroot /mnt systemctl enable lightdm")
            self.copy_configs('bspwm', username)
        elif wm == 'Hyprland':
            self.install_packages(['hyprland', 'lightdm', 'lightdm-gtk-greeter'])
            self.run_command("arch-chroot /mnt systemctl enable lightdm")
            self.copy_configs('hyprland', username)

        QMessageBox.information(self, "Установка завершена", f"{wm} установлена и настроена!")

if __name__ == "__main__":
    app = QApplication([])
    window = Installer()
    window.show()
    app.exec()

