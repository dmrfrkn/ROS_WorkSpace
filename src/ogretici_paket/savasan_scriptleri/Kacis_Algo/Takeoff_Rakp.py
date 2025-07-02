#!/usr/bin/env python3
# -- coding: utf-8 --

import time
import subprocess
from pymavlink import mavutil

# --- Gerekli Fonksiyonlar (Öncekiyle aynı, değişiklik yok) ---

def mod_degistir(connection, mode_name):
    if mode_name not in connection.mode_mapping():
        print(f"Bilinmeyen mod: {mode_name}")
        return
    mode_id = connection.mode_mapping()[mode_name]
    connection.mav.set_mode_send(
        connection.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)
    print(f"Mod '{mode_name}' olarak değiştirme komutu gönderildi...")
    while True:
        msg = connection.recv_match(type='HEARTBEAT', blocking=True)
        if msg.custom_mode == mode_id:
            print(f"Onaylandı: Mod şimdi {mode_name}")
            break
        time.sleep(0.1)

def arm_et(connection):
    print("Arm komutu gönderiliyor...")
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
    print("Arm onayı bekleniyor...")
    while True:
        msg = connection.recv_match(type='HEARTBEAT', blocking=True)
        if (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            print("Onaylandı: Uçak ARM edildi!")
            break
        time.sleep(0.1)

def rc_komutu_gonder(connection, throttle=1500, pitch=1500):
    connection.mav.rc_channels_override_send(
        connection.target_system, connection.target_component,
        1500, pitch, throttle, 1500, 0, 0, 0, 0)

def rc_kontrolu_birak(connection):
    connection.mav.rc_channels_override_send(
        connection.target_system, connection.target_component,
        0, 0, 0, 0, 0, 0, 0, 0)
    print("RC kontrolü bırakıldı.")


# --- ANA KOD (İRTİFA KONTROL MANTIĞI EKLENDİ) ---
if __name__ == "__main__":
    
    sitl_process = None
    connection = None

    # --- Ayarlanabilir Parametreler ---
    hedef_irtifa = 100.0          # Ulaşılmak istenen irtifa (metre)
    irtifa_toleransi = 2.0       # Hedefe ne kadar yaklaşınca görevin tamamlanacağı (metre)
    tirmanis_gazi = 2000         # Tırmanış için gaz seviyesi (1500-2000)
    tirmanis_acisi = 2000        # Tırmanış için pitch açısı (1500'den büyük)

    try:
        # Adım 1: SITL'i başlat
        print("SITL başlatılıyor...")
        sitl_command = [
            "sim_vehicle.py", "-v", "ArduPlane",
            "--add-param-file=ucak_parametre.txt",
            "--out=udp:127.0.0.1:14560", "--no-mavproxy"
        ]
        sitl_process = subprocess.Popen(sitl_command)
        time.sleep(10)

        # Adım 2: SITL'e Bağlan
        connection_string = 'udp:127.0.0.1:14560'
        print(f"{connection_string} adresine bağlanılıyor...")
        connection = mavutil.mavlink_connection(connection_string)
        connection.wait_heartbeat()
        print("Otopilota başarıyla bağlandı!")

        # Adım 3: Modu FBWA yap
        mod_degistir(connection, "FBWA")

        # Adım 4: Uçağı Arm et
        arm_et(connection)
        
        # Adım 5: HEDEF İRTİFAYA ULAŞANA KADAR TIRMAN
        print(f"RC kontrolü ile {hedef_irtifa} metreye tırmanış başlıyor...")
        while True:
            # Anlık irtifa bilgisini al
            msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
            anlik_irtifa = msg.relative_alt / 1000.0 # Milimetreden metreye çevir

            print(f"Anlık İrtifa: {anlik_irtifa:.2f} m / Hedef: {hedef_irtifa} m", end="\r")

            # Hedefe ulaşıldı mı diye kontrol et
            if anlik_irtifa >= hedef_irtifa - irtifa_toleransi:
                print(f"\nHedef irtifaya ulaşıldı! ({anlik_irtifa:.2f}m)")
                break # Tırmanış döngüsünden çık
            
            # Hedefe ulaşılmadıysa tırmanış komutunu gönder
            rc_komutu_gonder(connection, throttle=tirmanis_gazi, pitch=tirmanis_acisi)
            time.sleep(0.1) # Döngü frekansını ayarla

        # Adım 6: GÖREV SONU PROSEDÜRÜ
        print("Tırmanış tamamlandı. Kontrol otopilota devrediliyor.")
        
        # Uçağı stabil hale getir (gazı ve pitch'i nötrle)
        print("Uçak stabil hale getiriliyor...")
        rc_komutu_gonder(connection, throttle=1500, pitch=1500)
        time.sleep(1) # 1 saniye stabil uçsun

        # RC kontrolünü tamamen bırak
        rc_kontrolu_birak(connection)
        time.sleep(1)

        # Otonom görevler için GUIDED moda geç
        print("Otonom görevler için GUIDED moda geçiliyor...")
        mod_degistir(connection, "GUIDED")
        
        print("Prosedür başarıyla tamamlandı.")

    except Exception as e:
        print(f"\nBir hata oluştu: {e}")

    finally:
        # Adım 7: Her şeyi güvenle kapat
        print("Temizlik yapılıyor...")
        if connection:
            rc_kontrolu_birak(connection)
        if sitl_process:
            print("SITL süreci sonlandırılıyor.")
            sitl_process.terminate()
        print("Program bitti.")